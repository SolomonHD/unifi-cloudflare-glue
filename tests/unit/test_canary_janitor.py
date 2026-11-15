"""Synthetic-only report classification, bounding, and disclosure tests."""

import importlib.util
import json
import sys
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_janitor_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_janitor_test_package import canary_janitor as janitor
from canary_janitor_test_package.canary_identity import record_name
from canary_janitor_test_package.canary_store import Ledger, Receipt, RunIdentity, StoredLedger

ZONE = "a" * 32
RUN = "gha-1794700000-123-1"
NOW = datetime.fromtimestamp(1794700000 + 3600, timezone.utc)
CREATED = datetime.fromtimestamp(1794700000, timezone.utc).isoformat()
SECRET = "synthetic-secret-provider-body-DO-NOT-PRINT"


def candidate(label="txt", **changes):
    return replace(
        janitor.RecordCandidate(
            ZONE,
            "solomonhd.ai",
            ("b" if label == "txt" else "c") * 32,
            record_name(RUN, label),
            label.upper(),
            False,
            CREATED,
        ),
        **changes,
    )


def evidence(**changes):
    run = RunIdentity(
        RUN,
        "d" * 40,
        ZONE,
        "solomonhd.ai",
        ((record_name(RUN, "txt"), "TXT"), (record_name(RUN, "cname"), "CNAME")),
    )
    ledger = Ledger(
        run, "private-owner", 2, "state-v1", (Receipt("destroy", "state-v0", "failed", "state-v1"),)
    )
    records = tuple(
        janitor.RecordIdentity(item.record_id, item.name, item.record_type)
        for item in (candidate(), candidate("cname"))
    )
    return replace(
        janitor.ProtectedEvidence(
            run,
            StoredLedger(ledger, "claim-v1"),
            "claim-v1",
            2,
            "state-v1",
            "state-v1",
            records,
            records,
            "terminated_known",
            True,
            True,
        ),
        **changes,
    )


def report(records=None, protected=None, **options):
    return janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=Mock(return_value=[candidate()] if records is None else records),
        read_evidence=Mock(return_value=evidence() if protected is None else protected),
        **options,
    )


def reason(protected):
    return report(protected=protected).rows[0].reason


def test_exact_complete_failed_cleanup_is_reconciliation_only(capsys):
    result = report([candidate(), candidate("cname")])
    assert {row.reason for row in result.rows} == {"requires_explicit_reconciliation"}
    assert result.stale_threshold_seconds == 2100
    assert all(row.age_seconds == 3600 for row in result.rows)
    output = result.to_dict()
    assert output["report_only"] is True
    assert set(output["rows"][0]) == {
        "run_prefix",
        "name",
        "record_id",
        "record_type",
        "age_seconds",
        "reason",
    }
    assert "delet" not in json.dumps(output)
    assert "private-owner" not in json.dumps(output)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "changes",
    [
        {"name": "outside-" + SECRET},
        {"name": record_name(RUN, "txt") + ".evil"},
        {"name": record_name(RUN, "txt").upper()},
        {"name": record_name(RUN, "txt") + "."},
        {"name": "gha-01-123-1.txt.ci.solomonhd.ai"},
        {"name": "gha-" + "1" * 60 + "-123-1.txt.ci.solomonhd.ai"},
        {"record_id": SECRET},
        {"record_id": "B" * 32},
        {"record_type": "A"},
        {"record_type": "CNAME"},
        {"record_type": "txt"},
        {"proxied": True},
        {"proxied": 0},
        {"proxied": None},
        {"zone_id": "f" * 32},
        {"zone_name": SECRET},
    ],
)
def test_excluded_identity_never_echoed_or_evidence_read(changes):
    reader = Mock(side_effect=AssertionError("must not read"))
    result = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=lambda limit: [candidate(**changes)],
        read_evidence=reader,
    )
    assert result.rows == ()
    assert result.excluded == 1
    assert SECRET not in repr(result) + json.dumps(result.to_dict())
    reader.assert_not_called()


@pytest.mark.parametrize(
    "created,expected",
    [
        ("2026-99-15T12:00:00Z", "invalid_timestamp"),
        ("2026-11-15T12:00:00", "invalid_timestamp"),
        (SECRET, "invalid_timestamp"),
        ("", "invalid_timestamp"),
        (None, "invalid_timestamp"),
        ((NOW.replace(year=2027)).isoformat(), "future_timestamp"),
    ],
)
def test_api_date_must_be_valid_and_not_future(created, expected):
    result = report([candidate(created_on=created)])
    assert result.rows[0].reason == expected
    assert result.rows[0].age_seconds is None
    assert SECRET not in json.dumps(result.to_dict())


@pytest.mark.parametrize("offset,rows", [(2099, 0), (2100, 1), (2101, 1)])
def test_both_timestamps_must_meet_threshold_inclusive(offset, rows):
    current = datetime.fromtimestamp(1794700000 + offset, timezone.utc)
    result = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=current,
        read_candidates=lambda limit: [candidate()],
        read_evidence=lambda prefix: evidence(),
    )
    assert len(result.rows) == rows


