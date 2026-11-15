"""Synthetic CAS and completed succession only, not Wasabi qualification."""

import importlib.util
import json
import sys
from dataclasses import fields, replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# Do not collide with existing suites' top-level main.py imports.
spec = importlib.util.spec_from_file_location(
    "canary_store_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_store_test_package import canary_store as store

PREFIX = "gha-1794700000-123-1"
BINDING = store.StoreBinding(
    "https://synthetic.invalid", "synthetic-region", "sandbox", "canary/", "pinned-test-tuple"
)
RUN = store.RunIdentity(
    PREFIX,
    "a" * 40,
    "b" * 32,
    "solomonhd.ai",
    ((f"{PREFIX}.txt.ci.solomonhd.ai", "TXT"), (f"{PREFIX}.cname.ci.solomonhd.ai", "CNAME")),
)
FLAGS = [field.name for field in fields(store.Qualification) if field.name != "binding"]
QUALIFIED = store.Qualification(BINDING, **dict.fromkeys(FLAGS, True))
SENTINEL = "synthetic-private-provider-response"


class MemoryTransport:
    """Test-only memory fake, intentionally no production implementation."""

    def __init__(self):
        self.value = None
        self.serial = 0
        self.calls = []
        self.failure = None
        self.commit_then_fail = False
        self.before_update = None
        self.archives = {}
        self.archive_commit_then_fail = False

    def get(self, binding, key):
        self.calls.append("get")
        if self.failure == "get":
            raise RuntimeError(SENTINEL)
        return self.value

    def write(self, ledger):
        self.serial += 1
        self.value = store.StoredLedger(ledger, f"opaque-{self.serial}")
        if self.commit_then_fail:
            raise RuntimeError(SENTINEL)
        return self.value

    def create_if_absent(self, binding, key, ledger):
        self.calls.append("create")
        assert binding == BINDING and key == "canary/maintenance.json"
        if self.failure == "create":
            raise RuntimeError(SENTINEL)
        if self.value is not None:
            raise store.PreconditionFailed(SENTINEL)
        return self.write(ledger)

    def update_if_version(self, binding, key, ledger, expected_version):
        self.calls.append("update")
        if self.before_update:
            self.before_update()
        if self.failure == "update":
            raise RuntimeError(SENTINEL)
        if self.value is None or self.value.version != expected_version:
            raise store.PreconditionFailed(SENTINEL)
        return self.write(ledger)

    def create_archive(self, binding, key, receipt):
        self.calls.append("create_archive")
        if self.failure == "create_archive":
            raise RuntimeError(SENTINEL)
        if key in self.archives:
            raise store.PreconditionFailed(SENTINEL)
        self.serial += 1
        archive = store.StoredArchive(receipt, f"archive-{self.serial}")
        self.archives[key] = archive
        if self.archive_commit_then_fail:
            raise RuntimeError(SENTINEL)
        return archive

    def get_archive(self, binding, key):
        self.calls.append("get_archive")
        if self.failure == "get_archive":
            raise RuntimeError(SENTINEL)
        return self.archives.get(key)


def session(transport=None, qualification=QUALIFIED, binding=BINDING):
    return store.CanaryStore(transport or MemoryTransport(), binding, qualification)


def pending(transport=None):
    client = session(transport)
    client.claim("writer-1", RUN, "state-0")
    client.begin_intent("create", "state-0")
    return client


def test_durable_identity_and_intent_precede_one_effect_and_result():
    transport = MemoryTransport()
    client = pending(transport)
    intent = client.check_before_effect("state-0")
    assert intent.ledger.run == RUN
    assert intent.ledger.owner == "writer-1"
    assert intent.ledger.generation == 1
    assert intent.ledger.receipts == (store.Receipt("create", "state-0"),)
    result = client.record_result("succeeded", "state-0", "state-1")
    assert result.ledger.generation == 2
    assert result.ledger.state_generation == "state-1"
    assert result.ledger.receipts[-1].outcome == "succeeded"
    assert transport.calls == [
        "create",
        "get",
        "get",
        "update",
        "get",
        "get",
        "get",
        "update",
        "get",
    ]
    client.begin_intent("destroy", "state-1")


@pytest.mark.parametrize("flag", FLAGS)
def test_every_qualification_flag_required_before_mutation(flag):
    transport = MemoryTransport()
    with pytest.raises(store.StoreError, match="qualification"):
        session(transport, replace(QUALIFIED, **{flag: False})).claim("writer", RUN, "s0")
    assert transport.calls == []


@pytest.mark.parametrize("field", ["endpoint", "region", "bucket", "prefix", "runtime_identity"])
def test_qualification_bound_to_exact_target_and_runtime(field):
    transport = MemoryTransport()
    change = "https://other.invalid" if field == "endpoint" else "different/"
    with pytest.raises(store.StoreError):
        session(transport, binding=replace(BINDING, **{field: change})).claim("writer", RUN, "s0")
    assert transport.calls == []


@pytest.mark.parametrize(
    "changes",
    [
        {"endpoint": "http://synthetic.invalid"},
        {"endpoint": "https://user:password@synthetic.invalid"},
        {"endpoint": "https://synthetic.invalid/?token=secret"},
        {"prefix": "../sandbox/"},
        {"prefix": "/sandbox/"},
        {"prefix": "sandbox//"},
        {"prefix": ""},
        {"runtime_identity": ""},
    ],
)
def test_invalid_binding_rejected_without_io(changes):
    binding = replace(BINDING, **changes)
    transport = MemoryTransport()
    with pytest.raises(store.StoreError):
        session(transport, replace(QUALIFIED, binding=binding), binding).claim("writer", RUN, "s0")
    assert not transport.calls


@pytest.mark.parametrize(
    "changes",
    [
        {"run_prefix": "gha-0-123-1"},
        {"revision": "short"},
        {"zone_id": "unknown"},
        {"zone_name": "production.invalid"},
        {"intended_records": ()},
        {"intended_records": (("outside.invalid", "TXT"),)},
        {"intended_records": tuple(reversed(RUN.intended_records))},
    ],
)
def test_exact_immutable_identity_required_before_claim(changes):
    transport = MemoryTransport()
    with pytest.raises(store.StoreError, match="identity"):
        session(transport).claim("writer", replace(RUN, **changes), "s0")
    assert transport.calls == []


def test_competing_writer_and_same_owner_restart_cannot_take_over():
    transport = MemoryTransport()
    first = pending(transport)
    for owner in ("writer-2", "writer-1"):
        with pytest.raises(store.StoreError, match="no automatic takeover"):
            session(transport).claim(owner, RUN, "state-0")
    assert transport.value == first.retained
    assert not hasattr(first.retained.ledger, "expires")


@pytest.mark.parametrize("boundary", ["intent", "effect", "result"])
@pytest.mark.parametrize("change", ["owner", "generation", "run", "version", "absent"])
def test_lost_ownership_or_changed_generation_blocks_every_boundary(boundary, change):
    transport = MemoryTransport()
    client = pending(transport)
    if boundary == "result":
        client.check_before_effect("state-0")
    original = transport.value
    if change == "owner":
        transport.value = replace(original, ledger=replace(original.ledger, owner="new-writer"))
    elif change == "generation":
        transport.value = replace(original, ledger=replace(original.ledger, generation=9))
    elif change == "run":
        transport.value = replace(
            original, ledger=replace(original.ledger, run=replace(RUN, revision="c" * 40))
        )
    elif change == "version":
        transport.value = replace(original, version="other-opaque-version")
    else:
        transport.value = None
    calls = len(transport.calls)
    with pytest.raises(store.StoreError, match="Ownership or generation"):
        if boundary == "intent":
            client.begin_intent("update", "state-0")
        elif boundary == "effect":
            client.check_before_effect("state-0")
        else:
            client.record_result("succeeded", "state-0", "state-1")
    assert transport.calls[calls:] == ["get"]
    assert client.retained == original
    with pytest.raises(store.StoreError, match="blocked"):
        client.check_before_effect("state-0")


@pytest.mark.parametrize("boundary", ["intent", "effect", "result"])
def test_unexpected_external_state_generation_blocks(boundary):
    client = pending()
    if boundary == "result":
        client.check_before_effect("state-0")
    with pytest.raises(store.StoreError, match="generation"):
        if boundary == "intent":
            client.begin_intent("update", "unexpected")
        elif boundary == "effect":
            client.check_before_effect("unexpected")
        else:
            client.record_result("succeeded", "unexpected", "state-1")


def test_conditional_update_race_never_overwrites_newer_writer():
    transport = MemoryTransport()
    client = session(transport)
    client.claim("writer-1", RUN, "state-0")

    def competing_update():
        transport.value = replace(transport.value, version="new-generation")

    transport.before_update = competing_update
    with pytest.raises(store.StoreError, match="precondition"):
        client.begin_intent("create", "state-0")
    assert transport.calls.count("update") == 1
    assert transport.value.version == "new-generation"
    assert transport.value.ledger.receipts == ()


@pytest.mark.parametrize("operation", ["create", "get", "update"])
def test_backend_loss_is_sanitized_and_never_retried(operation):
    transport = MemoryTransport()
    client = session(transport)
    if operation != "create":
        client.claim("writer-1", RUN, "state-0")
    transport.failure = operation
    with pytest.raises(store.StoreError) as error:
        if operation == "create":
            client.claim("writer-1", RUN, "state-0")
        else:
            client.begin_intent("create", "state-0")
    assert SENTINEL not in str(error.value)
    assert error.value.__suppress_context__
    calls = list(transport.calls)
    with pytest.raises(store.StoreError, match="blocked"):
        client.begin_intent("destroy", "state-0")
    assert transport.calls == calls


def test_uncertain_claim_commit_is_retained_and_cannot_be_reclaimed():
    transport = MemoryTransport()
    transport.commit_then_fail = True
    client = session(transport)
    with pytest.raises(store.StoreError, match="Claim outcome unknown"):
        client.claim("writer-1", RUN, "state-0")
    assert transport.value.ledger.run == RUN
    assert client.attempted.run == RUN
    assert client.retained is None
    assert transport.calls == ["create"]
    transport.commit_then_fail = False
    with pytest.raises(store.StoreError, match="no automatic takeover"):
        session(transport).claim("writer-2", RUN, "state-0")


@pytest.mark.parametrize("boundary", ["intent", "result"])
def test_uncertain_receipt_write_retains_last_confirmation_and_actual_commit(boundary):
    transport = MemoryTransport()
    client = session(transport)
    client.claim("writer-1", RUN, "state-0")
    if boundary == "result":
        client.begin_intent("create", "state-0")
        client.check_before_effect("state-0")
    confirmed = client.retained
    transport.commit_then_fail = True
    with pytest.raises(store.StoreError, match="Receipt outcome unknown"):
        if boundary == "intent":
            client.begin_intent("create", "state-0")
        else:
            client.record_result("succeeded", "state-0", "state-1")
    assert client.retained == confirmed
    assert client.attempted.generation == confirmed.ledger.generation + 1
    assert transport.value.ledger.generation == confirmed.ledger.generation + 1
    assert not hasattr(client, "release") and not hasattr(client, "delete")


def test_uncertain_create_result_is_durable_and_prevents_retry_or_cleanup():
    client = pending()
    client.check_before_effect("state-0")
    retained = client.record_result("unknown", "state-0", "uncertain-state")
    assert retained.ledger.receipts[-1].outcome == "unknown"
    for phase in ("create", "destroy"):
        with pytest.raises(store.StoreError, match="blocked"):
            client.begin_intent(phase, "uncertain-state")


def test_pending_intent_cannot_be_overwritten_or_effect_implicitly_retried():
    client = pending()
    with pytest.raises(store.StoreError, match="Uncertain prior effect"):
        client.begin_intent("destroy", "state-0")
    client = pending()
    client.check_before_effect("state-0")
    with pytest.raises(store.StoreError, match="no implicit retry"):
        client.check_before_effect("state-0")


def test_effect_and_result_require_pending_intent_and_effect_boundary():
    client = session()
    client.claim("writer-1", RUN, "state-0")
    with pytest.raises(store.StoreError, match="pending intent"):
        client.check_before_effect("state-0")
    client.begin_intent("create", "state-0")
    with pytest.raises(store.StoreError, match="result boundary"):
        client.record_result("succeeded", "state-0", "state-1")


def test_definitive_failure_may_record_separate_cleanup_intent():
    client = pending()
    client.check_before_effect("state-0")
    client.record_result("failed", "state-0", "partial-state")
    cleanup = client.begin_intent("destroy", "partial-state")
    assert [receipt.phase for receipt in cleanup.ledger.receipts] == ["create", "destroy"]


def test_backend_loss_at_result_retains_pending_effect_without_cleanup():
    transport = MemoryTransport()
    client = pending(transport)
    client.check_before_effect("state-0")
    transport.failure = "get"
    with pytest.raises(store.StoreError, match="Ownership unavailable"):
        client.record_result("succeeded", "state-0", "state-1")
    assert transport.value.ledger.receipts[-1].outcome is None
    assert client.retained == transport.value
    with pytest.raises(store.StoreError, match="blocked"):
        client.begin_intent("destroy", "state-0")


def test_completed_effect_does_not_release_claim_or_enable_next_run():
    transport = MemoryTransport()
    client = pending(transport)
    client.check_before_effect("state-0")
    client.record_result("succeeded", "state-0", "state-1")
    with pytest.raises(store.StoreError, match="no automatic takeover"):
        session(transport).claim("next-run", RUN, "state-1")
    assert transport.value == client.retained


@pytest.mark.parametrize("operation", ["claim", "intent", "result"])
def test_invalid_write_confirmation_blocks_session(operation):
    transport = MemoryTransport()
    client = session(transport)
    if operation != "claim":
        client.claim("writer-1", RUN, "state-0")
    if operation == "result":
        client.begin_intent("create", "state-0")
        client.check_before_effect("state-0")
    original_write = transport.write

    def invalid_confirmation(ledger):
        return replace(original_write(ledger), version="")

    transport.write = invalid_confirmation
    with pytest.raises(store.StoreError, match="confirmation invalid"):
        if operation == "claim":
            client.claim("writer-1", RUN, "state-0")
        elif operation == "intent":
            client.begin_intent("create", "state-0")
        else:
            client.record_result("succeeded", "state-0", "state-1")
    assert transport.value.ledger == client.attempted
    with pytest.raises(store.StoreError, match="blocked"):
        client.check_before_effect("state-0")


def cleaned(transport=None, primary="succeeded"):
    client = pending(transport)
    client.check_before_effect("state-0")
    client.record_result(primary, "state-0", "state-1")
    for phase, before, after in (
        ("destroy", "state-1", "state-2"),
        ("absence", "state-2", "state-2"),
    ):
        client.begin_intent(phase, before)
        client.check_before_effect(before)
        client.record_result("succeeded", before, after)
    return client


def next_run(number=2):
    prefix = f"gha-1794700000-123-{number}"
    return replace(
        RUN,
        run_prefix=prefix,
        intended_records=(
            (f"{prefix}.txt.ci.solomonhd.ai", "TXT"),
            (f"{prefix}.cname.ci.solomonhd.ai", "CNAME"),
        ),
    )


@pytest.mark.parametrize("primary", ["succeeded", "failed"])
def test_verified_cleanup_archived_then_completed_then_successor(primary):
    transport = MemoryTransport()
    first = cleaned(transport, primary)
    before = first.retained
    completed = first.complete_verified("writer-1", "state-2")
    pointer = completed.ledger.completed
    assert pointer.key == f"canary/runs/{PREFIX}/completed.json"
    assert completed.ledger.generation == before.ledger.generation + 1
    assert transport.archives[pointer.key] == first.archive_retained
    assert first.archive_retained.receipt == store.CompletedReceipt(before.ledger, before.version)
    assert first.archive_attempted == first.archive_retained.receipt
    assert transport.calls[-5:] == ["create_archive", "get_archive", "get", "update", "get"]
    second = session(transport)
    successor = second.claim("writer-2", next_run(), "state-2")
    assert successor.ledger.predecessor == pointer
    assert successor.ledger.completed is None
    assert successor.ledger.owner == "writer-2"
    assert successor.ledger.generation == 0
    assert successor.ledger.receipts == ()
    assert len(transport.archives) == 1
    second.begin_intent("create", "state-2")
    with pytest.raises(store.StoreError):
        first.begin_intent("create", "state-2")


@pytest.mark.parametrize(
    "change",
    [
        "owner",
        "state",
        "generation",
        "pending",
        "failed_absence",
        "unknown",
        "missing_destroy",
        "failed_destroy",
        "not_last_absence",
    ],
)
def test_completion_requires_exact_owner_generation_and_verified_cleanup(change):
    transport = MemoryTransport()
    client = cleaned(transport)
    owner, state = "writer-1", "state-2"
    if change == "owner":
        owner = "other"
    elif change == "state":
        state = "stale-state"
    elif change == "generation":
        transport.value = replace(transport.value, version="changed")
    else:
        receipts = list(client.retained.ledger.receipts)
        if change == "pending":
            client.begin_intent("plan", state)
        else:
            if change == "failed_absence":
                receipts[-1] = replace(receipts[-1], outcome="failed")
            elif change == "unknown":
                receipts[0] = replace(receipts[0], outcome="unknown")
            elif change == "missing_destroy":
                receipts[-2] = replace(receipts[-2], phase="plan")
            elif change == "failed_destroy":
                receipts[-2] = replace(receipts[-2], outcome="failed")
            elif change == "not_last_absence":
                receipts[-1] = replace(receipts[-1], phase="validate")
            # Model a retained malformed record, never a legitimate protocol write.
            client._current = transport.value = replace(
                transport.value, ledger=replace(transport.value.ledger, receipts=tuple(receipts))
            )
    with pytest.raises(store.StoreError):
        client.complete_verified(owner, state)
    assert transport.archives == {}
    with pytest.raises(store.StoreError, match="blocked"):
        client.complete_verified("writer-1", "state-2")


@pytest.mark.parametrize(
    "operation",
    [
        "create_archive",
        "get_archive",
        "update",
        "get_after_archive",
        "archive_commit",
        "cas_commit",
        "archive_readback",
        "archive_confirmation",
        "cas_race",
    ],
)
def test_completion_uncertainty_never_retries_or_releases(operation):
    transport = MemoryTransport()
    client = cleaned(transport)
    before = client.retained
    if operation in ("create_archive", "get_archive", "update"):
        transport.failure = operation
    elif operation == "archive_commit":
        transport.archive_commit_then_fail = True
    elif operation == "cas_commit":
        transport.commit_then_fail = True
    elif operation == "get_after_archive":
        original = transport.get_archive

        def fail_next_get(binding, key):
            result = original(binding, key)
            transport.failure = "get"
            return result

        transport.get_archive = fail_next_get
    elif operation == "archive_readback":
        transport.get_archive = lambda *args: None
    elif operation == "archive_confirmation":
        original = transport.create_archive
        transport.create_archive = lambda *args: replace(original(*args), version="")
    else:
        transport.before_update = lambda: setattr(
            transport, "value", replace(transport.value, version="racer")
        )
    with pytest.raises(store.StoreError) as error:
        client.complete_verified("writer-1", "state-2")
    assert SENTINEL not in str(error.value)
    assert client.retained == before
    assert client.archive_attempted == store.CompletedReceipt(before.ledger, before.version)
    calls = list(transport.calls)
    with pytest.raises(store.StoreError, match="blocked"):
        client.complete_verified("writer-1", "state-2")
    with pytest.raises(store.StoreError, match="blocked"):
        client.begin_intent("create", "state-2")
    assert calls == transport.calls
    if operation == "cas_commit":
        assert transport.value.ledger.completed is not None
        assert client.attempted == transport.value.ledger


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "version",
        "body",
        "claim_version",
        "malformed",
        "key",
        "state",
        "same_run",
        "read_failure",
        "active_missing",
    ],
)
def test_successor_refuses_unverified_or_malformed_history(change):
    transport = MemoryTransport()
    first = cleaned(transport)
    completed = first.complete_verified("writer-1", "state-2")
    pointer = completed.ledger.completed
    archive = transport.archives[pointer.key]
    run, state = next_run(), "state-2"
    if change == "missing":
        del transport.archives[pointer.key]
    elif change == "version":
        transport.archives[pointer.key] = replace(archive, version="wrong")
    elif change == "body":
        transport.archives[pointer.key] = replace(
            archive,
            receipt=replace(archive.receipt, ledger=replace(archive.receipt.ledger, owner="other")),
        )
    elif change == "claim_version":
        transport.archives[pointer.key] = replace(
            archive, receipt=replace(archive.receipt, claim_version=completed.version)
        )
    elif change == "malformed":
        transport.archives[pointer.key] = store.StoredArchive(None, "bad")
    elif change == "key":
        transport.value = replace(
            completed,
            ledger=replace(
                completed.ledger, completed=replace(pointer, key="other/runs/fake/completed.json")
            ),
        )
    elif change == "state":
        transport.value = replace(
            completed, ledger=replace(completed.ledger, state_generation="other-state")
        )
    elif change == "same_run":
        run = RUN
    elif change == "read_failure":
        transport.failure = "get_archive"
    else:
        transport.get = lambda *args: None
    before = transport.value
    client = session(transport)
    calls = len(transport.calls)
    with pytest.raises(store.StoreError) as error:
        client.claim("writer-2", run, state)
    assert SENTINEL not in str(error.value)
    assert "update" not in transport.calls[calls:]
    assert transport.value == before
    with pytest.raises(store.StoreError, match="blocked"):
        client.claim("writer-2", run, state)


