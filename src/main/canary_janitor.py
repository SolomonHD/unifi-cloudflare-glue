"""Bounded, dependency-injected janitor inventory, with no deletion capability.

Adapters must supply normalized non-secret record metadata and protected evidence.
This module does not fetch credentials, contact providers, transfer ownership, or
repair state. Even a fully corroborated candidate needs explicit full-fixture
reconciliation through the separately qualified recovery path.
"""

import re
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Literal

from .canary_identity import RESOURCE_TYPE, ZONE_NAME, record_name, validate_canary_record
from .canary_store import (
    RunIdentity,
    StoredLedger,
    decode_ledger,
    encode_ledger,
)

_ID = re.compile(r"[0-9a-f]{32}")
_NAME = re.compile(r"(gha-[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*)\.(txt|cname)\.ci\.solomonhd\.ai")
_DATE = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


class JanitorError(ValueError):
    """Fixed, non-secret configuration diagnostic."""


@dataclass(frozen=True, repr=False)
class RecordCandidate:
    zone_id: str
    zone_name: str
    record_id: str
    name: str
    record_type: str
    proxied: bool
    created_on: str


@dataclass(frozen=True, repr=False)
class RecordIdentity:
    record_id: str
    name: str
    record_type: str


@dataclass(frozen=True, repr=False)
class ProtectedEvidence:
    run: RunIdentity
    claim: StoredLedger
    expected_claim_version: str
    expected_generation: int
    state_version: str | None
    expected_state_version: str | None
    state_records: tuple[RecordIdentity, ...]
    metadata_records: tuple[RecordIdentity, ...]
    writer_status: Literal["unknown", "active", "terminated_known"] = "unknown"
    owned: bool = False
    state_complete: bool = False

    def __post_init__(self) -> None:
        # Freeze caller-owned collections; reject unbounded iterators before reading.
        for key in ("state_records", "metadata_records"):
            values = getattr(self, key)
            if type(values) not in (list, tuple) or len(values) > 2:
                raise JanitorError("Invalid protected evidence")
            object.__setattr__(self, key, tuple(values))


@dataclass(frozen=True)
class ReportRow:
    run_prefix: str
    name: str
    record_id: str
    record_type: str
    age_seconds: int | None
    reason: str


@dataclass(frozen=True)
class JanitorReport:
    rows: tuple[ReportRow, ...]
    errors: tuple[str, ...]
    scanned: int
    excluded: int
    stale_threshold_seconds: int

    def to_dict(self) -> dict:
        return {
            "operation": "janitor_inventory",
            "report_only": True,
            "rows": [asdict(row) for row in self.rows],
            "errors": list(self.errors),
            "scanned": self.scanned,
            "excluded": self.excluded,
            "stale_threshold_seconds": self.stale_threshold_seconds,
        }


def _identity(record: RecordIdentity, prefix: str, zone_id: str) -> RecordIdentity:
    if type(record) is not RecordIdentity or type(record.record_id) is not str:
        raise JanitorError("Invalid protected evidence")
    if _ID.fullmatch(record.record_id) is None:
        raise JanitorError("Invalid protected evidence")
    validate_canary_record(
        run_prefix=prefix,
        name=record.name,
        zone_name=ZONE_NAME,
        zone_id=zone_id,
        expected_zone_id=zone_id,
        record_type=record.record_type,
        proxied=False,
        resource_type=RESOURCE_TYPE,
    )
    return RecordIdentity(record.record_id, record.name, record.record_type)


def _classify(evidence: ProtectedEvidence | None, record: RecordCandidate, prefix: str) -> str:
    if evidence is None:
        return "unowned"
    if type(evidence) is not ProtectedEvidence:
        return "invalid_evidence"
    if evidence.owned is not True:
        return "unowned"
    if evidence.writer_status == "active":
        return "active"
    if evidence.writer_status != "terminated_known":
        return "unknown_writer"
    try:
        # Round-trip the strict store schema to detach all nested input objects.
        claim = evidence.claim
        if type(claim) is not StoredLedger or type(claim.version) is not str:
            return "invalid_evidence"
        ledger = decode_ledger(encode_ledger(claim.ledger))
        evidence.run.validate()
        if (
            ledger.run != evidence.run
            or ledger.run.run_prefix != prefix
            or ledger.run.zone_id != record.zone_id
            or ledger.run.zone_name != record.zone_name
        ):
            return "identity_mismatch"
        if (
            not claim.version
            or claim.version != evidence.expected_claim_version
            or type(evidence.expected_generation) is not int
            or ledger.generation != evidence.expected_generation
        ):
            return "stale_claim_generation"
        if evidence.state_complete is not True or evidence.state_version is None:
            return "missing_or_partial_state"
        if (
            type(evidence.state_version) is not str
            or not evidence.state_version
            or evidence.state_version != evidence.expected_state_version
            or ledger.state_generation != evidence.state_version
        ):
            return "stale_state_generation"
        state = tuple(_identity(item, prefix, record.zone_id) for item in evidence.state_records)
        metadata = tuple(
            _identity(item, prefix, record.zone_id) for item in evidence.metadata_records
        )
        intended = {(record_name(prefix, "txt"), "TXT"), (record_name(prefix, "cname"), "CNAME")}
        if len(state) != 2 or {(item.name, item.record_type) for item in state} != intended:
            return "missing_or_partial_state"
        if (
            len({item.record_id for item in state}) != 2
            or set(state) != set(metadata)
            or RecordIdentity(record.record_id, record.name, record.record_type) not in state
        ):
            return "record_identity_mismatch"
        if any(receipt.outcome not in ("failed", "succeeded") for receipt in ledger.receipts):
            return "unknown_outcome"
        if ledger.completed is not None:
            return "completed_claim_conflict"
        if not any(
            receipt.phase in ("destroy", "absence") and receipt.outcome == "failed"
            for receipt in ledger.receipts
        ):
            return "cleanup_failure_not_established"
        return "requires_explicit_reconciliation"
    except Exception:
        return "invalid_evidence"


