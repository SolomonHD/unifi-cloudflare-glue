"""Read-only protected receipt intervals, not isolated DNS propagation latency.

The caller supplies historical maintenance-object versions for one selected run.
Bytes are decoded only in memory; no transport, credential or state access occurs.
LastModified is an observation of a protected write, not a provider event clock.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Literal

from .canary_identity import validate_run_prefix
from .canary_store import Ledger, Phase, decode_ledger

_INTERVAL_SCOPE = "includes protected I/O and verification; not provider-only latency"
_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])"
)


class MetricsError(RuntimeError):
    """Sanitized invalid or insufficient observation evidence."""


@dataclass(frozen=True)
class LedgerVersionObservation:
    data: bytes = field(repr=False)
    version: str = field(repr=False)
    last_modified: datetime | str = field(repr=False)


@dataclass(frozen=True)
class PhaseTiming:
    phase: Phase
    start: datetime
    end: datetime
    approximate_interval_seconds: float
    interval_scope: str = field(default=_INTERVAL_SCOPE, init=False)
    timestamp_resolution_seconds: Literal[1] = field(default=1, init=False)


def _utc(value: datetime | str) -> datetime:
    if type(value) is str:
        if _TIMESTAMP.fullmatch(value) is None:
            raise ValueError
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError
    return value.astimezone(timezone.utc)


def measure_phases(
    observations: Sequence[LedgerVersionObservation],
    *,
    run_prefix: str,
    revision: str,
    now: datetime,
) -> tuple[PhaseTiming, ...]:
    """Require complete, consistent version evidence of a successful completed run.

    Input order is immaterial: opaque versions are never sorted or interpreted.
    Generations establish protocol order; UTC LastModified must not go backwards
    in that order. Equal timestamps are valid at the source's one-second resolution.
    Exact repeated observations are harmless; conflicting copies fail closed.
    All supplied versions must belong to the exact requested run and revision.
    """
    try:
        validate_run_prefix(run_prefix)
        if type(revision) is not str or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            raise ValueError
        observed_now = _utc(now)
        if not 1 <= len(observations) <= 256:
            raise ValueError
        versions: dict[str, tuple[bytes, datetime]] = {}
        generations: dict[int, tuple[Ledger, datetime, datetime, set[str]]] = {}
        for observation in observations:
            if type(observation) is not LedgerVersionObservation:
                raise ValueError
            version = observation.version
            if (
                type(version) is not str
                or not 0 < len(version) <= 1024
                or not all(32 <= ord(char) <= 126 for char in version)
            ):
                raise ValueError
            timestamp = _utc(observation.last_modified)
            if timestamp > observed_now:
                raise ValueError
            # Decode even repeated observations; never trust an upstream decode.
            ledger = decode_ledger(observation.data)
            if (
                ledger.run.run_prefix != run_prefix
                or ledger.run.revision != revision
                or ledger.recovery is not None
                or any(receipt.outcome not in (None, "succeeded") for receipt in ledger.receipts)
            ):
                raise ValueError
            identity = (observation.data, timestamp)
            if version in versions and versions[version] != identity:
                raise ValueError
            versions[version] = identity
            previous = generations.get(ledger.generation)
            if previous is None:
                generations[ledger.generation] = (ledger, timestamp, timestamp, {version})
            else:
                prior_ledger, first, last, tokens = previous
                if prior_ledger != ledger:
                    raise ValueError
                generations[ledger.generation] = (
                    ledger,
                    min(first, timestamp),
                    max(last, timestamp),
                    tokens | {version},
                )
        ordered = [generations[index] for index in range(len(generations))]
        initial = ordered[0][0]
        final = ordered[-1][0]
        if initial.generation != 0 or initial.receipts or initial.completed is not None:
            raise ValueError
        if final.completed is None or not final.receipts:
            raise ValueError
        if not final.completed.key.endswith("/runs/" + run_prefix + "/completed.json"):
            raise ValueError
        intervals: list[PhaseTiming] = []
        pending_start: datetime | None = None
        for previous, current in zip(ordered, ordered[1:]):
            old, _, old_last, old_versions = previous
            ledger, first, _, _ = current
            if first < old_last or old.completed is not None:
                raise ValueError
            if ledger.completed is not None:
                if (
                    ledger.completed.claim_version not in old_versions
                    or ledger
                    != replace(old, generation=old.generation + 1, completed=ledger.completed)
                    or pending_start is not None
                ):
                    raise ValueError
            elif old.receipts and old.receipts[-1].outcome is None:
                receipt = ledger.receipts[-1]
                if receipt.outcome != "succeeded" or receipt.resulting_state_generation is None:
                    raise ValueError
                expected = replace(
                    old,
                    generation=old.generation + 1,
                    state_generation=receipt.resulting_state_generation,
                    receipts=(
                        *old.receipts[:-1],
                        replace(
                            old.receipts[-1],
                            outcome="succeeded",
                            resulting_state_generation=receipt.resulting_state_generation,
                        ),
                    ),
                )
                if ledger != expected or pending_start is None:
                    raise ValueError
                intervals.append(
                    PhaseTiming(
                        receipt.phase,
                        pending_start,
                        first,
                        (first - pending_start).total_seconds(),
                    )
                )
                pending_start = None
            else:
                if (
                    len(ledger.receipts) != len(old.receipts) + 1
                    or ledger.receipts[-1].outcome is not None
                    or ledger.receipts[-1].state_generation != old.state_generation
                    or ledger
                    != replace(
                        old,
                        generation=old.generation + 1,
                        receipts=(*old.receipts, ledger.receipts[-1]),
                    )
                    or pending_start is not None
                ):
                    raise ValueError
                pending_start = first
        if pending_start is not None or len(intervals) != len(final.receipts):
            raise ValueError
        return tuple(intervals)
    except Exception:
        raise MetricsError("Invalid or insufficient protected phase timing observations") from None