def test_two_successors_racing_only_one_cas_wins():
    transport = MemoryTransport()
    cleaned(transport).complete_verified("writer-1", "state-2")
    first, second = session(transport), session(transport)

    def competitor():
        transport.before_update = None
        second.claim("writer-3", next_run(3), "state-2")

    transport.before_update = competitor
    with pytest.raises(store.StoreError, match="precondition"):
        first.claim("writer-2", next_run(), "state-2")
    assert transport.value.ledger.owner == "writer-3"
    assert first.retained.ledger.completed is not None
    assert first.attempted.owner == "writer-2"
    assert len(transport.archives) == 1


def test_completed_owner_cannot_continue_or_complete_again():
    transport = MemoryTransport()
    client = cleaned(transport)
    client.complete_verified("writer-1", "state-2")
    with pytest.raises(store.StoreError, match="Completed session"):
        client.begin_intent("create", "state-2")
    assert transport.calls.count("create_archive") == 1


@pytest.mark.parametrize("kind", ["ledger", "archive"])
def test_strict_serialization_roundtrip_and_safe_errors(kind):
    client = cleaned()
    value = (
        client.retained.ledger
        if kind == "ledger"
        else store.CompletedReceipt(client.retained.ledger, client.retained.version)
    )
    encode, decode = (
        (store.encode_ledger, store.decode_ledger)
        if kind == "ledger"
        else (store.encode_archive, store.decode_archive)
    )
    payload = encode(value)
    assert type(payload) is bytes
    assert decode(payload) == value
    assert encode(decode(payload)) == payload
    invalid = [
        b"",
        SENTINEL.encode(),
        b"\xff",
        b"[]",
        b"null",
        b"{" * 5000,
        b"x" * 262145,
        b'{"schema":1,"schema":1,"kind":"ledger","body":{}}',
    ]
    row = json.loads(payload)
    for key, replacement in (("schema", True), ("schema", 2), ("kind", "other"), ("body", [])):
        invalid.append(json.dumps({**row, key: replacement}).encode())
    invalid.append(json.dumps({**row, "secret": SENTINEL}).encode())
    for bad in invalid:
        with pytest.raises(store.StoreError) as error:
            decode(bad)
        assert SENTINEL not in str(error.value)
        assert error.value.__suppress_context__


