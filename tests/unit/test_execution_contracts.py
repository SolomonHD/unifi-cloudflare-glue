"""Offline process, response and execution boundary checks, without provider access."""

import io
import json
import os
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/main"))

from execution import CLOUDFLARE_QUERY, parse_api_response, plan_counts, prepare_root, selected_root


@pytest.mark.parametrize(
    "actions,expected",
    [
        (["create"], (1, 0, 0, 0)),
        (["update"], (0, 1, 0, 0)),
        (["delete"], (0, 0, 1, 0)),
        (["delete", "create"], (1, 0, 1, 1)),
        (["create", "delete"], (1, 0, 1, 1)),
        (["no-op"], (0, 0, 0, 0)),
        (["read"], (0, 0, 0, 0)),
    ],
)
def test_real_action_arrays(actions, expected):
    plan = {
        "resource_changes": [{"change": {"actions": actions, "after": {"secret": "canary-value"}}}]
    }
    counts = plan_counts(plan)
    assert tuple(counts.values()) == expected
    assert "canary" not in json.dumps(counts)


@pytest.mark.parametrize(
    "plan",
    [
        None,
        [],
        {"resource_changes": None},
        {"resource_changes": {}},
        {"resource_changes": [None]},
        {"resource_changes": [{}]},
        {"resource_changes": [{"change": {"actions": [{"action": "create"}]}}]},
        {"resource_changes": [{"change": {"actions": "create"}}]},
        {"resource_changes": [{"change": {"actions": []}}]},
        {"resource_changes": [{"change": {"actions": ["create", "update"]}}]},
    ],
)
def test_malformed_actions_never_become_zero_drift(plan):
    with pytest.raises(ValueError, match="Terraform plan"):
        plan_counts(plan)


@pytest.mark.parametrize(
    "status,body",
    [
        (401, '{"success": true, "result": [], "errors": []}'),
        (500, "canary-auth-error"),
        (200, "null"),
        (200, "[]"),
        (200, "not-json"),
        (200, '{"success": false, "result": [], "errors": []}'),
        (200, '{"success": true, "result": null, "errors": []}'),
        (200, '{"success": true, "result": [], "errors": ["canary"]}'),
        (200, '{"result": []}'),
        (200, '{"success": true,"result": [1],"errors": []}'),
    ],
)
def test_http_or_error_envelopes_fail_closed(status, body):
    with pytest.raises(ValueError) as error:
        parse_api_response(body, status, "cloudflare")
    assert "canary" not in str(error.value)


def test_explicit_success_empty_result_is_valid_absence():
    assert parse_api_response('{"success":true,"result":[],"errors":[]}', 200, "cloudflare") == []


@pytest.mark.parametrize(
    "scope,root", [("full", "glue"), ("unifi", "unifi-dns"), ("cloudflare", "cloudflare-tunnel")]
)
def test_common_preparation_retains_sibling_module_layout(scope, root):
    assert selected_root(scope == "unifi", scope == "cloudflare", scope) == root
    dag = Mock()
    ctr = Mock()
    ctr.with_directory.return_value = ctr
    ctr.with_workdir.return_value = ctr
    ctr.with_new_file.return_value = ctr
    with patch("execution.terraform_runtime", return_value=ctr):
        result, path = prepare_root(dag, "qualified-image", root, "s3")
    assert result is ctr
    assert path == "/module/" + root
    dag.current_module.return_value.source.return_value.directory.assert_called_once_with(
        "terraform/modules"
    )
    ctr.with_directory.assert_called_once_with(
        "/module", dag.current_module.return_value.source.return_value.directory.return_value
    )
    ctr.with_workdir.assert_called_once_with(path)
    assert any(c.args[0] == path + "/backend.tf" for c in ctr.with_new_file.call_args_list)


@pytest.mark.parametrize(
    "format,content,exitcode",
    [
        ("yaml", 'bucket: state\nsecret_key: "canary\\ncredential"\n', 0),
        ("hcl", 'bucket = "state"\nsecret_key = "canary-credential"\n', 0),
        ("yaml", "canary-secret: [unterminated", 1),
        ("hcl", 'secret = "canary-unterminated', 1),
        ("yaml", "", 1),
        ("invalid", "canary-credential", 1),
    ],
)
def test_backend_process_keeps_plaintext_inside_protected_files(
    tmp_path, format, content, exitcode
):
    source = tmp_path / "input"
    destination = tmp_path / "backend.tfbackend"
    source.write_text(content)
    source.chmod(0o600)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "src/main/backend_runtime.py"),
            format,
            str(source),
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == exitcode
    assert "canary" not in result.stdout + result.stderr
    assert result.stdout == ""
    if exitcode == 0:
        assert destination.stat().st_mode & 0o777 == 0o600
        assert "secret_key" in destination.read_text()
    else:
        assert not destination.exists()


def test_cloudflare_http_program_checks_every_envelope_without_printing_credentials():
    canary = "synthetic-" + "token-cannot-leak"
    envelopes = [
        {"success": True, "errors": [], "result": []},
        {"success": True, "errors": [], "result": [{"id": "zone1", "name": "example.test"}]},
        {"success": False, "errors": [{"message": canary}], "result": []},
    ]
    responses = []
    for envelope in envelopes:
        response = Mock()
        response.status = 200
        response.read.return_value = json.dumps(envelope).encode()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        responses.append(response)
    stdout, stderr = io.StringIO(), io.StringIO()
    with (
        patch.dict(os.environ, {"CLOUDFLARE_API_TOKEN": canary}),
        patch.object(
            sys, "argv", ["query.py", "account", "example.test", "test-tunnel", "test.example.test"]
        ),
        patch("urllib.request.urlopen", side_effect=responses) as urlopen,
        redirect_stdout(stdout),
        redirect_stderr(stderr),
        pytest.raises(SystemExit) as failure,
    ):
        exec(CLOUDFLARE_QUERY, {})
    assert failure.value.code == 1
    assert urlopen.call_count == 3
    assert stdout.getvalue() == ""
    assert canary not in stderr.getvalue()
    assert "verification failed" in stderr.getvalue()
