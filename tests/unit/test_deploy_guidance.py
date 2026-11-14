"""Supported combined deploy API, selection, and secret-safe retrieval guidance."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call, patch

import dagger
import pytest
from dagger._exceptions import QueryErrorValue

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/main"))

from main import BACKEND_SECRET_PATH, UnifiCloudflareGlue

GUIDANCE = "Next Step: Retrieve Tunnel Credentials"
RAW_OUTPUT = 'SENTINEL_PROVIDER_OUTPUT {"resources": ["raw-state"]}'


@pytest.fixture
def deployment():
    """Mock the Dagger boundary, leaving deployment orchestration under test."""
    source = Mock(spec=dagger.Directory)
    generated = Mock(spec=dagger.File)
    directory = Mock(spec=dagger.Directory)
    directory.with_file.return_value = directory
    container = Mock(spec=dagger.Container)
    for method in (
        "from_",
        "with_directory",
        "with_new_file",
        "with_env_variable",
        "with_secret_variable",
        "with_mounted_secret",
        "with_workdir",
        "with_exec",
    ):
        getattr(container, method).return_value = container
    container.stdout = AsyncMock(return_value=RAW_OUTPUT)
    cf_token = Mock(spec=dagger.Secret)
    cf_token.plaintext = AsyncMock(return_value="SENTINEL_CF_TOKEN")
    unifi_key = Mock(spec=dagger.Secret)
    unifi_key.plaintext = AsyncMock(return_value="SENTINEL_UNIFI_KEY")
    with (
        patch("main.dagger.dag") as dag,
        patch.object(
            UnifiCloudflareGlue, "generate_unifi_config", new_callable=AsyncMock
        ) as generate_unifi,
        patch.object(
            UnifiCloudflareGlue, "generate_cloudflare_config", new_callable=AsyncMock
        ) as generate_cloudflare,
    ):
        dag.container.return_value = container
        dag.directory.return_value = directory
        generate_unifi.return_value = generated
        generate_cloudflare.return_value = generated
        yield SimpleNamespace(
            module=UnifiCloudflareGlue(),
            source=source,
            container=container,
            dag=dag,
            generate_unifi=generate_unifi,
            generate_cloudflare=generate_cloudflare,
            cf_token=cf_token,
            unifi_key=unifi_key,
        )


def deploy_arguments(deployment, scope):
    """Omit credentials entirely for an unselected provider."""
    arguments = {"kcl_source": deployment.source, "kcl_version": "0.11.0"}
    if scope != "cloudflare":
        arguments.update(
            unifi_url="https://unifi.example.test:8443",
            unifi_api_key=deployment.unifi_key,
        )
    if scope != "unifi":
        arguments.update(
            cloudflare_token=deployment.cf_token,
            cloudflare_account_id="account-actual-123",
            zone_name="actual.example.test",
        )
    if scope == "cloudflare":
        arguments["cloudflare_only"] = True
    elif scope == "unifi":
        arguments["unifi_only"] = True
    return arguments


@pytest.mark.asyncio
@pytest.mark.parametrize("scope", ["full", "cloudflare", "unifi"])
async def test_selection_runs_one_terraform_cycle_with_only_selected_inputs(deployment, scope):
    result = await deployment.module.deploy(**deploy_arguments(deployment, scope))

    assert "deployment" in result.lower()
    assert "completed successfully" in result
    assert (GUIDANCE in result) == (scope != "unifi")
    assert deployment.container.with_exec.call_args_list == [
        call(["terraform", "init"]),
        call(["terraform", "apply", "-auto-approve"]),
    ]
    module_path = {
        "full": "terraform/modules",
        "cloudflare": "terraform/modules/cloudflare-tunnel",
        "unifi": "terraform/modules/unifi-dns",
    }[scope]
    deployment.dag.current_module.return_value.source.return_value.directory.assert_called_once_with(
        module_path
    )
    deployment.container.with_workdir.assert_called_once_with(
        "/module/glue" if scope == "full" else "/module"
    )
    if scope != "cloudflare":
        deployment.generate_unifi.assert_awaited_once_with(deployment.source, "0.11.0")
    else:
        deployment.generate_unifi.assert_not_awaited()
    if scope != "unifi":
        deployment.generate_cloudflare.assert_awaited_once_with(deployment.source, "0.11.0")
    else:
        deployment.generate_cloudflare.assert_not_awaited()
    expected_secrets = []
    if scope != "cloudflare":
        expected_secrets.append(call("UNIFI_API_KEY", deployment.unifi_key))
    if scope != "unifi":
        expected_secrets.append(call("CLOUDFLARE_API_TOKEN", deployment.cf_token))
    assert deployment.container.with_secret_variable.call_args_list == expected_secrets
    deployment.cf_token.plaintext.assert_not_awaited()
    deployment.unifi_key.plaintext.assert_not_awaited()
    assert RAW_OUTPUT not in result


@pytest.mark.asyncio
async def test_conflicting_selection_fails_before_generation_or_deployment(deployment):
    result = await deployment.module.deploy(
        kcl_source=deployment.source, unifi_only=True, cloudflare_only=True
    )

    assert "Cannot use both --unifi-only and --cloudflare-only" in result
    assert GUIDANCE not in result
    deployment.generate_unifi.assert_not_awaited()
    deployment.generate_cloudflare.assert_not_awaited()
    deployment.dag.container.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scope,missing,message",
    [
        ("cloudflare", "cloudflare_token", "--cloudflare-token"),
        ("cloudflare", "cloudflare_account_id", "--cloudflare-account-id"),
        ("cloudflare", "zone_name", "--zone-name"),
        ("unifi", "unifi_api_key", "--unifi-api-key"),
        ("unifi", "unifi_url", "--unifi-url"),
        ("full", "unifi_api_key", "--unifi-api-key"),
        ("full", "cloudflare_token", "--cloudflare-token"),
    ],
)
async def test_missing_selected_credentials_fail_without_execution(
    deployment, scope, missing, message
):
    arguments = deploy_arguments(deployment, scope)
    arguments.pop(missing)

    result = await deployment.module.deploy(**arguments)

    assert "Failed" in result
    assert message in result
    assert GUIDANCE not in result
    deployment.generate_unifi.assert_not_awaited()
    deployment.generate_cloudflare.assert_not_awaited()
    deployment.dag.container.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("scope", ["full", "cloudflare"])
@pytest.mark.parametrize("storage", ["local", "s3", "gcs", "persistent"])
async def test_success_guidance_reflects_parameters_and_storage(deployment, scope, storage):
    arguments = deploy_arguments(deployment, scope)
    backend = Mock(spec=dagger.File)
    backend.contents = AsyncMock(return_value='bucket = "state"\naccess_key = "SENTINEL_BACKEND"')
    state = Mock(spec=dagger.Directory)
    if storage in ("s3", "gcs"):
        arguments.update(backend_type=storage, backend_config_file=backend)
    elif storage == "persistent":
        arguments["state_dir"] = state

    result = await deployment.module.deploy(**arguments)

    assert "completed successfully" in result
    assert f"{'-' * 60}\n{GUIDANCE}\n{'-' * 60}" in result
    assert "Option 1: Using Dagger (recommended):" in result
    assert "dagger call get-tunnel-secrets \\\n" in result
    assert "    --source='<kcl-source>' \\\n" in result
    assert "Replace the quoted path placeholders" in result
    assert "Reuse the same source" in result
    assert "original host paths are unavailable" in result
    assert "--source=./kcl" not in result
    assert "--source=. " not in result
    assert "./backend.hcl" not in result
    assert "./terraform-state" not in result
    assert "--cloudflare-account-id=account-actual-123" in result
    assert "--zone-name=actual.example.test" in result
    assert "--cloudflare-token=env:CF_TOKEN" in result
    assert "Option 2: Install cloudflared service directly:" in result
    assert "cloudflared service install <tunnel-token-from-option-1>" in result
    assert "examples/homelab-media-stack/README.md" in result
    if storage in ("s3", "gcs"):
        assert f"--backend-type={storage}" in result
        assert "--backend-config-file='<backend-config-file>'" in result
        assert "--state-dir" not in result
        deployment.container.with_mounted_secret.assert_called_once_with(
            BACKEND_SECRET_PATH,
            deployment.dag.set_secret.return_value,
            owner="root",
            mode=0o600,
        )
        deployment.container.with_exec.assert_any_call(
            ["terraform", "init", f"-backend-config={BACKEND_SECRET_PATH}"]
        )
    else:
        assert "--backend-type" not in result
        assert "--backend-config-file" not in result
        deployment.container.with_mounted_secret.assert_not_called()
    if storage == "persistent":
        assert "--state-dir='<state-dir>'" in result
        deployment.container.with_directory.assert_any_call("/state", state)
        deployment.container.with_workdir.assert_called_once_with("/state")
    else:
        assert "--state-dir" not in result
    assert RAW_OUTPUT not in result
    assert "SENTINEL_BACKEND" not in result
    assert "SENTINEL_CF_TOKEN" not in result
    assert "SENTINEL_UNIFI_KEY" not in result
    deployment.cf_token.plaintext.assert_not_awaited()
    deployment.unifi_key.plaintext.assert_not_awaited()
    assert all(
        "output" not in invocation.args[0]
        for invocation in deployment.container.with_exec.call_args_list
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("scope", ["full", "cloudflare", "unifi"])
@pytest.mark.parametrize("failure_phase", ["init", "apply"])
async def test_terraform_failure_omits_guidance_and_raw_error_output(
    deployment, scope, failure_phase
):
    failure = dagger.ExecError(
        [
            QueryErrorValue(
                "SENTINEL_EXCEPTION",
                extensions={
                    "_type": "EXEC_ERROR",
                    "cmd": ["terraform", failure_phase],
                    "exitCode": 17,
                    "stdout": RAW_OUTPUT,
                    "stderr": "SENTINEL_STDERR",
                },
            )
        ],
        Mock(document=None),
    )
    deployment.container.stdout.side_effect = (
        [failure] if failure_phase == "init" else ["Init complete", failure]
    )

    result = await deployment.module.deploy(**deploy_arguments(deployment, scope))

    assert "Failed" in result
    assert f"Terraform {failure_phase}" in result
    assert "exit code 17" in result
    assert GUIDANCE not in result
    assert "completed successfully" not in result
    assert "SENTINEL" not in result
    assert "raw-state" not in result
    expected = [call(["terraform", "init"])]
    if failure_phase == "apply":
        expected.append(call(["terraform", "apply", "-auto-approve"]))
    assert deployment.container.with_exec.call_args_list == expected


@pytest.mark.asyncio
@pytest.mark.parametrize("provider", ["unifi", "cloudflare"])
async def test_generation_failure_omits_guidance_and_prevents_terraform(deployment, provider):
    getattr(deployment, f"generate_{provider}").side_effect = ValueError("invalid generated config")

    result = await deployment.module.deploy(**deploy_arguments(deployment, "full"))

    assert "Could not generate" in result
    assert "invalid generated config" in result
    assert GUIDANCE not in result
    deployment.dag.container.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_storage", ["missing-config", "remote-and-state"])
async def test_invalid_backend_or_state_omits_guidance_and_prevents_terraform(
    deployment, invalid_storage
):
    arguments = deploy_arguments(deployment, "cloudflare")
    arguments["backend_type"] = "s3"
    if invalid_storage == "remote-and-state":
        arguments.update(
            backend_config_file=Mock(spec=dagger.File), state_dir=Mock(spec=dagger.Directory)
        )

    result = await deployment.module.deploy(**arguments)

    assert "Failed" in result
    assert GUIDANCE not in result
    deployment.dag.container.assert_not_called()


@pytest.mark.asyncio
async def test_unreadable_backend_omits_guidance_and_sensitive_error(deployment):
    backend = Mock(spec=dagger.File)
    backend.contents = AsyncMock(side_effect=RuntimeError("SENTINEL_BACKEND_FAILURE"))

    result = await deployment.module.deploy(
        **deploy_arguments(deployment, "cloudflare"),
        backend_type="s3",
        backend_config_file=backend,
    )

    assert "Failed" in result
    assert "Backend configuration processing" in result
    assert GUIDANCE not in result
    assert "SENTINEL" not in result
    deployment.container.with_exec.assert_not_called()
