"""Qualified invocation must not silently select an ambient CLI or engine."""

import os
import subprocess
from pathlib import Path

import pytest

WRAPPER = Path(__file__).resolve().parents[2] / "scripts/dagger-qualified.sh"
CLI_SHA = "d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075"
ENGINE = "image://registry.dagger.io/engine@sha256:ad121f720ed9bfb8e740f99dd783fa8472965a5e262fc64ff3ef2634cea1e6dd"


def run_wrapper(binary, *args, path=os.defpath):
    return subprocess.run(
        ["bash", str(WRAPPER), *args],
        env={"PATH": path, "DAGGER_BIN": str(binary), "DAGGER_ENGINE": "unqualified"},
        capture_output=True,
        text=True,
        check=False,
    )


def test_missing_cli_fails_before_engine_access(tmp_path):
    result = run_wrapper(tmp_path / "absent", "api", "call")
    assert result.returncode == 2
    assert "unavailable" in result.stderr
    assert not result.stdout


def test_wrong_cli_checksum_does_not_execute_it(tmp_path):
    binary = tmp_path / "dagger"
    binary.write_text("#!/bin/sh\nprintf 'unreviewed executable ran'\n")
    binary.chmod(0o700)
    result = run_wrapper(binary, "api", "call")
    assert result.returncode == 2
    assert "checksum differs" in result.stderr
    assert not result.stdout


@pytest.fixture
def qualified_boundary(tmp_path):
    binary = tmp_path / "dagger"
    binary.write_text("#!/bin/sh\nprintf '%s\\n' \"$@\"\n")
    binary.chmod(0o700)
    checksum = tmp_path / "sha256sum"
    checksum.write_text(f"#!/bin/sh\nprintf '{CLI_SHA}  fixture\\n'\n")
    checksum.chmod(0o700)
    return binary, f"{tmp_path}:{os.defpath}"


def test_pinned_engine_precedes_forwarded_arguments(qualified_boundary):
    binary, path = qualified_boundary
    result = run_wrapper(binary, "api", "call", "-m", ".", "hello", path=path)
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["--engine", ENGINE, "api", "call", "-m", ".", "hello"]


@pytest.mark.parametrize("override", [["--engine", "cloud"], ["--engine=tcp://other"]])
def test_unqualified_engine_override_never_reaches_cli(qualified_boundary, override):
    binary, path = qualified_boundary
    result = run_wrapper(binary, *override, path=path)
    assert result.returncode == 2
    assert "separately qualified" in result.stderr
    assert not result.stdout
