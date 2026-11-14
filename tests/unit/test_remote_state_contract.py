"""Public effect entry points fail before touching state or infrastructure."""

import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from main import UnifiCloudflareGlue

implementation = sys.modules[UnifiCloudflareGlue.__module__]


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["deploy", "destroy"])
@pytest.mark.parametrize("local_input", [False, True])
async def test_local_effects_rejected_before_generation_or_container_dispatch(
    operation, local_input
):
    module = UnifiCloudflareGlue()
    source = Mock(name="configuration-source")
    state = Mock(name="local-state") if local_input else None
    with (
        patch.object(implementation.dagger, "dag", new=Mock()) as dag,
        patch.object(module, "generate_unifi_config", new=AsyncMock()) as unifi,
        patch.object(module, "generate_cloudflare_config", new=AsyncMock()) as cloudflare,
        patch.object(implementation, "_generate_configs", new=AsyncMock()) as generate,
    ):
        with pytest.raises(ValueError, match="explicit remote backend"):
            await getattr(module, operation)(kcl_source=source, state_dir=state)
        assert not dag.mock_calls
        unifi.assert_not_called()
        cloudflare.assert_not_called()
        generate.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["deploy", "destroy"])
async def test_remote_and_local_state_rejected_before_dispatch(operation):
    with patch.object(implementation.dagger, "dag", new=Mock()) as dag:
        with pytest.raises(ValueError, match="Cannot use both"):
            await getattr(UnifiCloudflareGlue(), operation)(
                kcl_source=Mock(), backend_type="s3", state_dir=Mock()
            )
        assert not dag.mock_calls


def test_local_preview_input_is_not_authorization_for_effects():
    module = UnifiCloudflareGlue()
    state = Mock()
    assert module._validate_state_storage_config("local", state) == (True, "")
    allowed, error = module._validate_state_storage_config("local", state, for_effects=True)
    assert not allowed
    assert "DLR-1" in error
    assert "does not write back" in error
