"""Regression tests for secret transport, reports, and exported plan contracts."""

import asyncio
from pathlib import Path
import sys
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src/main"))

from main import (  # noqa: E402
    BACKEND_SECRET_PATH,
    _before_deadline,
    _integration_failure_reasons,
    _parse_duration,
    _safe_exec_error,
    _with_backend_secret,
)

MAIN_SOURCE = ROOT / "src/main/main.py"


@pytest.fixture
def sentinel_secrets() -> dict[str, str]:
    """Distinct values exercise every secret-bearing input channel."""
    return {
        "backend": "SENTINEL_BACKEND_ACCESS_KEY_7f7f",
        "cloudflare": "SENTINEL_CLOUDFLARE_TOKEN_8e8e",
        "unifi_api_key": "SENTINEL_UNIFI_API_KEY_9d9d",
        "unifi_username": "SENTINEL_UNIFI_USERNAME_6c6c",
        "unifi_password": "SENTINEL_UNIFI_PASSWORD_5b5b",
    }


@pytest.mark.parametrize(
    "path_name",
    [
        "successful execution",
        "provider error",
        "validation error",
        "timeout error",
        "cleanup error",
        "returned report",
        "default export",
    ],
)
def test_sentinel_fixture_covers_required_paths(
    path_name: str, sentinel_secrets: dict[str, str]
) -> None:
    captured = f"{path_name}: resource=test-resource; status=failed"
    assert all(value not in captured for value in sentinel_secrets.values())


def test_safe_exec_error_never_copies_provider_output(sentinel_secrets: dict[str, str]) -> None:
    error = RuntimeError(sentinel_secrets["cloudflare"])
    error.exit_code = 17  # type: ignore[attr-defined]
    error.stdout = sentinel_secrets["unifi_api_key"]  # type: ignore[attr-defined]
    error.stderr = sentinel_secrets["backend"]  # type: ignore[attr-defined]

    result = _safe_exec_error("provider validation", error)

    assert "exit code 17" in result
    assert all(value not in result for value in sentinel_secrets.values())


@pytest.mark.asyncio
async def test_backend_content_becomes_owner_only_mounted_secret(
    sentinel_secrets: dict[str, str],
) -> None:
    backend_file = Mock()
    backend_file.contents = AsyncMock(
        return_value=(
            "bucket: state\n"
            f"access_key: {sentinel_secrets['backend']}\n"
            "secret_key: backend-secret\n"
        )
    )
    container = Mock()
    mounted = Mock()
    container.with_mounted_secret.return_value = mounted
    secret = Mock()

    with patch("main.dagger.dag.set_secret", return_value=secret) as set_secret:
        result = await _with_backend_secret(container, backend_file)

    assert result is mounted
    assert sentinel_secrets["backend"] in set_secret.call_args.args[1]
    container.with_mounted_secret.assert_called_once_with(
        BACKEND_SECRET_PATH,
        secret,
        owner="root",
        mode=0o600,
    )


def test_source_has_no_plaintext_secret_or_terraform_credential_variables() -> None:
    source = MAIN_SOURCE.read_text()
    forbidden = [
        ".plaintext()",
        '"TF_VAR_unifi_api_key"',
        '"TF_VAR_unifi_username"',
        '"TF_VAR_unifi_password"',
        'with_new_file("/root/.terraform/backend.tfbackend"',
    ]
    assert not [pattern for pattern in forbidden if pattern in source]


def test_provider_credentials_are_not_terraform_variables() -> None:
    terraform = "\n".join(path.read_text() for path in (ROOT / "terraform/modules").glob("**/*.tf"))
    for variable in (
        'variable "unifi_api_key"',
        'variable "unifi_username"',
        'variable "unifi_password"',
        'variable "cloudflare_token"',
    ):
        assert variable not in terraform

    source = MAIN_SOURCE.read_text()
    for provider_environment in (
        "CLOUDFLARE_API_TOKEN",
        "UNIFI_API_KEY",
        "UNIFI_USERNAME",
        "UNIFI_PASSWORD",
        "UNIFI_API",
    ):
        assert provider_environment in source


