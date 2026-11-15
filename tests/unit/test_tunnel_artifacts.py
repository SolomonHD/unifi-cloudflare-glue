"""Protected credential generation, material, verification and application boundaries."""

import json
import os
import secrets
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import dagger
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/main"))

import tunnel_artifacts as runtime

from main import UnifiCloudflareGlue


@pytest.fixture
def material(tmp_path, monkeypatch):
    token, secret = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    values = {
        "tunnel_ids": {"device": "tunnel-id"},
        "tunnel_tokens": {"device": token},
        "credentials_json": {
            "device": json.dumps(
                {
                    "AccountTag": "account-id",
                    "TunnelID": "tunnel-id",
                    "TunnelName": "fixture",
                    "TunnelSecret": secret,
                }
            )
        },
    }
    monkeypatch.setattr(runtime, "INPUT_DIRECTORY", str(tmp_path))
    output = tmp_path / "protected"
    monkeypatch.setattr(runtime, "OUTPUT_DIRECTORY", str(output))
    return values, output, (token, secret)


def write_inputs(values, directory):
    for name in runtime.OUTPUT_NAMES:
        path = directory / (".tunnel-output-" + name + ".json")
        path.write_text(json.dumps(values[name]))
        path.chmod(0o600)


def invoke(monkeypatch, action, format):
    monkeypatch.setattr(sys, "argv", ["tunnel_artifacts.py", action, format])
    return runtime.main()


@pytest.mark.parametrize(
    "format,files",
    [
        ("json", {"credentials.json"}),
        ("human", {"credentials.json", "credentials.txt"}),
        ("shell", {"credentials.json", "tunnel-secrets.sh"}),
    ],
)
def test_runtime_generates_only_acknowledged_private_material(
    material, monkeypatch, capsys, format, files
):
    values, output, canaries = material
    write_inputs(values, output.parent)
    assert invoke(monkeypatch, "build", format) == 0
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert {path.name for path in output.iterdir()} == files
    assert output.stat().st_mode & 0o777 == 0o700
    for file in output.iterdir():
        assert file.stat().st_mode & 0o777 == 0o600
        assert file.stat().st_uid == os.getuid()
    payload = json.loads((output / "credentials.json").read_text())
    assert payload["tunnel_ids"] == values["tunnel_ids"]
    assert payload["tunnel_tokens"] == values["tunnel_tokens"]
    assert payload["credentials_json"]["device"] == json.loads(values["credentials_json"]["device"])
    assert invoke(monkeypatch, "verify", format) == 0
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert set(summary) == runtime.SUMMARY_KEYS
    assert summary["count"] == 1
    assert all(summary[key] is True for key in runtime.SUMMARY_KEYS if key != "count")
    assert captured.err == ""
    if any(canary in captured.out + captured.err for canary in canaries):
        pytest.fail("Generated credential leaked outside protected files")


@pytest.mark.parametrize("invalid", ["empty", "ids", "token", "credential", "identity", "json"])
def test_malformed_generated_outputs_fail_without_partial_artifact_or_error_values(
    material, monkeypatch, capsys, invalid
):
    values, output, canaries = material
    if invalid == "empty":
        values["tunnel_ids"] = {}
    elif invalid == "ids":
        values["tunnel_ids"] = {"other": "tunnel-id"}
    elif invalid == "token":
        values["tunnel_tokens"]["device"] = ""
    elif invalid == "credential":
        values["credentials_json"]["device"] = {"AccountTag": canaries[1]}
    elif invalid == "identity":
        decoded = json.loads(values["credentials_json"]["device"])
        decoded["TunnelID"] = "wrong-id"
        values["credentials_json"]["device"] = decoded
    else:
        values["credentials_json"]["device"] = canaries[1] + "malformed-json"
    write_inputs(values, output.parent)
    assert invoke(monkeypatch, "build", "json") == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Protected credential processing failed\n"
    assert not output.exists()
    if any(canary in captured.out + captured.err for canary in canaries):
        pytest.fail("Malformed credential leaked through diagnostics")


@pytest.mark.parametrize("corruption", ["mode", "extra", "symlink", "material", "boolean-count"])
def test_verifier_rejects_unsafe_or_corrupted_artifacts(material, monkeypatch, capsys, corruption):
    values, output, _ = material
    write_inputs(values, output.parent)
    assert invoke(monkeypatch, "build", "shell") == 0
    if corruption == "mode":
        (output / "credentials.json").chmod(0o644)
    elif corruption == "extra":
        (output / "extra.txt").write_text("unexpected")
    elif corruption == "symlink":
        saved = output.parent / "outside.json"
        (output / "credentials.json").rename(saved)
        (output / "credentials.json").symlink_to(saved)
    elif corruption == "material":
        (output / "tunnel-secrets.sh").write_text("invalid material")
    else:
        payload = json.loads((output / "credentials.json").read_text())
        payload["count"] = True
        (output / "credentials.json").write_text(json.dumps(payload))
    assert invoke(monkeypatch, "verify", "shell") == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Protected credential processing failed\n"