@pytest.mark.parametrize(
    "field,value",
    [
        ("owner", ""),
        ("owner", "\n"),
        ("owner", "x" * 1025),
        ("generation", True),
        ("generation", -1),
        ("generation", 99),
        ("state_generation", []),
        ("receipts", []),
        ("predecessor", {"key": "../completed.json", "version": "v"}),
    ],
)
def test_strict_ledger_json_rejects_bad_typed_body(field, value):
    row = json.loads(store.encode_ledger(cleaned().retained.ledger))
    row["body"][field] = value
    with pytest.raises(store.StoreError):
        store.decode_ledger(json.dumps(row).encode())


def test_serialization_rejects_unknown_missing_receipts_and_broken_continuity():
    original = json.loads(store.encode_ledger(cleaned().retained.ledger))
    for mutation in ("extra", "missing", "pending", "unknown", "state", "count"):
        row = json.loads(json.dumps(original))
        receipt = row["body"]["receipts"][0]
        if mutation == "extra":
            receipt["raw_provider"] = SENTINEL
        elif mutation == "missing":
            receipt.pop("phase")
        elif mutation in ("pending", "unknown"):
            receipt["outcome"] = None if mutation == "pending" else "unknown"
        elif mutation == "state":
            receipt["resulting_state_generation"] = "wrong"
        else:
            row["body"]["receipts"] *= 129
        with pytest.raises(store.StoreError):
            store.decode_ledger(json.dumps(row).encode())


