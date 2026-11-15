"""Derived backend fields must not reach the engine's ordinary exec logs."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/main"))

from execution import live_exec, plan_counts


class Container:
    def __init__(self):
        self.options = None
        self.argv = None

    def with_env_variable(self, name, value):
        assert name == "EXECUTION_NONCE"
        assert value
        return self

    def with_exec(self, argv, **options):
        self.argv, self.options = argv, options
        return self


@pytest.mark.parametrize("phase", ["init", "apply", "destroy", "plan", "show"])
def test_terraform_exec_does_not_use_default_output_channels(phase):
    container = Container()
    assert live_exec(container, ["terraform", phase]) is container
    assert container.argv == ["terraform", phase]
    assert container.options == {
        "redirect_stdout": "/root/.terraform-exec.stdout",
        "redirect_stderr": "/root/.terraform-exec.stderr",
    }


def test_explicit_protected_plan_output_preserved():
    container = Container()
    live_exec(container, ["terraform", "show", "-json"], redirect_stdout="/root/plan.json")
    assert container.options["redirect_stdout"] == "/root/plan.json"
    assert container.options["redirect_stderr"] == "/root/.terraform-exec.stderr"


def test_sanitized_parser_summary_keeps_its_bounded_channel():
    container = Container()
    live_exec(container, ["python", "-c", "print('summary')"])
    assert container.options == {}


def test_unrepresented_state_forgetting_is_not_reported_as_zero_drift():
    with pytest.raises(ValueError, match="invalid action array"):
        plan_counts({"resource_changes": [{"change": {"actions": ["forget"]}}]})