def inventory(
    *,
    zone_id: str,
    zone_name: str,
    read_candidates: Callable[[int], list[RecordCandidate] | tuple[RecordCandidate, ...]],
    read_evidence: Callable[[str], ProtectedEvidence | None],
    now: datetime,
    record_limit: int = 200,
    job_timeout_seconds: int = 1800,
    buffer_seconds: int = 300,
) -> JanitorReport:
    """Report bounded normalized input; injected reads are the only operations.

    The candidate adapter must itself bound provider paging and response bytes.
    Only concrete lists/tuples of at most record_limit are accepted, never lazy
    iterators. Overflow discards the entire batch, not an arbitrary first slice.
    Invalid/unrelated identities are counted without echoing their names or IDs.
    """
    if (
        type(zone_id) is not str
        or _ID.fullmatch(zone_id) is None
        or zone_name != ZONE_NAME
        or type(record_limit) is not int
        or not 1 <= record_limit <= 200
        or type(job_timeout_seconds) is not int
        or not 1800 <= job_timeout_seconds <= 86400
        or type(buffer_seconds) is not int
        or not 300 <= buffer_seconds <= 86400
        or type(now) is not datetime
        or now.tzinfo is None
        or now.utcoffset() is None
    ):
        raise JanitorError("Invalid janitor inventory configuration")
    threshold = job_timeout_seconds + buffer_seconds
    current = now.astimezone(timezone.utc).timestamp()
    rows: list[ReportRow] = []
    errors: list[str] = []
    excluded = 0
    try:
        batch = read_candidates(record_limit)
        if type(batch) not in (list, tuple) or len(batch) > record_limit:
            return JanitorReport((), ("inventory_limit_or_shape",), 0, 0, threshold)
        # Snapshot and validate the WHOLE batch before invoking any evidence reader.
        scanned = len(batch)
        frozen: list[tuple[RecordCandidate, str]] = []
        for item in tuple(batch):
            if type(item) is not RecordCandidate:
                excluded += 1
                continue
            if not all(
                type(value) is str
                for value in (
                    item.zone_id,
                    item.zone_name,
                    item.record_id,
                    item.name,
                    item.record_type,
                )
            ):
                excluded += 1
                continue
            match = _NAME.fullmatch(item.name) if len(item.name) <= 253 else None
            if match is None or _ID.fullmatch(item.record_id) is None:
                excluded += 1
                continue
            prefix = match[1]
            try:
                validate_canary_record(
                    run_prefix=prefix,
                    name=item.name,
                    zone_name=item.zone_name,
                    zone_id=item.zone_id,
                    expected_zone_id=zone_id,
                    record_type=item.record_type,
                    proxied=item.proxied,
                    resource_type=RESOURCE_TYPE,
                )
            except Exception:
                excluded += 1
                continue
            frozen.append(
                (
                    RecordCandidate(
                        *(
                            item.zone_id,
                            item.zone_name,
                            item.record_id,
                            item.name,
                            item.record_type,
                            item.proxied,
                            item.created_on if type(item.created_on) is str else "",
                        )
                    ),
                    prefix,
                )
            )
        if len({item.record_id for item, _ in frozen}) != len(frozen) or len(
            {item.name for item, _ in frozen}
        ) != len(frozen):
            return JanitorReport((), ("duplicate_record_identity",), scanned, excluded, threshold)
    except Exception:
        return JanitorReport((), ("inventory_read_failed",), 0, 0, threshold)

    evidence_cache: dict[str, ProtectedEvidence | None] = {}
    failed_reads: set[str] = set()
    for record, prefix in frozen:
        age = None
        reason = "invalid_timestamp"
        try:
            if len(record.created_on) > 64 or _DATE.fullmatch(record.created_on) is None:
                raise ValueError
            created = datetime.fromisoformat(record.created_on.replace("Z", "+00:00")).timestamp()
            named = int(prefix.split("-")[1])
            # Both independent clocks must corroborate staleness; neither is authority.
            if named > current or created > current:
                reason = "future_timestamp"
            elif current - named < threshold or current - created < threshold:
                excluded += 1
                continue
            else:
                age = int(min(current - named, current - created))
                reason = "stale"
        except Exception:
            pass
        if reason == "stale":
            try:
                if prefix not in evidence_cache and prefix not in failed_reads:
                    evidence_cache[prefix] = deepcopy(read_evidence(prefix))
                if prefix in failed_reads:
                    raise JanitorError("Protected evidence unavailable")
                reason = _classify(evidence_cache[prefix], record, prefix)
            except Exception:
                failed_reads.add(prefix)
                reason = "evidence_read_failed"
                if "evidence_read_failed" not in errors:
                    errors.append("evidence_read_failed")
            if reason == "invalid_evidence" and "selection_failed" not in errors:
                errors.append("selection_failed")
        rows.append(
            ReportRow(prefix, record.name, record.record_id, record.record_type, age, reason)
        )
    return JanitorReport(tuple(rows), tuple(errors), scanned, excluded, threshold)