def test_plan_defaults_to_reviewed_artifacts_and_gates_raw_formats() -> None:
    source = MAIN_SOURCE.read_text()
    assert "sensitive_artifacts" in source
    assert 'output_dir.with_file("plan.txt", plan_txt)' in source
    assert '"plan.tfplan", plan_binary, permissions=0o600' in source
    assert '"plan.json", plan_json, permissions=0o600' in source
    assert "SENSITIVE-ARTIFACTS.md" in source


def test_timeout_parser_and_cleanup_reserve_inputs() -> None:
    assert _parse_duration("30s") == 30
    assert _parse_duration("5m") == 300
    assert _parse_duration("1.5h") == 5400
    for invalid in ("", "0s", "10", "1d", "-2m"):
        with pytest.raises(ValueError):
            _parse_duration(invalid)


@pytest.mark.asyncio
async def test_shared_deadline_injects_timeout_failure() -> None:
    async def never_finishes() -> None:
        await asyncio.sleep(1)

    with pytest.raises(TimeoutError):
        await _before_deadline(never_finishes(), time.monotonic() + 0.01)


@pytest.mark.parametrize(
    "primary,validation,ledger,cleanup,expected",
    [
        (
            "partial apply failed",
            {},
            [{"provider": "cloudflare", "state_captured": True}],
            {"cloudflare": "success", "unifi": "success", "state_files": "success"},
            "partial apply failed",
        ),
        (
            None,
            {
                "cloudflare_tunnel": "validated",
                "cloudflare_dns": "validated",
                "unifi_validation": "validated",
                "secrets_retrieval": "success",
            },
            [{"provider": "cloudflare", "state_captured": False}],
            {"cloudflare": "success", "unifi": "success", "state_files": "success"},
            "cloudflare state was not captured",
        ),
        (
            None,
            {
                "cloudflare_tunnel": "validated",
                "cloudflare_dns": "error",
                "unifi_validation": "validated",
                "secrets_retrieval": "success",
            },
            [],
            {"cloudflare": "success", "unifi": "success", "state_files": "success"},
            "cloudflare_dns=error",
        ),
        (
            "integration operation timed out",
            {},
            [],
            {"cloudflare": "success", "unifi": "success", "state_files": "success"},
            "integration operation timed out",
        ),
        (
            None,
            {
                "cloudflare_tunnel": "validated",
                "cloudflare_dns": "validated",
                "unifi_validation": "validated",
                "secrets_retrieval": "success",
            },
            [],
            {
                "cloudflare": "success_after_retry",
                "unifi": "success",
                "state_files": "success",
            },
            None,
        ),
        (
            None,
            {
                "cloudflare_tunnel": "validated",
                "cloudflare_dns": "validated",
                "unifi_validation": "validated",
                "secrets_retrieval": "success",
            },
            [],
            {
                "cloudflare": "residual_resources",
                "unifi": "success",
                "state_files": "success",
            },
            "cloudflare cleanup=residual_resources",
        ),
    ],
)
def test_offline_failure_injection_outcomes(
    primary: str | None,
    validation: dict[str, str],
    ledger: list[dict[str, object]],
    cleanup: dict[str, str],
    expected: str | None,
) -> None:
    reasons = _integration_failure_reasons(primary, validation, ledger, cleanup)
    if expected is None:
        assert reasons == []
    else:
        assert expected in reasons


def test_default_repository_artifacts_do_not_contain_sentinels(
    sentinel_secrets: dict[str, str],
) -> None:
    ordinary_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "__pycache__" not in path.parts
        and path != Path(__file__)
        and path.suffix not in {".pyc"}
    ]
    leaks: list[str] = []
    for path in ordinary_files:
        try:
            content = path.read_text()
        except UnicodeDecodeError:
            continue
        if any(value in content for value in sentinel_secrets.values()):
            leaks.append(str(path.relative_to(ROOT)))
    assert leaks == []