def test_completed_serialization_preserves_history_and_rejects_unverified_archive():
    client = cleaned()
    completed = client.complete_verified("writer-1", "state-2")
    assert store.decode_ledger(store.encode_ledger(completed.ledger)) == completed.ledger
    with pytest.raises(store.StoreError):
        store.encode_archive(store.CompletedReceipt(completed.ledger, completed.version))
    with pytest.raises(store.StoreError):
        store.encode_archive(store.CompletedReceipt(store.Ledger(RUN, "owner", 0, "s0"), "v"))


def test_immutable_archive_collision_never_overwrites_prior_receipt():
    transport = MemoryTransport()
    client = cleaned(transport)
    key = f"canary/runs/{PREFIX}/completed.json"
    original = store.StoredArchive(
        store.CompletedReceipt(client.retained.ledger, "other-version"), "immutable"
    )
    transport.archives[key] = original
    with pytest.raises(store.StoreError):
        client.complete_verified("writer-1", "state-2")
    assert transport.archives[key] == original
    assert transport.value.ledger.completed is None
    assert transport.calls.count("create_archive") == 1


@pytest.mark.parametrize("failure", ["cas_failed", "cas_committed", "readback", "confirmation"])
def test_successor_uncertain_cas_keeps_predecessor_and_attempted_claim(failure):
    transport = MemoryTransport()
    previous = cleaned(transport).complete_verified("writer-1", "state-2")
    client = session(transport)
    if failure == "cas_failed":
        transport.failure = "update"
    elif failure == "cas_committed":
        transport.commit_then_fail = True
    else:
        original = transport.update_if_version

        def update(*args):
            result = original(*args)
            if failure == "readback":
                transport.failure = "get"
                return result
            return replace(result, version="")

        transport.update_if_version = update
    with pytest.raises(store.StoreError):
        client.claim("writer-2", next_run(), "new-run-initial-state")
    assert client.attempted.owner == "writer-2"
    assert client.attempted.predecessor == previous.ledger.completed
    assert client.archive_retained == transport.archives[previous.ledger.completed.key]
    if failure != "readback":
        assert client.retained == previous
    else:
        assert client.retained == transport.value
    calls = list(transport.calls)
    with pytest.raises(store.StoreError, match="blocked"):
        client.claim("writer-2", next_run(), "new-run-initial-state")
    assert transport.calls == calls


