"""Connected journal/lifecycle and hosted admission tests, without credentials."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_integration_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_integration_package.canary_dns import ExpectedRecord, verify_public_dns
from canary_integration_package.canary_entrypoint import BUCKET, checked_report, config_for
from canary_integration_package.canary_lifecycle import CompletedFailure, run_canary
from canary_integration_package.canary_policy import require_trusted_context
from canary_integration_package.canary_runtime import RuntimeJournal
from canary_integration_package.canary_store import (
    CanaryStore,
    PreconditionFailed,
    Qualification,
    RunIdentity,
    StoreBinding,
    StoredArchive,
    StoredLedger,
)

SHA = "a" * 40
RUN = "gha-1794700000-123-1"


def arguments(**changes):
    return dict(
        bucket=BUCKET,
        revision=SHA,
        run_id="123",
        attempt="1",
        repository="SolomonHD/unifi-cloudflare-glue",
        ref="refs/heads/main",
        event_name="workflow_dispatch",
        acceptance_sha="",
        acceptance_branch="",
        policy_reviewed="true",
        **changes,
    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("bucket", "production"),
        ("policy_reviewed", "false"),
        ("revision", "main"),
        ("run_id", "1;evil"),
    ],
)
def test_runtime_config_rejects_before_dagger_secret_injection(key, value):
    args = arguments()
    args[key] = value
    with pytest.raises(ValueError):
        config_for(**args)


def test_feature_pilot_requires_exact_sha_branch_and_push():
    context = {
        "repository": "SolomonHD/unifi-cloudflare-glue",
        "ref_type": "branch",
        "ref": "refs/heads/change/add-cloudflare-live-ci-canary",
        "sha": SHA,
        "event_name": "push",
    }
    require_trusted_context(
        context, acceptance_sha=SHA, acceptance_branch="change/add-cloudflare-live-ci-canary"
    )
    for changes in (
        {"sha": "b" * 40},
        {"event_name": "pull_request_target"},
        {"event_name": "workflow_dispatch"},
        {"repository": "fork/repo"},
    ):
        with pytest.raises(ValueError):
            require_trusted_context(
                {**context, **changes},
                acceptance_sha=SHA,
                acceptance_branch="change/add-cloudflare-live-ci-canary",
            )


def test_local_backend_qualification_cannot_admit_dns_lifecycle():
    args = arguments()
    args.update(
        operation="qualify",
        event_name="local_qualification",
        ref="refs/heads/change/add-cloudflare-live-ci-canary",
        acceptance_sha=SHA,
        acceptance_branch="change/add-cloudflare-live-ci-canary",
    )
    assert config_for(**args)["operation"] == "qualify"
    args["operation"] = "normal"
    with pytest.raises(ValueError):
        config_for(**args)


def test_checked_report_fails_closed_and_does_not_echo_raw_output():
    config = {"run_prefix": RUN, "revision": SHA, "operation": "normal"}
    with pytest.raises(RuntimeError) as error:
        checked_report("synthetic-secret-runtime-output", config, 1)
    assert "synthetic-secret" not in str(error.value)
    report = {
        "run_prefix": RUN,
        "revision": SHA,
        "phase": "absence",
        "primary": "verified",
        "cleanup": "verified",
        "qualified": True,
        "operation": "normal",
    }
    assert json.loads(checked_report(json.dumps(report), config, 0)) == report
    with pytest.raises(RuntimeError):
        checked_report(json.dumps(report), config, 1)
    report["cleanup"] = "unknown"
    with pytest.raises(RuntimeError):
        checked_report(json.dumps(report), config, 0)


class Memory:
    def __init__(self):
        self.current = None
        self.archives = {}
        self.version = 0

    def stored(self, ledger):
        self.version += 1
        self.current = StoredLedger(ledger, str(self.version))
        return self.current

    def get(self, binding, key):
        return self.current

    def create_if_absent(self, binding, key, ledger):
        if self.current:
            raise PreconditionFailed()
        return self.stored(ledger)

    def update_if_version(self, binding, key, ledger, expected):
        if not self.current or self.current.version != expected:
            raise PreconditionFailed()
        return self.stored(ledger)

    def create_archive(self, binding, key, receipt):
        if key in self.archives:
            raise PreconditionFailed()
        self.version += 1
        self.archives[key] = StoredArchive(receipt, "archive-" + str(self.version))
        return self.archives[key]

    def get_archive(self, binding, key):
        return self.archives.get(key)


def test_connected_journal_completes_and_successor_can_run():
    memory = Memory()
    binding = StoreBinding(
        "https://s3.us-east-1.wasabisys.com",
        "us-east-1",
        BUCKET,
        "cloudflare-live-ci/v1/",
        "runtime-test",
    )
    qualification = Qualification(binding, *([True] * 9))
    for number in (123, 124):
        prefix = f"gha-1794700000-{number}-1"
        identity = RunIdentity(
            prefix,
            SHA,
            "a" * 32,
            "solomonhd.ai",
            (
                (f"{prefix}.txt.ci.solomonhd.ai", "TXT"),
                (f"{prefix}.cname.ci.solomonhd.ai", "CNAME"),
            ),
        )
        state = ["absent"]
        journal = RuntimeJournal(
            CanaryStore(memory, binding, qualification), identity, lambda: state[0]
        )

        class Driver:
            def initialize(self):
                pass

            def apply(self, revision):
                state[0] = revision

            def verify_api(self, revision):
                pass

            def verify_dns(self, revision):
                if number == 123:
                    raise CompletedFailure()

            def drift(self):
                return False

            def has_state(self):
                return state[0] != "absent"

            def destroy(self):
                state[0] = "empty"

            def verify_absence(self):
                assert state[0] == "empty"

        report = run_canary(prefix, journal, Driver())
        assert report.cleanup == "verified"
        assert report.primary == ("failed" if number == 123 else "verified")
        assert memory.current.ledger.completed is not None
    assert len(memory.archives) == 2


def test_workflow_is_thin_pinned_and_initially_gated():
    path = ROOT / ".github/workflows/cloudflare-live-ci.gha.yaml"
    workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    job = workflow["jobs"]["canary"]
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] == "false"
    assert job["environment"] == "cloudflare-live-ci"
    assert int(job["timeout-minutes"]) <= 30
    assert "github.sha == vars.CANARY_ACCEPTANCE_SHA" in job["if"]
    assert "CLOUDFLARE_CANARY_SCHEDULE_ENABLED == 'true'" in job["if"]
    assert set(workflow["on"]) == {"push", "workflow_dispatch", "schedule"}
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    assert commands.count("api call -m . test-cloudflare-dns-canary") == 1
    for forbidden in (
        "terraform ",
        "api.cloudflare.com",
        "if: always()",
        "DAGGER_CLOUD_TOKEN",
        "upload-artifact",
    ):
        assert forbidden not in path.read_text()
    assert "--cloudflare-api-token=env://CLOUDFLARE_API_TOKEN" in commands
    assert "persist-credentials" in job["steps"][0]["with"]


def test_update_dns_budget_outlasts_warmed_sixty_second_ttl():
    clock = [0.0]
    expected = ExpectedRecord("a" * 32, f"{RUN}.cname.ci.solomonhd.ai", "CNAME", "example.org")

    def resolver(name, kind, timeout):
        return ["example.com" if clock[0] < 60 else "example.org"]

    def sleep(seconds):
        clock[0] += seconds

    result = verify_public_dns(
        expected,
        run_prefix=RUN,
        resolver=resolver,
        max_attempts=37,
        deadline_seconds=180,
        interval_seconds=5,
        clock=lambda: clock[0],
        sleep=sleep,
    )
    assert clock[0] >= 60
    assert result.attempts == 13
