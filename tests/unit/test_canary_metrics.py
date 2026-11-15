"""Synthetic observations only; no S3, clients, credentials or live DNS."""

import importlib.util
import json
import sys
import traceback
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, cast

import pytest

ROOT = Path(__file__).resolve().parents[2]
# Match other canary tests without colliding with top-level main.py imports.
spec = importlib.util.spec_from_file_location(
    "canary_metrics_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
assert spec is not None
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_metrics_test_package.canary_identity import ZONE_NAME, record_name
from canary_metrics_test_package.canary_metrics import (
    LedgerVersionObservation,
    MetricsError,
    measure_phases,
)
from canary_metrics_test_package.canary_store import (
    CompletedPointer,
    Ledger,
    Phase,
    Receipt,
    RunIdentity,
    decode_ledger,
    encode_ledger,
)

RUN = "gha-1794643200-123-1"
REVISION = "a" * 40
BASE = datetime(2026, 11, 14, 10, tzinfo=timezone.utc)
NOW = BASE + timedelta(days=1)
SECRET = "synthetic-credential-DO-NOT-REPORT"


def history(
    phases: tuple[Phase, ...] = ("create", "destroy", "absence")
) -> list[LedgerVersionObservation]:
    identity = RunIdentity(
        RUN,
        REVISION,
        "b" * 32,
        ZONE_NAME,
        ((record_name(RUN, "txt"), "TXT"), (record_name(RUN, "cname"), "CNAME")),
    )
    ledger = Ledger(identity, "private-owner", 0, "state-0")
    ledgers = [ledger]
    for index, phase in enumerate(phases):
        pending = Receipt(phase, ledger.state_generation)
        ledger = replace(
            ledger, generation=ledger.generation + 1, receipts=(*ledger.receipts, pending)
        )
        ledgers.append(ledger)
        state = f"state-{index + 1}"
        ledger = replace(
            ledger,
            generation=ledger.generation + 1,
            state_generation=state,
            receipts=(
                *ledger.receipts[:-1],
                replace(pending, outcome="succeeded", resulting_state_generation=state),
            ),
        )
        ledgers.append(ledger)
    ledgers.append(
        replace(
            ledger,
            generation=ledger.generation + 1,
            completed=CompletedPointer(
                f"canary/runs/{RUN}/completed.json",
                "archive-version",
                f"opaque-{ledger.generation}",
            ),
        )
    )
    return [
        LedgerVersionObservation(
            encode_ledger(item), f"opaque-{index}", BASE + timedelta(seconds=index * 3)
        )
        for index, item in enumerate(ledgers)
    ]


def measure(rows: list[LedgerVersionObservation], **kwargs: Any) -> Any:
    return measure_phases(rows, run_prefix=RUN, revision=REVISION, now=NOW, **kwargs)


def mutate(row: LedgerVersionObservation, **changes: Any) -> LedgerVersionObservation:
    body = json.loads(row.data)
    body["body"].update(changes)
    return replace(row, data=json.dumps(body).encode())


def test_selected_successful_run_intervals() -> None:
    result = measure(history())
    assert [item.phase for item in result] == ["create", "destroy", "absence"]
    for index, item in enumerate(result):
        assert item.start == BASE + timedelta(seconds=(2 * index + 1) * 3)
        assert item.end == BASE + timedelta(seconds=(2 * index + 2) * 3)
        assert item.start.tzinfo is timezone.utc
        assert item.end.tzinfo is timezone.utc
        assert item.approximate_interval_seconds == 3
        assert item.timestamp_resolution_seconds == 1
        assert "protected I/O and verification" in item.interval_scope
        assert "not provider-only" in item.interval_scope
        assert set(asdict(item)) == {
            "phase",
            "start",
            "end",
            "approximate_interval_seconds",
            "interval_scope",
            "timestamp_resolution_seconds",
        }


def test_every_supported_phase_and_repeated_phase() -> None:
    phases: tuple[Phase, ...] = (
        "initialize",
        "create",
        "create_api",
        "create_dns",
        "validate",
        "update",
        "update_api",
        "update_dns",
        "plan",
        "cleanup_state",
        "create",
        "destroy",
        "absence",
    )
    assert tuple(item.phase for item in measure(history(phases))) == phases


def test_input_order_and_opaque_versions_are_not_time_order() -> None:
    rows = history()
    assert measure(rows[::-1]) == measure(rows)
    rows = [replace(row, version=f"z-{100 - index}") for index, row in enumerate(rows)]
    final = decode_ledger(rows[-1].data)
    assert final.completed is not None
    rows[-1] = replace(
        rows[-1],
        data=encode_ledger(
            replace(
                final,
                completed=replace(final.completed, claim_version=rows[-2].version),
            )
        ),
    )
    assert measure(rows) == measure(history())


def test_duplicate_observations_and_completion_do_not_extend_end() -> None:
    rows = history()
    baseline = measure(rows)
    rows += [
        rows[2],
        rows[0],
        replace(rows[-1], version="later-completed", last_modified=BASE + timedelta(hours=1)),
    ]
    assert measure(rows) == baseline


def test_first_successful_result_is_used_not_repeated_snapshot() -> None:
    rows = history()
    rows.append(
        replace(rows[2], version="duplicate-result", last_modified=BASE + timedelta(seconds=7))
    )
    assert measure(rows) == measure(history())


def test_equal_one_second_timestamps_allow_zero_interval() -> None:
    rows = [replace(row, last_modified=BASE) for row in history()]
    assert all(item.approximate_interval_seconds == 0 for item in measure(rows))


@pytest.mark.parametrize("as_string", [False, True])
def test_utc_offsets_are_normalized(as_string: bool) -> None:
    rows = history()
    offset = timezone(timedelta(hours=5, minutes=30))
    rows = [replace(row, last_modified=(row.last_modified.astimezone(offset).isoformat() if as_string else row.last_modified.astimezone(offset))) for row in rows]  # type: ignore[union-attr]
    assert measure(rows) == measure(history())


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-14",
        "2026-11-14 10:00:00Z",
        "2026-11-14T10:00:00",
        "not-a-date",
        "2026-13-14T10:00:00Z",
        "2026-11-14T25:00:00Z",
        "2026-11-14T10:00:60Z",
        "2026-11-14T10:00:00+25:00",
        "2026-11-14T10:00:00+01:99",
        "2026-11-14T10:00:00Z\n",
        "NaN",
        None,
        1,
        datetime(2026, 11, 14),
        NOW + timedelta(seconds=1),
        "2026-11-16T00:00:00Z",
    ],
)
def test_malformed_naive_or_future_dates_rejected(value: Any) -> None:
    rows = history()
    rows[1] = replace(rows[1], last_modified=value)
    with pytest.raises(MetricsError):
        measure(rows)