def test_newer_api_timestamp_excluded_even_with_old_name():
    created = datetime.fromtimestamp(NOW.timestamp() - 2099, timezone.utc).isoformat()
    assert report([candidate(created_on=created)]).rows == ()


def test_newer_and_future_name_not_selected_using_old_api_date():
    for unix, expected in (
        (int(NOW.timestamp()) - 100, None),
        (int(NOW.timestamp()) + 1, "future_timestamp"),
    ):
        name = f"gha-{unix}-123-1.txt.ci.solomonhd.ai"
        result = report([candidate(name=name)])
        assert (result.rows[0].reason if result.rows else None) == expected


@pytest.mark.parametrize(
    "changes,expected",
    [
        ({"owned": False}, "unowned"),
        ({"owned": 1}, "unowned"),
        ({"writer_status": "active"}, "active"),
        ({"writer_status": "unknown"}, "unknown_writer"),
        ({"writer_status": SECRET}, "unknown_writer"),
        ({"state_complete": False}, "missing_or_partial_state"),
        ({"state_version": None}, "missing_or_partial_state"),
        ({"state_records": ()}, "missing_or_partial_state"),
        ({"expected_generation": 3}, "stale_claim_generation"),
        ({"expected_generation": True}, "stale_claim_generation"),
        ({"expected_claim_version": "other"}, "stale_claim_generation"),
        ({"state_version": "other"}, "stale_state_generation"),
        ({"expected_state_version": "other"}, "stale_state_generation"),
        ({"metadata_records": ()}, "record_identity_mismatch"),
    ],
)
def test_protected_exclusions(changes, expected):
    assert reason(evidence(**changes)) == expected


def test_missing_evidence_and_unknown_receipt_fail_closed():
    result = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=lambda limit: [candidate()],
        read_evidence=lambda prefix: None,
    )
    assert result.rows[0].reason == "unowned"
    original = evidence()
    unknown = replace(
        original.claim.ledger, receipts=(Receipt("destroy", "state-v0", "unknown", "state-v1"),)
    )
    assert reason(replace(original, claim=StoredLedger(unknown, "claim-v1"))) == "unknown_outcome"
    pending = replace(unknown, generation=1, receipts=(Receipt("destroy", "state-v1"),))
    assert (
        reason(replace(original, claim=StoredLedger(pending, "claim-v1"), expected_generation=1))
        == "unknown_outcome"
    )


def test_wrong_run_zone_revision_record_and_partial_state():
    original = evidence()
    assert (
        reason(replace(original, run=replace(original.run, revision="e" * 40)))
        == "identity_mismatch"
    )
    ledger = replace(original.claim.ledger, run=replace(original.run, zone_id="f" * 32))
    assert (
        reason(replace(original, run=ledger.run, claim=StoredLedger(ledger, "claim-v1")))
        == "identity_mismatch"
    )
    assert (
        reason(replace(original, state_records=original.state_records[:1]))
        == "missing_or_partial_state"
    )
    different = replace(original.state_records[0], record_id="e" * 32)
    assert (
        reason(replace(original, metadata_records=(different, original.state_records[1])))
        == "record_identity_mismatch"
    )
    assert report([candidate(record_id="e" * 32)]).rows[0].reason == "record_identity_mismatch"
    invalid = replace(original.state_records[0], name=SECRET)
    assert reason(replace(original, metadata_records=(invalid,))) == "invalid_evidence"


def test_age_does_not_establish_failed_cleanup():
    original = evidence()
    ledger = replace(
        original.claim.ledger, receipts=(Receipt("create", "state-v0", "failed", "state-v1"),)
    )
    assert (
        reason(replace(original, claim=StoredLedger(ledger, "claim-v1")))
        == "cleanup_failure_not_established"
    )


@pytest.mark.parametrize(
    "options",
    [
        {"record_limit": 0},
        {"record_limit": 201},
        {"record_limit": True},
        {"job_timeout_seconds": 1799},
        {"buffer_seconds": 299},
        {"buffer_seconds": 86401},
        {"job_timeout_seconds": 86401},
    ],
)
def test_invalid_limits_rejected_before_inventory(options):
    reader = Mock()
    with pytest.raises(janitor.JanitorError, match="Invalid janitor inventory configuration"):
        janitor.inventory(
            zone_id=ZONE,
            zone_name="solomonhd.ai",
            now=NOW,
            read_candidates=reader,
            read_evidence=reader,
            **options,
        )
    reader.assert_not_called()


@pytest.mark.parametrize(
    "zone_id,zone_name,now",
    [
        (SECRET, "solomonhd.ai", NOW),
        (ZONE, SECRET, NOW),
        (ZONE, "solomonhd.ai", NOW.replace(tzinfo=None)),
    ],
)
def test_bad_configuration_never_echoes_inputs(zone_id, zone_name, now):
    with pytest.raises(janitor.JanitorError) as caught:
        janitor.inventory(
            zone_id=zone_id,
            zone_name=zone_name,
            now=now,
            read_candidates=Mock(),
            read_evidence=Mock(),
        )
    assert SECRET not in str(caught.value)


