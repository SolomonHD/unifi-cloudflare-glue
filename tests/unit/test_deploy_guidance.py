"""Unit tests for deployment success message guidance.

This module tests that deploy_cloudflare() and deploy() functions
include proper tunnel token retrieval guidance in their success messages.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "main"))

from main import UnifiCloudflareGlue


class TestDeployCloudflareGuidance:
    """Test suite for deploy_cloudflare() success message guidance."""

    @pytest.fixture
    def module(self):
        """Create a fresh module instance for each test."""
        return UnifiCloudflareGlue()

    @pytest.fixture
    def mock_secret(self):
        """Create a mock Secret object."""
        secret = Mock()
        secret.plaintext = AsyncMock(return_value="mock-token-value")
        return secret

    @pytest.fixture
    def mock_directory(self):
        """Create a mock Directory object."""
        mock_dir = Mock()
        mock_dir.file = Mock(return_value=Mock())
        mock_dir.file.return_value.contents = AsyncMock(return_value="{}")
        return mock_dir

    @pytest.mark.asyncio
    async def test_success_message_contains_guidance_header(self, module, mock_secret, mock_directory):
        """Test that success message includes 'Next Step: Retrieve Tunnel Credentials' header."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            assert "Next Step: Retrieve Tunnel Credentials" in result
            assert "✓ Success" in result

    @pytest.mark.asyncio
    async def test_success_message_contains_dagger_command(self, module, mock_secret, mock_directory):
        """Test that success message includes 'dagger call get-tunnel-secrets' command."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            assert "dagger call get-tunnel-secrets" in result

    @pytest.mark.asyncio
    async def test_success_message_contains_actual_parameters(self, module, mock_secret, mock_directory):
        """Test that success message uses actual deployment parameters in command."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="my-account-123",
                zone_name="myzone.com",
            )

            assert "--cloudflare-account-id=my-account-123" in result
            assert "--zone-name=myzone.com" in result

    @pytest.mark.asyncio
    async def test_local_backend_shows_source_flag(self, module, mock_secret, mock_directory):
        """Test that local backend command includes --source flag."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
                backend_type="local",
            )

            assert "--source=." in result

    @pytest.mark.asyncio
    async def test_remote_backend_shows_backend_flags(self, module, mock_secret, mock_directory):
        """Test that remote backend command includes backend-specific flags."""
        mock_backend_file = Mock()

        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_new_file = Mock(return_value=mock_container)
            mock_container.with_file = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
                backend_type="s3",
                backend_config_file=mock_backend_file,
            )

            assert "--backend-type=s3" in result
            assert "--backend-config-file=./backend.hcl" in result

    @pytest.mark.asyncio
    async def test_persistent_state_shows_state_dir_flag(self, module, mock_secret, mock_directory):
        """Test that persistent state command includes --state-dir flag."""
        mock_state_dir = Mock()

        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
                state_dir=mock_state_dir,
            )

            assert "--state-dir=./terraform-state" in result

    @pytest.mark.asyncio
    async def test_success_message_contains_terraform_output_command(self, module, mock_secret, mock_directory):
        """Test that success message includes terraform output command option."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            assert "terraform output -json cloudflare_tunnel_tokens" in result

    @pytest.mark.asyncio
    async def test_success_message_contains_cloudflared_install_command(self, module, mock_secret, mock_directory):
        """Test that success message includes cloudflared service install example."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            assert "cloudflared service install" in result

    @pytest.mark.asyncio
    async def test_success_message_contains_example_documentation_link(self, module, mock_secret, mock_directory):
        """Test that success message includes link to example documentation."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            assert "examples/homelab-media-stack/README.md" in result

    @pytest.mark.asyncio
    async def test_failure_message_does_not_contain_guidance(self, module, mock_secret, mock_directory):
        """Test that failure message does NOT include tunnel token guidance."""
        import dagger

        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            # Make init succeed but apply fail
            mock_container.with_exec = Mock(side_effect=[
                Mock(stdout=AsyncMock(return_value="Init complete!")),
                Mock(stdout=AsyncMock(side_effect=dagger.ExecError("apply failed", 1, "", ""))),
            ])

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            assert "✗ Failed" in result
            assert "Next Step: Retrieve Tunnel Credentials" not in result