@pytest.mark.parametrize("now", [datetime(2026, 11, 15), None, "bad"])
def test_invalid_reference_clock_rejected(now: Any) -> None:
    with pytest.raises(MetricsError):
        measure_phases(history(), run_prefix=RUN, revision=REVISION, now=now)


@pytest.mark.parametrize("index", range(8))
def test_each_missing_generation_rejected(index: int) -> None:
    rows = history()
    del rows[index]
    with pytest.raises(MetricsError):
        measure(rows)


def test_failed_and_nonterminal_histories_rejected() -> None:
    for count in range(1, 8):
        with pytest.raises(MetricsError):
            measure(history()[:count])


@pytest.mark.parametrize("index", [1, 2, 3, 4, 5, 6, 7])
def test_inconsistent_chronology_rejected(index: int) -> None:
    rows = history()
    rows[index] = replace(rows[index], last_modified=BASE - timedelta(seconds=1))
    with pytest.raises(MetricsError):
        measure(rows)


@pytest.mark.parametrize(
    "changes",
    [
        {"generation": 99},
        {"owner": "different-owner"},
        {"state_generation": "wrong-state"},
        {"predecessor": {"key": "x/completed.json", "version": "other", "claim_version": "v"}},
    ],
)
def test_generation_and_immutable_history_changes_rejected(changes: dict[str, Any]) -> None:
    rows = history()
    rows[2] = mutate(rows[2], **changes)
    with pytest.raises(MetricsError):
        measure(rows)


