"""Exercise the offline graph with an immutable transport and real shell exits."""

import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/main"))

import offline


@dataclass(frozen=True)
class Container:
    platform: str | None = None
    image: str = ""
    events: tuple = ()

    def record(self, operation, *args, **kwargs):
        return replace(self, events=(*self.events, (operation, args, kwargs)))

    def from_(self, image):
        return replace(self.record("from", image), image=image)

    def file(self, path):
        return self.image, path

    def with_file(self, *args, **kwargs):
        return self.record("file", *args, **kwargs)

    def with_directory(self, *args, **kwargs):
        return self.record("directory", *args, **kwargs)

    def with_workdir(self, path):
        return self.record("workdir", path)

    def with_env_variable(self, *args):
        return self.record("env", *args)

    def with_exec(self, *args, **kwargs):
        return self.record("exec", *args, **kwargs)

    async def stdout(self):
        source = next(args[1] for op, args, _ in self.events if op == "directory")
        environment = {
            "PATH": os.defpath,
            **{args[0]: args[1] for op, args, _ in self.events if op == "env"},
        }
        # The transport executes the actual final argv; prerequisite acquisition
        # is not a subprocess in unit tests and never accesses a registry here.
        command = [args[0] for op, args, _ in self.events if op == "exec"][-1]
        return subprocess.run(
            command, cwd=source, env=environment, capture_output=True, text=True, check=True
        ).stdout


def graph(source):
    client = Mock()
    client.container.side_effect = Container
    with (
        patch.object(offline.core, "core", return_value=client),
        patch.object(offline, "kcl_binary", return_value="qualified-kcl") as compiler,
    ):
        container = offline.offline_verification_container(source)
    compiler.assert_called_once_with()
    return container


def test_pinned_tool_files_and_ephemeral_source_projection():
    source = object()
    container = graph(source)
    assert container.platform == "linux/amd64"
    assert container.image == offline.PYTHON_IMAGE
    files = [args for op, args, _ in container.events if op == "file"]
    assert files == [
        ("/usr/local/bin/uv", (offline.UV_IMAGE, "/usr/local/bin/uv")),
        ("/usr/local/bin/kcl", "qualified-kcl"),
        ("/usr/local/bin/terraform", (offline.terraform_image(), "/bin/terraform")),
    ]
    assert all("@sha256:" in image for image in (offline.UV_IMAGE, offline.PYTHON_IMAGE))
    [(args, kwargs)] = [
        (args, kwargs) for op, args, kwargs in container.events if op == "directory"
    ]
    assert args == ("/workspace", source)
    assert kwargs == {
        "include": list(offline.SOURCE_INCLUDE),
        "exclude": list(offline.SOURCE_EXCLUDE),
    }
    assert "tests/unit/**" in kwargs["include"]
    assert "tests/fixtures/**" in kwargs["include"]
    assert "tests/integration/**" not in kwargs["include"]
    assert "**/*.tfstate*" in kwargs["exclude"]
    assert "**/*.tfplan*" in kwargs["exclude"]
    assert "**/*.tfbackend" in kwargs["exclude"]
    assert "**/.env.*" in kwargs["exclude"]


def test_bootstrap_is_before_offline_and_baseline_is_not_reimplemented():
    container = graph(object())
    commands = [args[0] for op, args, _ in container.events if op == "exec"]
    assert commands[:4] == [
        ["python", "--version"],
        ["uv", "--version"],
        ["kcl", "version"],
        ["terraform", "version", "-json"],
    ]
    assert commands[-1] == ["bash", "scripts/verify-offline.sh"]
    bootstrap = commands[-2]
    assert commands[-3] == ["uv", "sync", "--frozen"]
    assert bootstrap[:4] == ["uv", "run", "--frozen", "--no-sync"]
    assert bootstrap[-3:-1] == ["python", "-c"]
    script = (ROOT / "scripts/verify-offline.sh").read_text()
    project = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert project["dependency-groups"]["dev"] == [
        "pytest==9.2.0",
        "pytest-asyncio==1.5.0",
        "black==26.10.1",
        "isort==9.0.2",
        "mypy==2.4.1",
        "types-PyYAML==6.0.12.20261113",
    ]
    assert "--with" not in script
    assert "--no-sync" in script
    for check in (
        "verify black --check src tests",
        "verify isort --check-only src tests",
        "verify mypy src/main",
        "verify python -m compileall -q src tests",
        "verify python -m pytest tests/unit -ra",
    ):
        assert check in script
    for entry in (
        "main.k",
        "test_validation.k",
        "test_error_validation.k",
        "test_error_format.k",
        "test_cloudflare.k",
        "generators/unifi.k",
        "generators/cloudflare.k",
    ):
        assert entry in script
    assert "--offline --frozen" in script
    assert all(not kwargs for op, _, kwargs in container.events if op == "exec")
    offline_index = container.events.index(("env", ("UV_OFFLINE", "true"), {}))
    assert container.events[offline_index + 1 :] == (
        ("exec", (["bash", "scripts/verify-offline.sh"],), {}),
    )


@pytest.mark.parametrize("exit_code", [0, 7])
async def test_actual_verification_argv_preserves_success_and_failure(
    tmp_path, monkeypatch, exit_code
):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    script = scripts / "verify-offline.sh"
    script.write_text(
        "set -eu\n"
        'test "$UV_OFFLINE" = true\n'
        'test "$UV_PYTHON_DOWNLOADS" = never\n'
        'test -z "${CLOUDFLARE_API_TOKEN+x}"\n'
        'test -z "${UNIFI_API_KEY+x}"\n'
        f"exit {exit_code}\n"
    )
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "synthetic-not-forwarded")
    monkeypatch.setenv("UNIFI_API_KEY", "synthetic-not-forwarded")
    container = graph(tmp_path)
    before = script.read_bytes()
    if exit_code:
        with pytest.raises(subprocess.CalledProcessError) as error:
            await container.stdout()
        assert error.value.returncode == exit_code
        assert error.value.cmd == ["bash", "scripts/verify-offline.sh"]
    else:
        assert await container.stdout() == ""
    assert script.read_bytes() == before
    assert list(tmp_path.iterdir()) == [scripts]