def test_history_chain_survives_multiple_completed_runs():
    transport = MemoryTransport()
    first = cleaned(transport).complete_verified("writer-1", "state-2")
    second = session(transport)
    second.claim("writer-2", next_run(), "new-state")
    for phase in ("destroy", "absence"):
        second.begin_intent(phase, "new-state")
        second.check_before_effect("new-state")
        second.record_result("succeeded", "new-state", "new-state")
    completed = second.complete_verified("writer-2", "new-state")
    archived_second = transport.archives[completed.ledger.completed.key]
    assert archived_second.receipt.ledger.predecessor == first.ledger.completed
    third = session(transport).claim("writer-3", next_run(3), "third-initial-state")
    assert third.ledger.predecessor == completed.ledger.completed
    assert len(transport.archives) == 2


@pytest.mark.parametrize("phase", sorted(store._PHASES))
def test_runtime_phase_names_have_serializable_durable_intents(phase):
    client = session()
    client.claim("writer", RUN, "s0")
    pending_ledger = client.begin_intent(phase, "s0").ledger
    assert store.decode_ledger(store.encode_ledger(pending_ledger)) == pending_ledger


def test_encode_rejects_untrusted_dataclass_values_without_echo():
    bad = replace(cleaned().retained.ledger, owner=object())
    with pytest.raises(store.StoreError) as error:
        store.encode_ledger(bad)
    assert "object at" not in str(error.value)
    assert error.value.__suppress_context__


@pytest.mark.parametrize("boundary", ["claim", "update", "archive"])
@pytest.mark.parametrize("malformed", [None, "raw", 1])
def test_malformed_transport_confirmation_permanently_blocks(boundary, malformed):
    transport = MemoryTransport()
    client = session(transport) if boundary == "claim" else cleaned(transport)
    if boundary == "claim":
        transport.create_if_absent = lambda *args: malformed
        action = lambda: client.claim("writer", RUN, "s0")
    elif boundary == "update":
        transport.update_if_version = lambda *args: malformed
        action = lambda: client.begin_intent("plan", "state-2")
    else:
        transport.create_archive = lambda *args: malformed
        action = lambda: client.complete_verified("writer-1", "state-2")
    with pytest.raises(store.StoreError):
        action()
    with pytest.raises(store.StoreError, match="blocked"):
        action()


@pytest.mark.parametrize("encoding", ["utf-16", "utf-32"])
def test_json_wire_schema_requires_utf8(encoding):
    payload = store.encode_ledger(cleaned().retained.ledger).decode("utf-8").encode(encoding)
    with pytest.raises(store.StoreError):
        store.decode_ledger(payload)
