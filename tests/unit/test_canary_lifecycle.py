"""Failure injection for orchestration; no live backend or provider is selected."""

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
# Existing suites load main.py as a top-level module, so use a distinct package.
spec = importlib.util.spec_from_file_location(
    "canary_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_test_package.canary_lifecycle import CompletedFailure, run_canary

PREFIX = "gha-1794700000-123-1"


class Harness:
    def __init__(self, fail=None, unknown=False, missing_state=False, drift=False):
        self.fail = fail
        self.unknown = unknown
        self.missing_state = missing_state
        self.has_drift = drift
        self.calls = []

    def call(self, name):
        self.calls.append(name)
        if name == self.fail or isinstance(self.fail, set) and name in self.fail:
            error = RuntimeError if self.unknown else CompletedFailure
            raise error("synthetic-secret-provider-output")

    def prepare(self):
        self.call("prepare")

    def assert_owned(self):
        self.call("owned")

    def intent(self, phase):
        self.call(f"intent:{phase}")

    def result(self, phase, outcome):
        self.call(f"result:{phase}:{outcome}")

    def complete(self):
        self.call("complete")

    def initialize(self):
        self.call("initialize")

    def apply(self, revision):
        self.call(revision)

    def verify_api(self, revision):
        self.call(f"api:{revision}")

    def verify_dns(self, revision):
        self.call(f"dns:{revision}")

    def drift(self):
        self.call("plan")
        return self.has_drift

    def has_state(self):
        self.call("state")
        return not self.missing_state

    def destroy(self):
        self.call("destroy")

    def verify_absence(self):
        self.call("absence")


def test_full_lifecycle_intents_precede_effects():
    harness = Harness()
    report = run_canary(PREFIX, harness, harness)
    assert report.succeeded
    for phase in ("create", "update", "destroy"):
        assert harness.calls.index(f"intent:{phase}") < harness.calls.index(phase)
        assert harness.calls[harness.calls.index(phase) - 1] == "owned"
    assert harness.calls[-1] == "complete"


@pytest.mark.parametrize("phase", ["create", "api:create", "dns:create", "update", "plan"])
def test_completed_primary_failure_attempts_cleanup_and_keeps_failure(phase):
    harness = Harness(fail=phase)
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == "failed"
    assert report.cleanup == "verified"
    assert not report.succeeded
    assert "destroy" in harness.calls
    assert "synthetic-secret" not in repr(report)


@pytest.mark.parametrize("phase", ["create", "update", "intent:create", "result:create:verified"])
def test_unknown_or_store_failure_does_not_replay_or_destroy(phase):
    harness = Harness(fail=phase, unknown=True)
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == "unknown"
    assert report.cleanup == "not_attempted"
    assert "destroy" not in harness.calls
    assert "complete" not in harness.calls
    assert harness.calls.count("create") <= 1


@pytest.mark.parametrize("phase", ["destroy", "absence"])
def test_cleanup_failure_is_separate_and_never_success(phase):
    harness = Harness(fail=phase)
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == "verified"
    assert report.cleanup == "failed"
    assert not report.succeeded
    assert "complete" not in harness.calls


def test_missing_state_requires_explicit_reconciliation():
    harness = Harness(missing_state=True)
    report = run_canary(PREFIX, harness, harness)
    assert report.cleanup == "unknown"
    assert "destroy" not in harness.calls


def test_nonzero_drift_is_primary_failure_even_after_cleanup():
    harness = Harness(drift=True)
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == "failed"
    assert report.cleanup == "verified"


@pytest.mark.parametrize("phase", ["prepare", "owned"])
def test_backend_or_ownership_loss_blocks_effects(phase):
    harness = Harness(fail=phase, unknown=True)
    report = run_canary(PREFIX, harness, harness)
    assert not report.succeeded
    assert "create" not in harness.calls


def test_bad_name_rejected_before_any_adapter_call():
    harness = Harness()
    with pytest.raises(ValueError):
        run_canary("gha-1-2-3.evil", harness, harness)
    assert harness.calls == []


def test_primary_and_cleanup_failures_are_both_retained():
    harness = Harness(fail={"dns:create", "destroy"})
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == report.cleanup == "failed"
    assert "complete" not in harness.calls


def test_ownership_loss_after_intent_prevents_create():
    class LostOwner(Harness):
        def assert_owned(self):
            self.call("owned")
            if "intent:create" in self.calls:
                raise RuntimeError("synthetic-secret-provider-output")

    harness = LostOwner()
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == "unknown"
    assert "intent:create" in harness.calls
    assert "create" not in harness.calls
    assert "destroy" not in harness.calls


def test_process_interruption_does_not_promise_finalization():
    class KilledWriter(Harness):
        def apply(self, revision):
            self.call(revision)
            raise KeyboardInterrupt()

    harness = KilledWriter()
    with pytest.raises(KeyboardInterrupt):
        run_canary(PREFIX, harness, harness)
    assert "intent:create" in harness.calls
    assert "destroy" not in harness.calls
    assert "complete" not in harness.calls


@pytest.mark.parametrize(
    "phase", ["destroy", "result:destroy:verified", "result:absence:verified", "complete"]
)
def test_uncertain_cleanup_or_final_receipt_never_reports_success(phase):
    harness = Harness(fail=phase, unknown=True)
    report = run_canary(PREFIX, harness, harness)
    assert report.primary == "verified"
    assert report.cleanup == "unknown"
    assert not report.succeeded
    assert harness.calls.count("destroy") == 1
    assert "synthetic-secret" not in repr(report)