@pytest.mark.parametrize("outcome", ["failed", "unknown", "unrecognized", None])
def test_failed_unknown_or_missing_result_rejected(outcome: Any) -> None:
    rows = history()
    for index in range(2, len(rows)):
        body = json.loads(rows[index].data)
        body["body"]["receipts"][0]["outcome"] = outcome
        rows[index] = replace(rows[index], data=json.dumps(body).encode())
    with pytest.raises(MetricsError):
        measure(rows)


def test_unknown_phase_rejected() -> None:
    rows = history()
    body = json.loads(rows[1].data)
    body["body"]["receipts"][0]["phase"] = SECRET
    rows[1] = replace(rows[1], data=json.dumps(body).encode())
    with pytest.raises(MetricsError) as error:
        measure(rows)
    assert SECRET not in str(error.value)


@pytest.mark.parametrize("field_name", ["phase", "state_generation"])
def test_result_must_match_exact_intent_receipt(field_name: str) -> None:
    rows = history()
    body = json.loads(rows[2].data)
    body["body"]["receipts"][0][field_name] = "update" if field_name == "phase" else "other-state"
    rows[2] = replace(rows[2], data=json.dumps(body).encode())
    with pytest.raises(MetricsError):
        measure(rows)


@pytest.mark.parametrize("field_name", ["run_prefix", "revision"])
def test_exact_selected_identity_required(field_name: str) -> None:
    rows = history()
    options = {"run_prefix": RUN, "revision": REVISION, "now": NOW}
    options[field_name] = "gha-1794643200-124-1" if field_name == "run_prefix" else "c" * 40
    with pytest.raises(MetricsError):
        measure_phases(rows, **options)  # type: ignore[arg-type]


@pytest.mark.parametrize("version", ["", "null\x00", "a" * 1025, None, 5, SECRET + "\n"])
def test_invalid_opaque_version_rejected(version: Any) -> None:
    rows = history()
    rows[0] = replace(rows[0], version=version)
    with pytest.raises(MetricsError):
        measure(rows)


@pytest.mark.parametrize("conflict", ["body", "timestamp", "generation"])
def test_duplicate_conflicting_version_rejected(conflict: str) -> None:
    rows = history()
    if conflict == "body":
        duplicate = mutate(rows[0], owner="another-owner")
    elif conflict == "timestamp":
        duplicate = replace(rows[0], last_modified=BASE + timedelta(seconds=1))
    else:
        duplicate = replace(rows[1], version=rows[0].version)
    rows.append(duplicate)
    with pytest.raises(MetricsError):
        measure(rows)


def test_conflicting_same_generation_rejected() -> None:
    rows = history()
    rows.append(replace(mutate(rows[0], owner="another-owner"), version="different-version"))
    with pytest.raises(MetricsError):
        measure(rows)


@pytest.mark.parametrize(
    "field_name,value",
    [("claim_version", "unobserved-version"), ("key", "canary/runs/other/completed.json")],
)
def test_completed_marker_must_match_history(field_name: str, value: str) -> None:
    rows = history()
    body = json.loads(rows[-1].data)
    body["body"]["completed"][field_name] = value
    rows[-1] = replace(rows[-1], data=json.dumps(body).encode())
    with pytest.raises(MetricsError):
        measure(rows)