@pytest.mark.parametrize("batch", [[candidate()] * 201, {SECRET: SECRET}, iter([candidate()])])
def test_unbounded_or_oversized_batches_discarded(batch):
    result = report(records=batch)
    assert result.rows == ()
    assert result.errors == ("inventory_limit_or_shape",)


def test_duplicate_names_and_ids_fail_closed():
    assert report([candidate(), candidate()]).errors == ("duplicate_record_identity",)
    assert report([candidate(), candidate("cname", record_id="b" * 32)]).rows == ()


def test_read_and_selection_errors_are_aggregated_without_provider_body(capsys):
    def fail(*args):
        raise RuntimeError(SECRET)

    result = janitor.inventory(
        zone_id=ZONE, zone_name="solomonhd.ai", now=NOW, read_candidates=fail, read_evidence=fail
    )
    assert result.errors == ("inventory_read_failed",)
    result2 = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=lambda limit: [candidate(), candidate("cname")],
        read_evidence=fail,
    )
    assert result2.errors == ("evidence_read_failed",)
    assert {row.reason for row in result2.rows} == {"evidence_read_failed"}
    bad = report(protected=SECRET)
    assert bad.errors == ("selection_failed",)
    assert SECRET not in repr(result) + repr(result2) + repr(bad) + json.dumps(result2.to_dict())
    assert capsys.readouterr() == ("", "")


def test_mutable_inputs_are_frozen_and_evidence_read_once_per_run():
    batch = [candidate(), candidate("cname")]
    protected = evidence()

    def read(prefix):
        batch.clear()
        return protected

    reader = Mock(side_effect=read)
    result = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=lambda limit: batch,
        read_evidence=reader,
    )
    assert len(result.rows) == 2
    reader.assert_called_once_with(RUN)
    output = result.to_dict()
    output["rows"][0]["reason"] = SECRET
    assert SECRET not in json.dumps(result.to_dict())
    with pytest.raises(FrozenInstanceError):
        result.rows[0].reason = SECRET
    source = list(protected.state_records)
    frozen = replace(protected, state_records=source)
    source.clear()
    assert len(frozen.state_records) == 2


def test_no_deletion_mode_exists():
    with pytest.raises(TypeError):
        report(delete=True)
    assert not hasattr(janitor, "delete")


@pytest.mark.parametrize(
    "created",
    [
        "2026-11-15T12:00:00+00:99",
        "2026-11-15T12:00:60Z",
        "2026-11-15T24:00:00Z",
        "2026-11-15T12:00:00Z\n",
    ],
)
def test_noncanonical_api_dates_fail_closed(created):
    assert report([candidate(created_on=created)]).rows[0].reason == "invalid_timestamp"


def test_normal_reports_never_include_protected_values(capsys):
    original = evidence()
    ledger = replace(
        original.claim.ledger,
        owner=SECRET,
        state_generation=SECRET,
        receipts=(Receipt("destroy", SECRET, "failed", SECRET),),
    )
    protected = replace(
        original,
        claim=StoredLedger(ledger, SECRET),
        expected_claim_version=SECRET,
        state_version=SECRET,
        expected_state_version=SECRET,
    )
    result = report(protected=protected)
    assert result.rows[0].reason == "requires_explicit_reconciliation"
    assert SECRET not in json.dumps(result.to_dict()) + repr(result) + capsys.readouterr().out


def test_candidate_snapshot_precedes_callbacks_even_for_forced_object_mutation():
    txt, cname = candidate(), candidate("cname")

    def read(prefix):
        object.__setattr__(cname, "name", SECRET)
        object.__setattr__(cname, "record_id", SECRET)
        return evidence()

    result = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=lambda limit: [txt, cname],
        read_evidence=read,
    )
    assert len(result.rows) == 2
    assert result.rows[1].name == record_name(RUN, "cname")
    assert SECRET not in json.dumps(result.to_dict())


def test_maximum_inventory_is_bounded_and_read_limit_forwarded():
    batch = [
        candidate(
            name=f"gha-1794700000-{index + 1}-1.txt.ci.solomonhd.ai", record_id=f"{index:032x}"
        )
        for index in range(200)
    ]
    reader = Mock(return_value=batch)
    result = janitor.inventory(
        zone_id=ZONE,
        zone_name="solomonhd.ai",
        now=NOW,
        read_candidates=reader,
        read_evidence=lambda prefix: None,
    )
    reader.assert_called_once_with(200)
    assert result.scanned == len(result.rows) == 200


def test_evidence_collections_cannot_be_unbounded():
    original = evidence()
    with pytest.raises(janitor.JanitorError):
        replace(original, state_records=iter(original.state_records))
    with pytest.raises(janitor.JanitorError):
        replace(original, metadata_records=original.metadata_records * 2)
