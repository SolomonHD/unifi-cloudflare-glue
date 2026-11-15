"""Native command contracts using private-file fake processes; no live calls."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from shutil import copytree
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_terraform_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_terraform_test_package import canary_terraform as tf
from canary_terraform_test_package.canary_identity import record_name
from canary_terraform_test_package.canary_lifecycle import CompletedFailure

PREFIX = "gha-1794700000-123456789-1"
ZONE = "a" * 32
FIXTURE = Path(__file__).resolve().parents[2] / "terraform/cloudflare-canary"


def attrs(label):
    return dict(
        id=("b" if label == "txt" else "c") * 32,
        name=record_name(PREFIX, label),
        type=label.upper(),
        zone_id=ZONE,
        proxied=False,
    )


def state(labels=("txt", "cname")):
    return {
        "version": 4,
        "serial": 3,
        "lineage": "owned",
        "resources": (
            [
                {
                    "mode": "managed",
                    "type": tf.RESOURCE_TYPE,
                    "name": "canary",
                    "provider": f'provider["{tf.PROVIDER}"]',
                    "instances": [
                        {"index_key": label, "attributes": attrs(label)} for label in labels
                    ],
                }
            ]
            if labels
            else []
        ),
    }


def plan(labels=("txt", "cname"), action="create"):
    def after(label):
        value = attrs(label)
        revision = "update" if action == "update" else "create"
        value.update(
            content=(
                f"canary_{revision}"
                if label == "txt"
                else ("example.org" if revision == "update" else "example.com")
            ),
            ttl=60,
            comment=PREFIX,
        )
        return value

    return {
        "configuration": {
            "provider_config": {"cloudflare": {"full_name": tf.PROVIDER}},
            "root_module": {
                "resources": [
                    {
                        "address": "cloudflare_dns_record.canary",
                        "provider_config_key": "cloudflare",
                    },
                    {"address": tf.DATA_ADDRESS, "provider_config_key": "cloudflare"},
                ]
            },
        },
        "resource_changes": [
            {
                "address": f'cloudflare_dns_record.canary["{label}"]',
                "mode": "managed",
                "type": tf.RESOURCE_TYPE,
                "name": "canary",
                "index": label,
                "provider_name": tf.PROVIDER,
                "change": {
                    "actions": [action],
                    "before": attrs(label) if action == "delete" else None,
                    "after": None if action == "delete" else after(label),
                },
            }
            for label in labels
        ],
    }


class Processes:
    def __init__(self):
        self.calls = []
        self.queue = []

    def add(self, command, payload=b"", code=0):
        self.queue.append((command, payload, code))

    def __call__(self, args, **kwargs):
        self.calls.append((args, kwargs))
        command, payload, code = self.queue.pop(0)
        assert args[1] == command
        assert kwargs["start_new_session"] is True
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert kwargs["stdout"].fileno() != kwargs["stderr"].fileno()
        kwargs["stdout"].write(
            json.dumps(payload).encode() if isinstance(payload, dict) else payload
        )
        kwargs["stderr"].write(b"synthetic-secret-never-render")
        process = Mock(pid=12345)
        if code == "timeout":
            process.wait.side_effect = [subprocess.TimeoutExpired(args, 1), 0]
        else:
            process.wait.return_value = code
        return process


@pytest.fixture
def setup(tmp_path):
    root = copytree(FIXTURE, tmp_path / "fixture")
    processes = Processes()
    dns = Mock()
    checkpoints = []
    driver = tf.TerraformDriver(
        root,
        run_prefix=PREFIX,
        zone_id=ZONE,
        backend=tf.BackendConfig(
            "https://s3.wasabisys.com",
            "us-east-1",
            "test-state",
            f"canary/runs/{PREFIX}/terraform.tfstate",
        ),
        state_generation=lambda: "generation-3",
        checkpoint=lambda raw, gen: checkpoints.append((raw, gen)),
        runtime=True,
        runtime_check=lambda: True,
        process_factory=processes,
        dns_client=dns,
        resolver=lambda name, kind, timeout: ["canary_create" if kind == "TXT" else "example.com."],
    )
    return driver, processes, dns, checkpoints


def initialize(driver, processes):
    processes.add("init")
    driver.initialize()


def queue_apply(processes, *, code=0, labels=("txt", "cname"), revision="create"):
    processes.add("plan", code=2)
    processes.add("show", plan(action="update" if revision == "update" else "create"))
    processes.add("apply", code=code)
    processes.add("state", state(labels))
    if code == 0:
        processes.add("output", {label: attrs(label) for label in labels})


def test_runtime_requires_explicit_gate(setup):
    driver, _, _, _ = setup
    with pytest.raises(tf.TerraformUnknown, match="dagger_runtime_required"):
        tf.TerraformDriver(
            driver.root,
            run_prefix=PREFIX,
            zone_id=ZONE,
            backend=driver.backend,
            state_generation=lambda: "x",
            checkpoint=lambda *_: None,
        )


def test_initialize_validates_fixture_and_nonsecret_backend(setup, monkeypatch):
    driver, processes, dns, _ = setup
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "synthetic-secret")
    monkeypatch.setenv("TF_CLI_ARGS", "-bad-secret")
    monkeypatch.setenv("TF_LOG", "TRACE")
    initialize(driver, processes)
    dns.verify_zone.assert_called_once()
    args, kwargs = processes.calls[0]
    assert args[1] == "init" and "synthetic-secret" not in str(args)
    assert kwargs["env"]["AWS_SECRET_ACCESS_KEY"] == "synthetic-secret"
    assert "TF_CLI_ARGS" not in kwargs["env"] and "TF_LOG" not in kwargs["env"]
    assert "synthetic-secret" not in driver._backend_hcl
    assert "use_lockfile = true" in driver._backend_hcl


def test_full_create_update_drift_destroy(setup):
    driver, processes, dns, checkpoints = setup
    initialize(driver, processes)
    for revision in ("create", "update"):
        queue_apply(processes, revision=revision)
        driver.apply(revision)
        driver.verify_api(revision)
    assert len(checkpoints) == 2 and all(gen == "generation-3" for _, gen in checkpoints)
    assert {record.content for record in driver._records.values()} == {
        "canary_update",
        "example.org",
    }
    processes.add("plan")
    processes.add("show", plan(action="no-op"))
    assert driver.drift() is False
    processes.add("state", state())
    assert driver.has_state() is True
    processes.add("state", state())
    processes.add("plan", code=2)
    processes.add("show", plan(action="delete"))
    processes.add("apply")
    processes.add("state", state(()))
    driver.destroy()
    processes.add("state", state(()))
    driver.verify_absence()
    assert len(checkpoints) == 3
    assert dns.verify_absent.call_count == 2
    assert not processes.queue


def test_public_dns_uses_exact_created_expectations(setup):
    driver, processes, _, _ = setup
    initialize(driver, processes)
    queue_apply(processes)
    driver.apply("create")
    driver.verify_dns("create")


def test_completed_partial_failure_checkpoint_before_exception(setup):
    driver, processes, _, checkpoints = setup
    initialize(driver, processes)
    queue_apply(processes, code=1, labels=("txt",))
    with pytest.raises(tf.TerraformUnknown, match="terraform_effect_outcome_unconfirmed") as error:
        driver.apply("create")
    assert len(checkpoints) == 1
    assert "synthetic-secret" not in str(error.value)
    assert _labels(checkpoints[0][0]) == ["txt"]


def _labels(raw):
    return [i["index_key"] for r in json.loads(raw)["resources"] for i in r["instances"]]


def test_timeout_kills_waits_and_never_checkpoints(setup, monkeypatch):
    driver, processes, _, checkpoints = setup
    initialize(driver, processes)
    queue_apply(processes, code="timeout")
    kill = Mock()
    monkeypatch.setattr(tf.os, "killpg", kill)
    with pytest.raises(tf.TerraformUnknown, match="terraform_effect_unknown"):
        driver.apply("create")
    kill.assert_called_once_with(12345, tf.signal.SIGKILL)
    assert not checkpoints
    assert processes.queue[0][0] == "state"


def test_checkpoint_failure_is_unknown_not_completed_failure(setup):
    driver, processes, _, _ = setup
    initialize(driver, processes)
    queue_apply(processes, code=1)
    driver._checkpoint = Mock(side_effect=RuntimeError("synthetic-secret"))
    with pytest.raises(tf.TerraformUnknown, match="effect_checkpoint_unconfirmed"):
        driver.apply("create")


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p["resource_changes"][0].update(address="cloudflare_zone.accidental"),
        lambda p: p["resource_changes"][0].update(type="cloudflare_zone"),
        lambda p: p["resource_changes"][0].update(name="unrelated"),
        lambda p: p["resource_changes"][0].update(provider_name="registry.terraform.io/evil/evil"),
        lambda p: p["resource_changes"][0]["change"]["after"].update(zone_id="f" * 32),
        lambda p: p["resource_changes"][0]["change"]["after"].update(name="elsewhere.solomonhd.ai"),
        lambda p: p["configuration"]["root_module"].update(module_calls={"evil": {}}),
        lambda p: p["configuration"]["provider_config"].update(aws={"full_name": "aws"}),
        lambda p: p["resource_changes"][0]["change"].update(actions=["delete", "create"]),
    ],
)
def test_unexpected_plan_never_applies(setup, mutation):
    driver, processes, _, checkpoints = setup
    initialize(driver, processes)
    candidate = plan()
    mutation(candidate)
    processes.add("plan", code=2)
    processes.add("show", candidate)
    with pytest.raises(tf.TerraformUnknown):
        driver.apply("create")
    assert not checkpoints
    assert [args[1] for args, _ in processes.calls] == ["init", "plan", "show"]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s["resources"][0].update(type="cloudflare_zone"),
        lambda s: s["resources"][0].update(name="unrelated"),
        lambda s: s["resources"][0].update(provider="evil"),
        lambda s: s["resources"][0].update(module="module.evil"),
        lambda s: s["resources"][0]["instances"][0].update(index_key="other"),
        lambda s: s["resources"][0]["instances"][0]["attributes"].update(zone_id="f" * 32),
        lambda s: s["resources"].append(copy.deepcopy(s["resources"][0])),
    ],
)
def test_unexpected_state_blocks_cleanup(setup, mutation):
    driver, processes, _, _ = setup
    initialize(driver, processes)
    candidate = state()
    mutation(candidate)
    processes.add("state", candidate)
    with pytest.raises(tf.TerraformUnknown):
        driver.destroy()
    assert processes.calls[-1][0][1] == "state"


def test_nonempty_remote_state_blocks_absence(setup):
    driver, processes, dns, _ = setup
    initialize(driver, processes)
    processes.add("state", state(("txt",)))
    with pytest.raises(CompletedFailure, match="remote_state_not_empty"):
        driver.verify_absence()
    dns.verify_absent.assert_not_called()


def test_unexpected_source_is_rejected_before_init(setup):
    driver, processes, _, _ = setup
    (driver.root / "unexpected.tf").write_text('provider "aws" {}')
    with pytest.raises(tf.TerraformUnknown, match="unexpected_fixture_file"):
        driver.initialize()
    assert not processes.calls


@pytest.mark.parametrize(
    "field,value",
    [
        ("endpoint", "http://s3.wasabisys.com"),
        ("endpoint", "https://user:secret@s3.wasabisys.com"),
        ("endpoint", "https://s3.wasabisys.com/?secret=x"),
        ("key", "../secret.tfstate"),
        ("bucket", "bad\nsecret"),
        ("region", "bad\nsecret"),
    ],
)
def test_backend_rejects_injection(field, value):
    values = dict(
        endpoint="https://s3.wasabisys.com",
        region="us-east-1",
        bucket="test-state",
        key="canary/state.tfstate",
    )
    values[field] = value
    with pytest.raises(ValueError, match="invalid_canary_backend"):
        tf.BackendConfig(**values).hcl()


class Holder:
    def __init__(self, *, boolean=False):
        self.evidence = None
        self.released = False
        self.boolean = boolean

    def create_lock(self, key, body):
        self.evidence = tf.LockEvidence(key, "owned-s3-version", body)
        return True if self.boolean else self.evidence

    def read_lock(self, key):
        return self.evidence

    def release_lock(self, key, version):
        assert self.evidence.key == key and self.evidence.version == version
        self.released = True
        self.evidence = None


def qualification_backend(driver):
    driver.backend = tf.BackendConfig(
        driver.backend.endpoint,
        driver.backend.region,
        driver.backend.bucket,
        "canary/qualification/12345678-1234-4123-8123-123456789abc/terraform.tfstate",
    )
    driver._backend_hcl = driver.backend.hcl()
    driver._qualification = True
    for name in ("main.tf", "variables.tf", "outputs.tf"):
        (driver.root / name).unlink()
    (driver.root / "versions.tf").write_text(
        'terraform {\n required_version = ">= 1.13.5, < 2.0.0"\n backend "s3" {}\n}\n'
    )


def test_native_lock_requires_observed_refusal_and_success_after_owned_release(setup, monkeypatch):
    driver, processes, _, _ = setup
    qualification_backend(driver)
    initialize(driver, processes)
    holder = Holder()
    monkeypatch.setattr(tf.uuid, "uuid4", lambda: "12345678-1234-4123-8123-123456789abc")
    processes.add(
        "plan",
        b"Error acquiring the state lock: PreconditionFailed 12345678-1234-4123-8123-123456789abc synthetic-private-details",
        1,
    )
    processes.add("plan")
    processes.add("show", {"configuration": {"root_module": {}}})
    key = tf.qualify_native_lock(driver, holder, qualification_prefix="canary/qualification/")
    assert holder.released and key == driver.backend.key + ".tflock"
    assert [args[1] for args, _ in processes.calls] == ["init", "plan", "plan", "show"]


@pytest.mark.parametrize(
    "code,payload", [(0, b""), (1, b"unrelated failure"), (2, b""), ("timeout", b"")]
)
def test_native_lock_unknown_or_wrong_failure_retains_owned_lock(setup, monkeypatch, code, payload):
    driver, processes, _, _ = setup
    qualification_backend(driver)
    initialize(driver, processes)
    holder = Holder()
    processes.add("plan", payload, code)
    monkeypatch.setattr(tf.os, "killpg", Mock())
    with pytest.raises(tf.TerraformUnknown, match="native_lock_qualification_unconfirmed"):
        tf.qualify_native_lock(driver, holder, qualification_prefix="canary/qualification/")
    assert holder.evidence is not None and not holder.released


def test_native_lock_boolean_is_not_evidence(setup):
    driver, processes, _, _ = setup
    qualification_backend(driver)
    initialize(driver, processes)
    with pytest.raises(tf.TerraformUnknown):
        tf.qualify_native_lock(
            driver, Holder(boolean=True), qualification_prefix="canary/qualification/"
        )
    assert len(processes.calls) == 1


def test_native_lock_rejects_run_backend_without_creating_lock(setup):
    driver, processes, _, _ = setup
    initialize(driver, processes)
    holder = Holder()
    with pytest.raises(tf.TerraformUnknown, match="disposable_lock_backend_required"):
        tf.qualify_native_lock(driver, holder, qualification_prefix="canary/qualification/")
    assert holder.evidence is None


def test_unexpected_partial_state_still_checkpointed_before_blocking(setup):
    driver, processes, _, checkpoints = setup
    initialize(driver, processes)
    processes.add("plan", code=2)
    processes.add("show", plan())
    processes.add("apply", code=1)
    invalid = state()
    invalid["resources"][0]["name"] = "unexpected"
    processes.add("state", invalid)
    with pytest.raises(tf.TerraformUnknown, match="effect_checkpoint_unconfirmed"):
        driver.apply("create")
    assert len(checkpoints) == 1 and json.loads(checkpoints[0][0]) == invalid


def test_state_pull_failure_after_completed_effect_is_unknown(setup):
    driver, processes, _, checkpoints = setup
    initialize(driver, processes)
    processes.add("plan", code=2)
    processes.add("show", plan())
    processes.add("apply", code=1)
    processes.add("state", code=1)
    with pytest.raises(tf.TerraformUnknown, match="effect_checkpoint_unconfirmed"):
        driver.apply("create")
    assert not checkpoints


def test_checkpoint_stdout_and_stderr_are_private(setup, capsys):
    import sys

    driver, processes, _, _ = setup
    initialize(driver, processes)
    queue_apply(processes)

    def checkpoint(raw, generation):
        print("synthetic-private-checkpoint")
        print("synthetic-private-checkpoint", file=sys.stderr)

    driver._checkpoint = checkpoint
    driver.apply("create")
    captured = capsys.readouterr()
    assert "synthetic-private" not in captured.out + captured.err


@pytest.mark.parametrize("kind", ["missing", "symlink", "unexpected-provider", "moving-version"])
def test_provider_lock_is_checked_before_native_init(setup, tmp_path, kind):
    driver, processes, _, _ = setup
    lock = driver.root / ".terraform.lock.hcl"
    if kind == "missing":
        lock.unlink()
    elif kind == "symlink":
        other = tmp_path / "lock"
        other.write_text(lock.read_text())
        lock.unlink()
        lock.symlink_to(other)
    elif kind == "unexpected-provider":
        lock.write_text(
            lock.read_text()
            + '\nprovider "registry.terraform.io/hashicorp/random" { version="1.0.0" }\n'
        )
    else:
        lock.write_text(lock.read_text().replace('"5.16.0"', '"5.17.0"'))
    with pytest.raises(tf.TerraformUnknown, match="invalid_provider_lock"):
        driver.initialize()
    assert not processes.calls


@pytest.mark.parametrize("kind", ["apply", "destroy"])
def test_qualification_root_cannot_apply_or_destroy(setup, kind):
    driver, processes, _, _ = setup
    qualification_backend(driver)
    initialize(driver, processes)
    with pytest.raises(tf.TerraformUnknown, match="qualification_is_plan_only"):
        driver.apply("create") if kind == "apply" else driver.destroy()
    assert len(processes.calls) == 1


@pytest.mark.parametrize("change", ["wrong-content", "wrong-ttl", "partial-plan", "no-op-update"])
def test_revision_plan_must_change_both_exact_values(setup, change):
    driver, processes, _, _ = setup
    initialize(driver, processes)
    candidate = plan(action="update")
    if change == "wrong-content":
        candidate["resource_changes"][0]["change"]["after"]["content"] = "incorrect"
    elif change == "wrong-ttl":
        candidate["resource_changes"][0]["change"]["after"]["ttl"] = 120
    elif change == "partial-plan":
        candidate["resource_changes"].pop()
    else:
        candidate["resource_changes"][0]["change"]["actions"] = ["no-op"]
    processes.add("plan", code=2)
    processes.add("show", candidate)
    with pytest.raises(tf.TerraformUnknown):
        driver.apply("update")
    assert processes.calls[-1][0][1] == "show"