class TestDeployGuidance:
    """Test suite for deploy() success message guidance."""

    @pytest.fixture
    def module(self):
        """Create a fresh module instance for each test."""
        return UnifiCloudflareGlue()

    @pytest.fixture
    def mock_secret(self):
        """Create a mock Secret object."""
        secret = Mock()
        secret.plaintext = AsyncMock(return_value="mock-token-value")
        return secret

    @pytest.fixture
    def mock_directory(self):
        """Create a mock Directory object."""
        mock_dir = Mock()
        mock_dir.file = Mock(return_value=Mock())
        mock_dir.file.return_value.contents = AsyncMock(return_value="{}")
        mock_dir.entries = AsyncMock(return_value=[])
        return mock_dir
    @pytest.mark.asyncio
    async def test_both_success_shows_guidance(self, module, mock_secret, mock_directory):
        """Test that guidance appears when both UniFi and Cloudflare succeed."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_new_file = Mock(return_value=mock_container)
            mock_container.with_file = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")
            mock_container.file = Mock(return_value=mock_directory.file())

            result = await module.deploy(
                kcl_source=mock_directory,
                unifi_url="https://unifi.local:8443",
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
                unifi_api_key=mock_secret,
            )

            assert "✓ Both deployments completed successfully" in result
            assert "Next Step: Retrieve Tunnel Credentials" in result
            assert "dagger call get-tunnel-secrets" in result

    @pytest.mark.asyncio
    async def test_guidance_uses_kcl_source_directory(self, module, mock_secret, mock_directory):
        """Test that deploy() guidance uses --source=./kcl for KCL-generated configs."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_new_file = Mock(return_value=mock_container)
            mock_container.with_file = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")
            mock_container.file = Mock(return_value=mock_directory.file())

            result = await module.deploy(
                kcl_source=mock_directory,
                unifi_url="https://unifi.local:8443",
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
                unifi_api_key=mock_secret,
            )

            # deploy() uses --source=./kcl for KCL-generated configs
            assert "--source=./kcl" in result

    @pytest.mark.asyncio
    async def test_unifi_success_only_no_guidance(self, module, mock_secret, mock_directory):
        """Test that guidance does NOT appear when only UniFi succeeds."""
        import dagger

        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_new_file = Mock(return_value=mock_container)
            mock_container.with_file = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            # First 4 calls: UniFi success (init + apply), then Cloudflare init
            # 5th call: Cloudflare apply fails
            exec_results = [
                Mock(stdout=AsyncMock(return_value="Init complete!")),  # UniFi init
                Mock(stdout=AsyncMock(return_value="Apply complete!")),  # UniFi apply
                Mock(stdout=AsyncMock(return_value="Init complete!")),  # CF init
                Mock(stdout=AsyncMock(side_effect=dagger.ExecError("apply failed", 1, "", ""))),  # CF apply fails
            ]
            mock_container.with_exec = Mock(side_effect=exec_results)
            mock_container.file = Mock(return_value=mock_directory.file())

            result = await module.deploy(
                kcl_source=mock_directory,
                unifi_url="https://unifi.local:8443",
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
                unifi_api_key=mock_secret,
            )

            assert "○ UniFi: Success" in result or "UniFi: Success" in result
            assert "Cloudflare: Failed" in result
            assert "Next Step: Retrieve Tunnel Credentials" not in result


class TestVisualFormatting:
    """Test visual formatting of guidance sections."""

    @pytest.fixture
    def module(self):
        return UnifiCloudflareGlue()

    @pytest.fixture
    def mock_secret(self):
        secret = Mock()
        secret.plaintext = AsyncMock(return_value="mock-token")
        return secret

    @pytest.fixture
    def mock_directory(self):
        mock_dir = Mock()
        mock_dir.file = Mock(return_value=Mock())
        mock_dir.file.return_value.contents = AsyncMock(return_value="{}")
        return mock_dir

    @pytest.mark.asyncio
    async def test_separator_lines_present(self, module, mock_secret, mock_directory):
        """Test that separator lines (60 dashes) are present in guidance."""
        with patch("dagger.dag") as mock_dag:
            mock_container = Mock()
            mock_dag.container = Mock(return_value=mock_container)
            mock_dag.directory = Mock(return_value=mock_directory)
            mock_container.from_ = Mock(return_value=mock_container)
            mock_container.with_directory = Mock(return_value=mock_container)
            mock_container.with_env_variable = Mock(return_value=mock_container)
            mock_container.with_secret_variable = Mock(return_value=mock_container)
            mock_container.with_workdir = Mock(return_value=mock_container)
            mock_container.with_exec = Mock(return_value=mock_container)
            mock_container.stdout = AsyncMock(return_value="Apply complete!")

            result = await module.deploy_cloudflare(
                source=mock_directory,
                cloudflare_token=mock_secret,
                cloudflare_account_id="test-account-id",
                zone_name="example.com",
            )

            # Check for separator line (60 dashes)
            assert "-" * 60 in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
