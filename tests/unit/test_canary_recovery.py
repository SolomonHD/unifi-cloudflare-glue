"""Explicit recovery admission and terminal-proof checks without live effects."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_recovery_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_recovery_test_package import canary_recovery as recovery
from canary_recovery_test_package import canary_store as storage
from canary_recovery_test_package.canary_s3 import StoredBlob
from canary_recovery_test_package.canary_store import StoreError

RUN = "gha-1794714939-43674454065-1"
SHA = "a" * 40


def terminal(**changes):
    return {
        "id": 43674454065,
        "run_attempt": 1,
        "status": "completed",
        "conclusion": "failure",
        "head_sha": SHA,
        "repository": {"full_name": recovery.REPOSITORY},
        "head_repository": {"full_name": recovery.REPOSITORY},
        "event": "push",
        "head_branch": "change/add-cloudflare-live-ci-canary",
        "path": ".github/workflows/cloudflare-live-ci.gha.yaml",
        **changes,
    }


def jobs(**changes):
    return {
        "total_count": 1,
        "jobs": [
            {
                "status": "completed",
                "completed_at": "2026-11-15T03:55:53Z",
                "conclusion": "failure",
                **changes,
            }
        ],
    }


def test_exact_terminal_attempt_is_read_from_fixed_public_repository(monkeypatch):
    reader = Mock(side_effect=[terminal(), jobs()])
    monkeypatch.setattr(recovery, "public_json", reader)
    assert recovery.terminal_evidence(RUN, SHA).endswith("/43674454065/attempts/1")
    assert (
        reader.call_args_list[0].args[0]
        == "repos/SolomonHD/unifi-cloudflare-glue/actions/runs/43674454065/attempts/1"
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"head_sha": "b" * 40},
        {"status": "in_progress"},
        {"conclusion": None},
        {"run_attempt": 2},
        {"id": 1},
        {"event": "pull_request_target"},
        {"head_repository": {"full_name": "fork/repo"}},
        {"path": ".github/workflows/other.yaml"},
        {"head_branch": "other"},
        {"repository": {"full_name": "other/repo"}},
    ],
)
def test_nonmatching_or_active_attempt_cannot_authorize_recovery(monkeypatch, changes):
    monkeypatch.setattr(recovery, "public_json", Mock(side_effect=[terminal(**changes), jobs()]))
    with pytest.raises(StoreError):
        recovery.terminal_evidence(RUN, SHA)


@pytest.mark.parametrize(
    "changes", [{"status": "in_progress"}, {"completed_at": None}, {"conclusion": None}]
)
def test_all_jobs_must_be_terminal(monkeypatch, changes):
    monkeypatch.setattr(recovery, "public_json", Mock(side_effect=[terminal(), jobs(**changes)]))
    with pytest.raises(StoreError):
        recovery.terminal_evidence(RUN, SHA)


def config(**changes):
    return {
        "run_prefix": RUN,
        "exclusive_writer": True,
        "prior_writer_terminated": True,
        "expected_claim_version_id": "claim-id",
        "expected_state_version_id": "state-id",
        **changes,
    }


@pytest.mark.parametrize(
    "changes", [{"exclusive_writer": False}, {"prior_writer_terminated": False}]
)
def test_operator_proofs_are_required_before_transport_creation(monkeypatch, changes):
    constructor = Mock()
    monkeypatch.setattr(recovery, "in_runtime", lambda: True)
    monkeypatch.setattr(recovery, "Boto3S3Transport", constructor)
    with pytest.raises(StoreError):
        recovery.reconcile(config(**changes))
    constructor.assert_not_called()


def test_stale_version_stops_before_qualification_or_ownership_transfer(monkeypatch):
    transport = Mock()
    transport.get.return_value = SimpleNamespace(
        version=json.dumps(["claim-id", '"etag"'], separators=(",", ":")),
        ledger=SimpleNamespace(
            run=SimpleNamespace(run_prefix=RUN),
            completed=None,
        ),
    )
    transport.get_blob.return_value = SimpleNamespace(
        version=json.dumps(["different-state", '"etag"'], separators=(",", ":"))
    )
    monkeypatch.setattr(recovery, "in_runtime", lambda: True)
    monkeypatch.setattr(recovery, "Boto3S3Transport", Mock(return_value=transport))
    qualifier = Mock()
    monkeypatch.setattr(recovery, "qualify_backend", qualifier)
    result = recovery.reconcile(config())
    assert result["cleanup"] == "not_attempted"
    assert result["ownership_transferred"] is False
    qualifier.assert_not_called()
    transport.create_blob.assert_not_called()


def test_missing_state_never_transfers_ownership_or_guesses_cleanup(monkeypatch):
    transport = Mock()
    transport.get.return_value = SimpleNamespace(
        ledger=SimpleNamespace(
            run=SimpleNamespace(run_prefix=RUN),
            completed=None,
        )
    )
    transport.get_blob.return_value = None
    monkeypatch.setattr(recovery, "in_runtime", lambda: True)
    monkeypatch.setattr(recovery, "Boto3S3Transport", Mock(return_value=transport))
    qualifier = Mock()
    monkeypatch.setattr(recovery, "qualify_backend", qualifier)
    result = recovery.reconcile(config())
    assert result["ownership_transferred"] is False
    assert result["cleanup"] == "not_attempted"
    qualifier.assert_not_called()
    transport.create_blob.assert_not_called()


@pytest.mark.parametrize("destroy_unknown", [False, True])
@pytest.mark.parametrize("state_count", [1, 2])
@pytest.mark.parametrize("transfer_unknown", [False, True])
def test_connected_recovery_preserves_unknown_history_and_never_replays(
    monkeypatch, destroy_unknown, state_count, transfer_unknown
):
    class Memory:
        def __init__(self):
            self.current = None
            self.archives, self.snapshots, self.blobs = {}, {}, {}
            self.counter = 0

        def version(self):
            self.counter += 1
            return json.dumps([f"version-{self.counter}", '"etag"'], separators=(",", ":"))

        def get(self, binding, key):
            return self.current

        def create_if_absent(self, binding, key, ledger):
            if self.current:
                raise storage.PreconditionFailed()
            self.current = storage.StoredLedger(ledger, self.version())
            return self.current

        def update_if_version(self, binding, key, ledger, expected):
            if self.current.version != expected:
                raise storage.PreconditionFailed()
            self.current = storage.StoredLedger(ledger, self.version())
            if transfer_unknown and ledger.recovery is not None and not ledger.receipts:
                raise storage.StoreError("synthetic-uncertain-CAS")
            return self.current

        def create_archive(self, binding, key, receipt):
            if key in self.archives:
                raise storage.PreconditionFailed()
            self.archives[key] = storage.StoredArchive(receipt, self.version())
            return self.archives[key]

        def get_archive(self, binding, key):
            return self.archives.get(key)

        def create_recovery_snapshot(self, binding, key, snapshot):
            if key in self.snapshots:
                raise storage.PreconditionFailed()
            self.snapshots[key] = storage.StoredRecoverySnapshot(snapshot, self.version())
            return self.snapshots[key]

        def get_recovery_snapshot(self, binding, key):
            return self.snapshots.get(key)

        def get_blob(self, binding, key):
            return self.blobs.get(key)

        def create_blob(self, binding, key, raw):
            if key in self.blobs:
                raise storage.PreconditionFailed()
            self.blobs[key] = StoredBlob(raw, self.version())
            return self.blobs[key]

    memory = Memory()
    binding = storage.StoreBinding(
        recovery.ENDPOINT, recovery.REGION, recovery.BUCKET, recovery.PREFIX, recovery.RUNTIME_ID
    )
    qualification = storage.Qualification(binding, *([True] * 9))
    identity = storage.RunIdentity(
        RUN,
        SHA,
        "b" * 32,
        "solomonhd.ai",
        (
            (f"{RUN}.txt.ci.solomonhd.ai", "TXT"),
            (f"{RUN}.cname.ci.solomonhd.ai", "CNAME"),
        ),
    )
    old = storage.CanaryStore(memory, binding, qualification)
    old.claim("prior-owner", identity, "absent")
    old.begin_intent("create", "absent")
    old.check_before_effect("absent")
    prior_version = memory.current.version
    state_key = recovery.PREFIX + f"runs/{RUN}/terraform.tfstate"
    parsed = {
        "version": 4,
        "resources": [
            {
                "mode": "managed",
                "instances": [
                    {"index_key": "txt", "attributes": {"id": "txt-id"}},
                    {"index_key": "cname", "attributes": {"id": "cname-id"}},
                ],
            }
        ],
    }
    memory.blobs[state_key] = StoredBlob(json.dumps(parsed).encode(), memory.version())
    original_state_version = memory.blobs[state_key].version
    actions = []

    class Driver:
        def __init__(self, root, **kwargs):
            self.checkpoint = kwargs["checkpoint"]

        def initialize(self):
            actions.append("initialize")

        def _state(self):
            blob = memory.blobs[state_key]
            return blob.data, json.loads(blob.data), state_count

        def apply(self, *_):
            raise AssertionError("Recovery must not replay apply")

        def destroy(self):
            actions.append("destroy")
            if destroy_unknown:
                raise recovery.StoreError("synthetic-private-provider-diagnostic")
            memory.blobs[state_key] = StoredBlob(b'{"version":4,"resources":[]}', memory.version())
            blob = memory.blobs[state_key]
            self.checkpoint(blob.data, blob.version)

        def verify_absence(self):
            actions.append("absence")
            assert json.loads(memory.blobs[state_key].data)["resources"] == []

    dns = Mock()
    dns._records.side_effect = lambda name, deadline: [
        {"id": "txt-id" if ".txt." in name else "cname-id"}
    ]
    monkeypatch.setattr(recovery, "in_runtime", lambda: True)
    monkeypatch.setattr(recovery, "Boto3S3Transport", Mock(return_value=memory))
    monkeypatch.setattr(recovery, "qualify_backend", Mock(return_value=qualification))
    monkeypatch.setattr(
        recovery,
        "terminal_evidence",
        Mock(
            return_value=f"https://github.com/{recovery.REPOSITORY}/actions/runs/43674454065/attempts/1"
        ),
    )
    monkeypatch.setattr(recovery, "TerraformDriver", Driver)
    monkeypatch.setattr(recovery, "CloudflareDNSClient", Mock(return_value=dns))
    monkeypatch.setattr(recovery.shutil, "copytree", lambda source, target: target.mkdir())
    request = config(
        expected_claim_version_id=json.loads(prior_version)[0],
        expected_state_version_id=json.loads(original_state_version)[0],
    )
    result = recovery.reconcile(request)
    if state_count != 2:
        assert result["ownership_transferred"] is False
        assert result["cleanup"] == "not_attempted"
        assert not memory.snapshots
        assert memory.current.version == prior_version
        assert actions == ["initialize"]
        return
    if transfer_unknown:
        assert result["ownership_transferred"] is None
        assert result["cleanup"] == "unknown"
        assert memory.current.ledger.recovery is not None
        assert not memory.archives
        assert actions == ["initialize"]
        return
    assert result["ownership_transferred"] is True
    assert result["original_outcome"] == "unknown"
    assert result["cleanup"] == ("unknown" if destroy_unknown else "verified")
    snapshot = next(iter(memory.snapshots.values())).snapshot
    assert snapshot.ledger.receipts[-1].outcome is None
    assert snapshot.claim_version == prior_version
    assert memory.current.ledger.recovery is not None
    assert (memory.current.ledger.completed is not None) is not destroy_unknown
    assert actions == (
        ["initialize", "destroy"] if destroy_unknown else ["initialize", "destroy", "absence"]
    )
