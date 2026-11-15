"""Offline-testable canary orchestration; adapters own qualified runtime I/O.

No transport or in-memory backend is selected by this module. An adapter must
preserve partial state and distinguish a completed failure from an unknown
effect before this lifecycle can safely attempt cleanup.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from .canary_identity import validate_run_prefix

Outcome = Literal["verified", "failed", "unknown", "not_attempted"]


class CompletedFailure(Exception):
    """The adapter observed command termination, including any partial effects."""


class Journal(Protocol):
    def prepare(self) -> None:
        """Qualify backend/exclusion and persist exact run identity before I/O."""

    def assert_owned(self) -> None: ...

    def intent(self, phase: str) -> None: ...

    def result(self, phase: str, outcome: Outcome) -> None: ...

    def complete(self) -> None:
        """Commit verified state/API absence before releasing known ownership."""


class Driver(Protocol):
    def initialize(self) -> None: ...

    def apply(self, revision: Literal["create", "update"]) -> None: ...

    def verify_api(self, revision: Literal["create", "update"]) -> None: ...

    def verify_dns(self, revision: Literal["create", "update"]) -> None: ...

    def drift(self) -> bool:
        """Return whether a completed, valid detailed-exitcode plan has changes."""

    def has_state(self) -> bool: ...

    def destroy(self) -> None: ...

    def verify_absence(self) -> None:
        """Require exact-name API absence and authoritative empty state."""


@dataclass(frozen=True)
class Report:
    run_prefix: str
    phase: str
    primary: Outcome
    cleanup: Outcome

    @property
    def succeeded(self) -> bool:
        return self.primary == self.cleanup == "verified"


def run_canary(run_prefix: str, journal: Journal, driver: Driver) -> Report:
    """Create/update/plan/destroy without replaying unknown effects.

    All phase strings are internal constants. Exceptions are deliberately not
    rendered: their messages may contain provider output or credentials.
    A returned failed/unknown report must become nonzero at the public adapter.
    """
    validate_run_prefix(run_prefix)
    phase = "prepare"
    primary: Outcome = "unknown"
    cleanup: Outcome = "not_attempted"
    effect_possible = False
    try:
        journal.prepare()
        phase = "initialize"
        journal.intent(phase)
        journal.assert_owned()
        driver.initialize()
        journal.result(phase, "verified")
        for revision in ("create", "update"):
            phase = revision
            journal.assert_owned()
            journal.intent(phase)
            journal.assert_owned()
            effect_possible = True
            driver.apply(revision)
            journal.result(phase, "verified")
            phase = f"{revision}_api"
            journal.intent(phase)
            journal.assert_owned()
            driver.verify_api(revision)
            journal.result(phase, "verified")
            phase = f"{revision}_dns"
            journal.intent(phase)
            journal.assert_owned()
            driver.verify_dns(revision)
            journal.result(phase, "verified")
        phase = "plan"
        journal.intent(phase)
        journal.assert_owned()
        if driver.drift():
            raise CompletedFailure()
        journal.result(phase, "verified")
        primary = "verified"
    except CompletedFailure:
        primary = "failed"
        try:
            journal.assert_owned()
            journal.result(phase, "failed")
        except Exception:
            return Report(run_prefix, phase, "unknown", "not_attempted")
    except Exception:
        # The durable intent, if committed, remains unresolved. Do not replay it
        # or attempt destroy while command termination/ownership is uncertain.
        return Report(run_prefix, phase, "unknown", "not_attempted")

    failed_phase = phase
    if not effect_possible:
        return Report(run_prefix, failed_phase, primary, cleanup)
    try:
        phase = "cleanup_state"
        journal.intent(phase)
        journal.assert_owned()
        if not driver.has_state():
            return Report(run_prefix, phase, primary, "unknown")
        journal.result(phase, "verified")
        phase = "destroy"
        journal.intent(phase)
        journal.assert_owned()
        driver.destroy()
        journal.result(phase, "verified")
        phase = "absence"
        journal.intent(phase)
        journal.assert_owned()
        driver.verify_absence()
        journal.result(phase, "verified")
        journal.complete()
        cleanup = "verified"
    except CompletedFailure:
        cleanup = "failed"
        try:
            journal.assert_owned()
            journal.result(phase, "failed")
        except Exception:
            cleanup = "unknown"
    except Exception:
        cleanup = "unknown"
    return Report(run_prefix, phase if cleanup != "verified" else failed_phase, primary, cleanup)