def test_shell_material_quotes_derived_values_without_execution(material, monkeypatch, capsys):
    values, output, _ = material
    marker = output.parent / "must-not-exist"
    hostile = "'\n$(touch " + str(marker) + ") ; injected '"
    values["tunnel_tokens"]["device"] = hostile
    write_inputs(values, output.parent)
    assert invoke(monkeypatch, "build", "shell") == 0
    result = subprocess.run(
        [
            "bash",
            "-c",
            '. "$1"; test "$TUNNEL_0_TOKEN" = "$EXPECTED"',
            "fixture",
            str(output / "tunnel-secrets.sh"),
        ],
        env={**os.environ, "EXPECTED": hostile},
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert not marker.exists()
    assert capsys.readouterr().out == ""


class CredentialGraph:
    """Metadata operations are allowed; every raw contents/stdout read fails."""

    def __init__(self, calls, artifact, history=(), failure=None):
        self.calls, self.artifact, self.history, self.failure = calls, artifact, history, failure

    def __getattr__(self, name):
        if name.startswith("with_"):

            def changed(*args, **kwargs):
                return CredentialGraph(
                    self.calls, self.artifact, (*self.history, (name, args, kwargs)), self.failure
                )

            return changed
        raise AttributeError(name)

    def with_exec(self, argv, **options):
        self.calls.append((argv, options, self.history))
        return CredentialGraph(
            self.calls, self.artifact, (*self.history, ("exec", argv, options)), self.failure
        )

    async def sync(self):
        if self.failure == "timeout":
            raise TimeoutError("private-error-content")
        return self

    async def exit_code(self):
        return 17 if self.failure == "output" else 0

    async def stdout(self):
        raise AssertionError("Application stdout would disclose raw credentials")

    def directory(self, path):
        assert path == runtime.OUTPUT_DIRECTORY
        return self.artifact


@pytest.mark.asyncio
@pytest.mark.parametrize("format", ["json", "human", "shell"])
@pytest.mark.parametrize("backend", ["local", "s3"])
async def test_public_api_returns_native_artifact_without_raw_reads(format, backend):
    calls = []
    artifact = Mock(spec=dagger.Directory)
    artifact.file.return_value.contents = AsyncMock(
        side_effect=AssertionError("Raw File read forbidden")
    )
    graph = CredentialGraph(calls, artifact)
    source, state = Mock(spec=dagger.Directory), Mock(spec=dagger.Directory)
    args = dict(
        source=source,
        cloudflare_token=Mock(spec=dagger.Secret),
        cloudflare_account_id="account",
        zone_name="example.test",
        protected_disclosure=True,
        output_format=format,
    )
    if backend == "local":
        args["state_dir"] = state
    else:
        args.update(
            backend_type="s3",
            backend_config_file=Mock(spec=dagger.Secret),
            backend_config_format="hcl",
        )
    with (
        patch("main.terraform_runtime", return_value=graph),
        patch("main._with_backend_secret", new=AsyncMock(side_effect=lambda ctr, *_: ctr)),
    ):
        result = await UnifiCloudflareGlue().get_tunnel_secrets(**args)
    assert result is artifact
    native_outputs = [
        (argv, opts) for argv, opts, _ in calls if argv[:2] == ["terraform", "output"]
    ]
    assert [argv[-1] for argv, _ in native_outputs] == list(runtime.OUTPUT_NAMES)
    for argv, options in native_outputs:
        assert options["redirect_stdout"] == "/root/.tunnel-output-" + argv[-1] + ".json"
        assert options["redirect_stderr"] == "/root/.tunnel-output.stderr"
    assert calls[-1][0] == ["python", runtime.RUNTIME_SCRIPT, "build", format]
    assert calls[-1][1]["redirect_stderr"].startswith("/root/")
    assert calls[-1][1]["redirect_stdout"].startswith("/root/")
    assert all(argv[0] != "sh" for argv, _, _ in calls)
    artifact.file.return_value.contents.assert_not_awaited()
    source.entries.assert_not_called()
    state.entries.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["timeout", "output"])
async def test_credential_capture_failure_is_sanitized_and_stops_dependent_reads(failure):
    calls = []
    artifact = Mock(spec=dagger.Directory)
    graph = CredentialGraph(calls, artifact, failure=failure)
    with patch("main.terraform_runtime", return_value=graph), pytest.raises(RuntimeError) as caught:
        await UnifiCloudflareGlue().get_tunnel_secrets(
            source=Mock(spec=dagger.Directory),
            cloudflare_token=Mock(spec=dagger.Secret),
            cloudflare_account_id="account",
            zone_name="example.test",
            state_dir=Mock(spec=dagger.Directory),
            protected_disclosure=True,
        )
    assert len(calls) == 1
    assert "private-error-content" not in str(caught.value)
    assert ("outcome unknown" if failure == "timeout" else "exit code 17") in str(caught.value)
    assert caught.value.__suppress_context__


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", [None, "", {}, {"count": 0}, {"count": 1, "secret": "private"}])
async def test_bounded_verifier_rejects_unexpected_summaries(invalid):
    graph = Mock()
    graph.with_directory.return_value = graph
    graph.with_env_variable.return_value = graph
    graph.with_exec.return_value = graph
    graph.stdout = AsyncMock(return_value=json.dumps(invalid))
    with pytest.raises(ValueError, match="bounded credential verification"):
        await runtime.verify_tunnel_artifact(graph, Mock(spec=dagger.Directory), "json")