def test_observation_bound_includes_duplicates() -> None:
    rows = history()
    assert measure(rows + [rows[0]] * (256 - len(rows))) == measure(rows)
    with pytest.raises(MetricsError):
        measure(rows + [rows[0]] * (257 - len(rows)))
    with pytest.raises(MetricsError):
        measure([])


@pytest.mark.parametrize(
    "data",
    [
        SECRET.encode(),
        b"\xff" + SECRET.encode(),
        ('{"schema":1,"schema":1,"secret":"' + SECRET + '"}').encode(),
        json.dumps({"schema": 2, "kind": "ledger", "body": SECRET}).encode(),
        b"x" * 262145,
    ],
)
def test_malformed_bytes_never_echoed(data: bytes) -> None:
    row = LedgerVersionObservation(data, SECRET, SECRET)
    assert SECRET not in repr(row)
    rows = history()
    rows[0] = replace(row, last_modified=BASE)
    with pytest.raises(MetricsError) as error:
        measure(rows)
    assert SECRET not in str(error.value)
    assert SECRET not in repr(error.value)
    assert SECRET not in "".join(traceback.format_exception(error.value))
    assert error.value.__suppress_context__


def test_no_private_fields_in_reports_or_repr() -> None:
    rows = history()
    rows = [replace(mutate(row, owner=SECRET), version=SECRET + row.version) for row in rows]
    final = decode_ledger(rows[-1].data)
    assert final.completed is not None
    rows[-1] = replace(
        rows[-1],
        data=encode_ledger(
            replace(
                final,
                completed=replace(
                    final.completed,
                    claim_version=rows[-2].version,
                ),
            )
        ),
    )
    output = measure(rows)
    assert SECRET not in repr(output)
    assert SECRET not in repr([asdict(item) for item in output])
    assert SECRET not in repr(rows)


def test_non_observation_input_is_sanitized() -> None:
    with pytest.raises(MetricsError):
        measure(cast(Any, [{"Body": SECRET}]))


def test_recovery_completion_is_not_a_successful_original_run() -> None:
    rows = history(("destroy", "absence"))
    recovered = []
    for index, row in enumerate(rows):
        body = json.loads(row.data)
        body["body"]["recovery"] = {
            "key": f"canary/runs/{RUN}/recovery.json",
            "version": "snapshot-version",
            "claim_version": "unresolved-version",
            "generation": 1,
        }
        body["body"]["generation"] += 2
        observation = replace(row, data=json.dumps(body).encode())
        # Each ledger is valid in isolation; metrics must still reject recovery.
        assert decode_ledger(observation.data).generation == index + 2
        recovered.append(observation)
    with pytest.raises(MetricsError):
        measure(recovered)


@pytest.mark.parametrize("index", range(8))
def test_strict_decode_required_for_every_version(index: int) -> None:
    rows = history()
    body = json.loads(rows[index].data)
    body["body"]["unexpected-private-metadata"] = SECRET
    rows[index] = replace(rows[index], data=json.dumps(body).encode())
    with pytest.raises(MetricsError) as error:
        measure(rows)
    assert SECRET not in str(error.value)


def test_immutable_run_details_cannot_change_mid_history() -> None:
    rows = history()
    body = json.loads(rows[2].data)
    body["body"]["run"]["zone_id"] = "c" * 32
    rows[2] = replace(rows[2], data=json.dumps(body).encode())
    assert decode_ledger(rows[2].data).run.zone_id == "c" * 32
    with pytest.raises(MetricsError):
        measure(rows)


def test_rewritten_old_receipt_rejected_even_if_latest_receipt_matches() -> None:
    rows = history()
    body = json.loads(rows[4].data)
    body["body"]["receipts"][0]["phase"] = "update"
    rows[4] = replace(rows[4], data=json.dumps(body).encode())
    assert decode_ledger(rows[4].data).receipts[0].phase == "update"
    with pytest.raises(MetricsError):
        measure(rows)
