"""Read-only recovery diagnostics never publish state or invoke an effect."""

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "canary_observe_test_package",
    ROOT / "src/main/__init__.py",
    submodule_search_locations=[str(ROOT / "src/main")],
)
package = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = package
from canary_observe_test_package import canary_observation as observation
from canary_observe_test_package.canary_store import StoreError
from canary_observe_test_package.canary_terraform import TerraformUnknown

RUN = "gha-1794714939-43674454065-1"
SENTINEL = "synthetic-private-state-value"


def retained(prefix=RUN):
    return SimpleNamespace(
        ledger=SimpleNamespace(
            run=SimpleNamespace(run_prefix=prefix, revision="a" * 40, zone_id="b" * 32),
            completed=None,
            receipts=[SimpleNamespace(phase="create", outcome=None)],
        )
    )


def test_missing_runtime_guard_prevents_even_transport_construction(monkeypatch):
    constructor = Mock()
    monkeypatch.setattr(observation, "in_runtime", lambda: False)
    monkeypatch.setattr(observation, "Boto3S3Transport", constructor)
    with pytest.raises(StoreError):
        observation.observe(RUN)
    constructor.assert_not_called()


def test_missing_state_observation_never_qualifies_or_initializes(monkeypatch):
    transport = Mock()
    transport.get.return_value = retained()
    transport.get_blob.return_value = None
    constructor = Mock(return_value=transport)
    monkeypatch.setattr(observation, "in_runtime", lambda: True)
    monkeypatch.setattr(observation, "Boto3S3Transport", constructor)
    result = observation.observe(RUN)
    assert constructor.call_args.kwargs["observation_only"] is True
    assert result["state_present"] is False
    assert result["last_phase"] == "create"
    transport.qualify_backend.assert_not_called()
    transport.create_blob.assert_not_called()
    transport.delete_blob.assert_not_called()


def test_different_retained_run_is_not_inspected(monkeypatch):
    transport = Mock()
    transport.get.return_value = retained("gha-1794714939-999-1")
    monkeypatch.setattr(observation, "in_runtime", lambda: True)
    monkeypatch.setattr(observation, "Boto3S3Transport", Mock(return_value=transport))
    with pytest.raises(StoreError):
        observation.observe(RUN)
    transport.get_blob.assert_not_called()


def test_invalid_state_shape_reports_only_fixed_error_and_boolean_diffs(monkeypatch, capsys):
    private = json.dumps({"version": 4, "resources": [], "secret": SENTINEL}).encode()
    transport = Mock()
    transport.get.return_value = retained()
    transport.get_blob.return_value = SimpleNamespace(data=private, version="opaque")
    driver = Mock()
    driver._run.return_value = (0, private)
    driver._state.side_effect = TerraformUnknown("unexpected_state_resource")
    monkeypatch.setattr(observation, "in_runtime", lambda: True)
    monkeypatch.setattr(observation, "Boto3S3Transport", Mock(return_value=transport))
    monkeypatch.setattr(observation, "TerraformDriver", Mock(return_value=driver))
    monkeypatch.setattr(observation.shutil, "copytree", lambda source, target: target.mkdir())
    result = observation.observe(RUN)
    assert result["state_shape_valid"] is False
    assert result["state_shape_error"] == "unexpected_state_resource"
    assert SENTINEL not in json.dumps(result) + capsys.readouterr().out
    driver.apply.assert_not_called()
    driver.destroy.assert_not_called()
    driver._plan.assert_not_called()
