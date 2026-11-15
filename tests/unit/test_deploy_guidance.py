"""Public execution contracts tested against an immutable synthetic Dagger graph."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import dagger
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src/main"))

from main import UnifiCloudflareGlue

RAW_OUTPUT = 'CANARY_PROVIDER_OUTPUT {"resources": ["raw-state"]}'


class Graph:
    """Every graph change produces a child; dependent execs must retain ancestry."""

    def __init__(self, calls, history=(), failure=None):
        self.calls = calls
        self.history = history
        self.failure = failure

    def __getattr__(self, method):
        if method in {
            "from_",
            "with_directory",
            "with_new_file",
            "with_file",
            "with_workdir",
            "with_secret_variable",
            "with_env_variable",
        }:

            def change(*args, **kwargs):
                return Graph(self.calls, (*self.history, (method, args, kwargs)), self.failure)

            return change
        raise AttributeError(method)

    def with_exec(self, argv, **kwargs):
        self.calls.append((list(argv), self.history, kwargs))
        return Graph(self.calls, (*self.history, ("exec", list(argv), kwargs)), self.failure)

    async def stdout(self):
        last = [item for item in self.history if item[0] == "exec"][-1]
        if last[1][0] == "python":
            return json.dumps({"add": 1, "change": 1, "destroy": 1, "replace": 1})
        if self.failure == "timeout" and last[1][1] == "apply":
            raise TimeoutError("CANARY_TIMEOUT")
        if self.failure and last[1][1] == self.failure:
            if last[2].get("expect") == dagger.ReturnType.ANY:
                return RAW_OUTPUT
            error = RuntimeError(RAW_OUTPUT)
            error.exit_code = 17
            raise error
        return RAW_OUTPUT

    async def exit_code(self):
        last = [item for item in self.history if item[0] == "exec"][-1]
        return 17 if last[1][1] == self.failure else 0

    def file(self, path):
        file = Mock(spec=dagger.File)
        file.sync = AsyncMock(return_value=file)
        file.contents = AsyncMock(
            return_value=json.dumps(
                {
                    "resource_changes": [
                        {"change": {"actions": ["delete", "create"]}},
                        {"change": {"actions": ["update"]}},
                    ]
                }
            )
        )
        return file


@pytest.fixture
def deployment():
    calls = []
    graph = Graph(calls)
    directories = []

    def new_directory():
        directory = Mock(spec=dagger.Directory)
        directory.with_file.return_value = directory
        directory.with_new_file.return_value = directory
        directories.append(directory)
        return directory

    source = Mock(spec=dagger.Directory)
    secret = Mock(spec=dagger.Secret)
    secret.plaintext = AsyncMock(return_value="CANARY_SECRET")
    generated = {"unifi": Mock(spec=dagger.File), "cloudflare": Mock(spec=dagger.File)}
    with (
        patch("main.dagger.dag", new=Mock()) as dag,
        patch("main._generate_configs", new=AsyncMock(return_value=generated)) as generation,
        patch("main.prepare_root", return_value=(graph, "/module/glue")) as prepare,
        patch(
            "main._with_backend_secret", new=AsyncMock(side_effect=lambda ctr, *_: ctr)
        ) as backend,
    ):
        dag.directory.side_effect = new_directory
        yield SimpleNamespace(
            module=UnifiCloudflareGlue(),
            calls=calls,
            graph=graph,
            source=source,
            secret=secret,
            prepare=prepare,
            backend=backend,
            generation=generation,
            dag=dag,
            directories=directories,
        )


def arguments(case, scope="full"):
    result = dict(
        kcl_source=case.source,
        state_scope=scope,
        backend_type="s3",
        backend_config_file=case.secret,
        backend_config_format="hcl",
    )
    if scope != "cloudflare":
        result.update(unifi_url="https://unifi.example.test:8443", unifi_api_key=case.secret)
    if scope != "unifi":
        result.update(
            cloudflare_token=case.secret,
            cloudflare_account_id="account-actual-123",
            zone_name="actual.example.test",
        )
    result.update(unifi_only=scope == "unifi", cloudflare_only=scope == "cloudflare")
    return result


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["deploy", "destroy", "plan"])
@pytest.mark.parametrize(
    "scope,root", [("full", "glue"), ("unifi", "unifi-dns"), ("cloudflare", "cloudflare-tunnel")]
)
async def test_public_operations_share_roots_and_preserve_initialization(
    deployment, operation, scope, root
):
    result = await getattr(deployment.module, operation)(**arguments(deployment, scope))
    assert deployment.prepare.call_args.args[2:] == (root, "s3")
    assert deployment.backend.call_args.args[1:] == (deployment.secret, "hcl")
    providers = ("unifi", "cloudflare") if scope == "full" else (scope,)
    deployment.generation.assert_awaited_once_with(deployment.source, "0.12.4", providers)
    commands = [call[0] for call in deployment.calls]
    assert commands[0][0:2] == ["terraform", "init"]
    assert commands[1][0:2] == ["terraform", "apply" if operation == "deploy" else operation]
    assert any(item[0] == "exec" and item[1] == commands[0] for item in deployment.calls[1][1])
    assert all(command[0] in {"terraform", "python"} for command in commands)
    if operation == "plan":
        assert commands[-1][0] == "python"
        assert "plan_counts" in commands[-1][-1]
    if operation != "plan":
        assert "successfully" in result
        assert RAW_OUTPUT not in result
        assert "CANARY_SECRET" not in result
    else:
        output = deployment.directories[-1]
        assert result is output
        files = {c.args[0] for c in output.with_file.call_args_list}
        assert files == {"plan.txt"}
        summary = output.with_new_file.call_args.args[1]
        assert "Resources to add:     1" in summary
        assert "Resources to change:  1" in summary
        assert "Resources to destroy: 1" in summary
        assert "requires separate authorization" in summary
        assert "CANARY" not in summary
    deployment.secret.plaintext.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["deploy", "destroy", "plan"])
@pytest.mark.parametrize("label", ["x\nterraform destroy", "$(id)", ";echo bad", "x" * 81])
async def test_invalid_labels_fail_before_generation_or_provider_access(
    deployment, operation, label
):
    with pytest.raises(ValueError, match="run label"):
        await getattr(deployment.module, operation)(**arguments(deployment), cache_buster=label)
    deployment.prepare.assert_not_called()
    deployment.generation.assert_not_awaited()
    assert deployment.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["deploy", "destroy", "plan"])
async def test_incompatible_state_root_fails_before_backend_access(deployment, operation):
    args = arguments(deployment, "unifi")
    args["state_scope"] = "full"
    with pytest.raises(ValueError, match="incompatible"):
        await getattr(deployment.module, operation)(**args)
    deployment.prepare.assert_not_called()
    deployment.generation.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["deploy", "destroy", "plan"])
@pytest.mark.parametrize("phase", ["init", "effect"])
async def test_failure_is_nonzero_sanitized_and_stops_dependents(deployment, operation, phase):
    failed = "init" if phase == "init" else "apply" if operation == "deploy" else operation
    deployment.prepare.return_value = (Graph(deployment.calls, failure=failed), "/module/glue")
    with pytest.raises(RuntimeError) as captured:
        await getattr(deployment.module, operation)(**arguments(deployment))
    assert "exit code 17" in str(captured.value)
    assert "CANARY" not in str(captured.value)
    assert "raw-state" not in str(captured.value)
    assert captured.value.__suppress_context__
    assert len(deployment.calls) == (1 if phase == "init" else 2)


@pytest.mark.asyncio
async def test_repeated_identical_deployments_have_independent_live_nonces(deployment):
    await deployment.module.deploy(**arguments(deployment))
    await deployment.module.deploy(**arguments(deployment))
    nonces = [
        next(
            item[1][1]
            for item in reversed(history)
            if item[0] == "with_env_variable" and item[1][0] == "EXECUTION_NONCE"
        )
        for _, history, _ in deployment.calls
    ]
    assert len(nonces) == 4
    assert len(set(nonces)) == 4
    assert all(call.args[0] is deployment.source for call in deployment.generation.call_args_list)
    deployment.source.with_new_file.assert_not_called()


@pytest.mark.asyncio
async def test_generation_failure_prevents_all_terraform_work(deployment):
    deployment.generation.side_effect = RuntimeError("CANARY_GENERATION_ERROR")
    with pytest.raises(RuntimeError, match="Configuration generation") as captured:
        await deployment.module.deploy(**arguments(deployment))
    assert "CANARY" not in str(captured.value)
    deployment.prepare.assert_not_called()


@pytest.mark.asyncio
async def test_selected_credentials_required_before_generation(deployment):
    args = arguments(deployment)
    args.pop("cloudflare_token")
    with pytest.raises(ValueError, match="--cloudflare-token"):
        await deployment.module.deploy(**args)
    deployment.generation.assert_not_awaited()
    deployment.prepare.assert_not_called()


@pytest.mark.asyncio
async def test_credentials_are_not_default_string_outputs(deployment):
    with pytest.raises(ValueError, match="protected-disclosure acknowledgement"):
        await deployment.module.get_tunnel_secrets(
            source=deployment.source,
            cloudflare_token=deployment.secret,
            cloudflare_account_id="account",
            zone_name="example.test",
        )
    deployment.dag.container.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "failure", [None, "apply", "timeout", "credential-schema", "credential-timeout"]
)
async def test_disposable_integration_preserves_init_state_and_never_replays_unknown_effects(
    deployment, failure
):
    deployment.dag.container.return_value = Graph(deployment.calls, failure=failure)

    artifact = Mock(spec=dagger.Directory)
    artifact.file.return_value.contents = AsyncMock(
        side_effect=AssertionError("Raw credential read forbidden")
    )
    summary = {
        "count": 1,
        "ids_valid": True,
        "tokens_valid": True,
        "credentials_valid": True,
        "format_valid": True,
        "permissions_valid": True,
    }
    verifier = AsyncMock(return_value=summary)
    if failure == "credential-schema":
        verifier.side_effect = ValueError("CANARY_GENERATED_TOKEN invalid schema")
    elif failure == "credential-timeout":
        verifier.side_effect = TimeoutError("CANARY_GENERATED_SECRET deadline")

    with (
        patch.object(UnifiCloudflareGlue, "_generate_test_id", return_value="test-abc12"),
        patch.object(
            UnifiCloudflareGlue, "get_tunnel_secrets", new=AsyncMock(return_value=artifact)
        ) as retrieval,
        patch("main.verify_tunnel_artifact", new=verifier),
        patch("main.terraform_runtime", return_value=deployment.graph),
        patch.object(
            UnifiCloudflareGlue,
            "_cloudflare_resource_counts",
            new=AsyncMock(side_effect=[(1, 1), (0, 0)]),
        ),
        patch.object(
            UnifiCloudflareGlue, "_unifi_dns_exists", new=AsyncMock(side_effect=[True, False])
        ),
    ):
        invocation = deployment.module.test_integration(
            source=deployment.source,
            cloudflare_zone="example.test",
            cloudflare_token=deployment.secret,
            cloudflare_account_id="account",
            unifi_url="https://unifi.test",
            api_url="https://unifi.test",
            unifi_api_key=deployment.secret,
        )
        if failure:
            with pytest.raises(RuntimeError) as error:
                await invocation
            result = str(error.value)
            assert (
                "outcome unknown"
                if failure == "timeout"
                else (
                    "secrets_retrieval=failed"
                    if failure.startswith("credential-")
                    else "exit code 17"
                )
            ) in result
        else:
            result = await invocation
            assert "ALL RESOURCES VALIDATED" in result
        assert "CANARY" not in result
        artifact.file.return_value.contents.assert_not_awaited()
        for call in retrieval.call_args_list:
            assert call.kwargs["protected_disclosure"] is True
        if failure is None:
            assert [call.args[2] for call in verifier.call_args_list] == ["json", "human"]
    effects = [
        (argv, history) for argv, history, _ in deployment.calls if argv[1] in {"apply", "destroy"}
    ]
    for argv, history in effects:
        assert any(item[0] == "exec" and item[1][1] == "init" for item in history)
    commands = [argv[1] for argv, _ in effects]
    if failure == "timeout":
        assert commands == ["apply"]
    elif failure == "apply":
        assert commands == ["apply", "destroy"]
    else:
        assert commands == ["apply", "apply", "destroy", "destroy"]
