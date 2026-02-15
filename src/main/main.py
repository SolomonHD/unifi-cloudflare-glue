"""Dagger module for unifi-cloudflare-glue.

This module provides containerized, reproducible pipelines for managing
hybrid DNS infrastructure bridging UniFi network DNS with Cloudflare Tunnel edge DNS.
"""

import asyncio
import dagger
from dagger import function, object_type, Secret, Doc, Directory
from typing import Annotated, Optional
import random
import string
import json
import shlex
import time

from .backend_config import process_backend_config_content


async def _process_backend_config(backend_config_file: dagger.File) -> tuple[str, str]:
    """
    Process a backend configuration file, converting YAML to HCL if necessary.
    
    Args:
        backend_config_file: File object containing backend configuration (YAML or HCL)
        
    Returns:
        Tuple of (content, extension) where content is the HCL-formatted backend config
        and extension is '.tfbackend' for mounting
    """
    try:
        # Get the file contents
        content = await backend_config_file.contents()
        return process_backend_config_content(content)
    except Exception:
        # If we can't read the file, return empty content
        return ("", '.tfbackend')


# Custom exception for KCL generation errors
class KCLGenerationError(Exception):
    """Raised when KCL configuration generation fails."""
    pass


@object_type
class UnifiCloudflareGlue:
    """UniFi Cloudflare Glue - Hybrid DNS infrastructure management."""

    @function
    async def hello(self, name: Annotated[str, Doc("Name to greet")] = "World") -> str:
        """Return a greeting message for verification."""
        return f"✓ Hello, {name}! from unifi-cloudflare-glue"

    @function
    async def version(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing VERSION file")],
    ) -> str:
        """
        Return the current version of unifi-cloudflare-glue.

        Reads the VERSION file from the source directory and returns the
        version string. All components (KCL, Terraform, Dagger) share
        the same version number.

        Args:
            source: Directory containing the VERSION file (use --source=.)

        Returns:
            Version string (e.g., "0.1.0")

        Example:
            dagger call version --source=.
        """
        try:
            version_file = source.file("VERSION")
            version_content = await version_file.contents()
            return version_content.strip()
        except Exception as e:
            return f"✗ Failed: Could not read VERSION file: {str(e)}"

    @function
    async def generate_unifi_config(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
    ) -> dagger.File:
        """
        Generate UniFi JSON configuration from KCL schemas.

        This function runs the KCL UniFi generator in a containerized environment
        and returns the generated JSON configuration as a File object.

        Args:
            source: Directory containing KCL module (must have kcl.mod)
            kcl_version: KCL version to use (default: "latest")

        Returns:
            dagger.File containing the generated UniFi JSON configuration

        Example:
            dagger call generate-unifi-config --source=./kcl export --path=./unifi.json
        """
        # Check for kcl.mod
        try:
            mod_file = source.file("kcl.mod")
            _ = await mod_file.contents()
        except Exception:
            raise KCLGenerationError(
                "✗ No kcl.mod found in source directory. "
                "Is this a valid KCL module?\n"
                "Hint: Run 'kcl mod init' in your KCL directory to create a module."
            )

        # Check for main.k entry point
        try:
            main_file = source.file("main.k")
            _ = await main_file.contents()
        except Exception:
            raise KCLGenerationError(
                "✗ Entry point file not found: main.k\n"
                "The module requires main.k as the entry point.\n"
                "Hint: Ensure your KCL module has a main.k file that exports unifi_output."
            )

        # Create container with KCL and yq for YAML to JSON conversion
        base_ctr = dagger.dag.container().from_(f"kcllang/kcl:{kcl_version}")
        
        # Install curl and yq for YAML to JSON conversion
        ctr = base_ctr.with_exec([
            "sh", "-c",
            "apt-get update && apt-get install -y curl && curl -sL https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -o /usr/local/bin/yq && chmod +x /usr/local/bin/yq"
        ])
        
        # Mount source directory
        ctr = ctr.with_directory("/src", source).with_workdir("/src")

        # Step 1: Download KCL dependencies to prevent git clone messages in output
        # This must be done before 'kcl run' to ensure clean YAML output
        try:
            ctr = ctr.with_exec(["kcl", "mod", "update"])
            await ctr.stdout()  # Wait for completion but don't capture output
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ Failed to download KCL dependencies:\n"
                f"Exit code: {e.exit_code}\n"
                f"Stderr: {e.stderr}\n"
                f"\nPossible causes:\n"
                f"  - Network connectivity issues\n"
                f"  - Invalid kcl.mod syntax\n"
                f"  - Git repository not accessible\n"
                f"\nSuggested fixes:\n"
                f"  - Check your network connection\n"
                f"  - Validate kcl.mod syntax with 'kcl mod graph' locally\n"
                f"  - Ensure git dependencies are accessible from this environment"
            )

        # Step 2: Run KCL main.k and capture full output
        try:
            ctr = ctr.with_exec(["kcl", "run", "main.k"])
            kcl_output = await ctr.stdout()
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ KCL execution failed:\n"
                f"Exit code: {e.exit_code}\n"
                f"Stdout: {e.stdout}\n"
                f"Stderr: {e.stderr}\n"
                f"\nHint: Check your KCL syntax with 'kcl run main.k' locally."
            )

        # Step 3: Check for validation errors in output
        # When KCL validation fails, generate_with_output() prints errors and returns no JSON
        if "✗" in kcl_output or "VALIDATION" in kcl_output:
            raise KCLGenerationError(
                f"✗ KCL validation failed:\n\n{kcl_output}\n"
                f"\nThe KCL configuration has validation errors that must be fixed.\n"
                f"See the error messages above for details on what needs to be corrected."
            )

        # Step 4: Validate empty output
        if not kcl_output or not kcl_output.strip():
            raise KCLGenerationError(
                "✗ KCL produced empty output:\n"
                "Possible causes:\n"
                "  - main.k is empty or has no output statements\n"
                "  - KCL module has no output statements\n"
                "  - All configurations are commented out\n"
                "\nHint: Run 'kcl run main.k' locally to see the raw output."
            )

        # Step 5: Write KCL output to temporary file for yq extraction
        ctr = ctr.with_new_file("/tmp/kcl-output.yaml", kcl_output)

        # Step 6: Extract unifi_output section using yq
        try:
            ctr = ctr.with_exec(["yq", "eval", ".unifi_output", "/tmp/kcl-output.yaml"])
            unifi_yaml = await ctr.stdout()
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ Failed to extract unifi_output from YAML:\n"
                f"yq error: {e.stderr}\n"
                f"\nHint: Ensure your main.k exports 'unifi_output' as a public variable."
            )

        # Step 7: Check for null output (missing key)
        if not unifi_yaml or unifi_yaml.strip() == "null" or not unifi_yaml.strip():
            raise KCLGenerationError(
                "✗ main.k does not export 'unifi_output':\n"
                "The main.k file must export a public variable named 'unifi_output'.\n"
                "\nExample:\n"
                "  import unifi_cloudflare_glue.generators.unifi as unifi_gen\n"
                "  unifi_output = unifi_gen.generate_with_output(config)\n"
                "\nHint: Run 'kcl run main.k' locally to inspect the output structure."
            )

        # Step 8: Convert extracted YAML to JSON
        ctr = ctr.with_new_file("/tmp/unifi-output.yaml", unifi_yaml)
        try:
            ctr = ctr.with_exec(["yq", "eval", "-o=json", "/tmp/unifi-output.yaml"])
            json_result = await ctr.stdout()
        except dagger.ExecError as e:
            # Truncate output to 1000 characters for error display
            truncated_output = unifi_yaml[:1000] if len(unifi_yaml) > 1000 else unifi_yaml
            ellipsis_indicator = "... (truncated)" if len(unifi_yaml) > 1000 else ""
            raise KCLGenerationError(
                f"✗ YAML to JSON conversion failed:\n"
                f"yq error: {e.stderr}\n"
                f"\nExtracted unifi_output that failed to parse:\n"
                f"{'-' * 60}\n"
                f"{truncated_output}{ellipsis_indicator}\n"
                f"{'-' * 60}\n"
                f"\nPossible causes:\n"
                f"  - KCL validation warnings in output\n"
                f"  - Invalid YAML structure in unifi_output\n"
                f"  - KCL syntax errors that produced partial output\n"
                f"\nHint: Run 'kcl run main.k' locally to see the raw output."
            )

        # Step 9: Validate JSON output
        try:
            json.loads(json_result)
        except json.JSONDecodeError as je:
            # Truncate JSON result to 500 characters for error display
            truncated_json = json_result[:500] if len(json_result) > 500 else json_result
            json_ellipsis = "... (truncated)" if len(json_result) > 500 else ""
            raise KCLGenerationError(
                f"✗ Invalid JSON output after yq conversion:\n"
                f"JSON parse error: {str(je)}\n"
                f"\nInvalid output preview:\n"
                f"{'-' * 60}\n"
                f"{truncated_json}{json_ellipsis}\n"
                f"{'-' * 60}\n"
                f"\nHint: This may indicate a bug in yq or unexpected KCL output format."
            )

        # Step 10: Return as file
        return dagger.dag.directory().with_new_file("unifi.json", json_result).file("unifi.json")

    def _validate_backend_config(
        self,
        backend_type: str,
        backend_config_file: Optional[dagger.File],
    ) -> tuple[bool, str]:
        """
        Validate backend configuration parameters.
        
        Args:
            backend_type: Type of backend (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Optional File object containing backend configuration
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Non-local backend requires config file
        if backend_type != "local" and backend_config_file is None:
            return False, (
                f"✗ Failed: Backend type '{backend_type}' requires --backend-config-file\n\n"
                f"Example:\n"
                f"  dagger call deploy-unifi \\\n"
                f"      --backend-type={backend_type} \\\n"
                f"      --backend-config-file=./{backend_type}-backend.hcl \\\n"
                f"      ..."
            )
        
        # Config file provided but local backend selected
        if backend_type == "local" and backend_config_file is not None:
            return False, (
                "✗ Failed: --backend-config-file specified but backend_type is 'local'\n\n"
                "To use a remote backend, set --backend-type to one of:\n"
                "  s3, azurerm, gcs, remote, consul, http, etc.\n\n"
                "To use local backend without config file:\n"
                "  Omit --backend-config-file or set --backend-type=local"
            )
        
        return True, ""

    def _validate_state_storage_config(
        self,
        backend_type: str,
        state_dir: Optional[dagger.Directory],
    ) -> tuple[bool, str]:
        """
        Validate mutual exclusion between remote backend and persistent local state directory.
        
        Args:
            backend_type: Type of backend (local, s3, azurerm, gcs, remote, etc.)
            state_dir: Optional Directory for persistent local state storage
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for mutual exclusion between remote backend and state_dir
        if backend_type != "local" and state_dir is not None:
            return False, (
                "✗ Failed: Cannot use both --state-dir and --backend-type (remote backend).\n\n"
                "These options are mutually exclusive. Choose one state management mode:\n\n"
                "1. Ephemeral state (default - no flags):\n"
                "   dagger call deploy-unifi \\\n"
                "       --source=. \\\n"
                "       --unifi-url=https://unifi.local:8443 \\\n"
                "       --unifi-api-key=env:UNIFI_API_KEY\n\n"
                "2. Persistent local state (--state-dir):\n"
                "   dagger call deploy-unifi \\\n"
                "       --source=. \\\n"
                "       --unifi-url=https://unifi.local:8443 \\\n"
                "       --unifi-api-key=env:UNIFI_API_KEY \\\n"
                "       --state-dir=./terraform-state\n\n"
                "3. Remote backend (--backend-type):\n"
                "   dagger call deploy-unifi \\\n"
                "       --source=. \\\n"
                "       --unifi-url=https://unifi.local:8443 \\\n"
                "       --unifi-api-key=env:UNIFI_API_KEY \\\n"
                "       --backend-type=s3 \\\n"
                "       --backend-config-file=./s3-backend.hcl"
            )
        
        return True, ""

    def _generate_backend_block(self, backend_type: str) -> str:
        """
        Generate backend.tf content for remote backends.
        
        Args:
            backend_type: Type of backend (s3, azurerm, gcs, remote, etc.)
            
        Returns:
            HCL content for backend.tf file
        """
        return f'''terraform {{
  backend "{backend_type}" {{}}
}}
'''

    @function
    async def deploy_unifi(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing unifi.json")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL (e.g., https://unifi.local:8443)")],
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username (use with password)")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password (use with username)")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller (useful for self-signed certificates)")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
    ) -> str:
        """
        Deploy UniFi DNS configuration using Terraform.

        This function runs Terraform to deploy UniFi DNS records from the generated
        unifi.json configuration. Supports both API key and username/password authentication.

        Authentication (pick one method):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            source: Directory containing unifi.json configuration file
            unifi_url: UniFi Controller URL
            api_url: Optional UniFi API URL (defaults to unifi_url)
            unifi_api_key: UniFi API key for authentication
            unifi_username: UniFi username for authentication
            unifi_password: UniFi password for authentication
            unifi_insecure: Skip TLS verification for self-signed certificates
            terraform_version: Terraform version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)

        Returns:
            Status message indicating success or failure of deployment

        Example:
            dagger call deploy-unifi \\
                --source=. \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY

            # With insecure TLS (for self-signed certificates)
            dagger call deploy-unifi \\
                --source=. \\
                --unifi-url=https://192.168.10.1 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-insecure

            # With persistent local state
            dagger call deploy-unifi \\
                --source=. \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --state-dir=./terraform-state
        """
        # Validate authentication - either API key OR username/password, not both
        using_api_key = unifi_api_key is not None
        using_password = unifi_username is not None and unifi_password is not None

        if not using_api_key and not using_password:
            return "✗ Failed: Must provide either unifi_api_key OR both unifi_username and unifi_password"

        if using_api_key and using_password:
            return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."

        # Validate backend configuration
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            return error_msg

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            return error_msg

        # Use unifi_url as default for api_url if not provided
        actual_api_url = api_url if api_url else unifi_url

        # Check for unifi.json
        try:
            config_file = source.file("unifi.json")
            _ = await config_file.contents()
        except Exception:
            return "✗ Failed: unifi.json not found in source directory. Run generate-unifi-config first."

        # Create Terraform container
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

        # Mount source directory with unifi.json
        ctr = ctr.with_directory("/workspace", source)

        # Mount the UniFi DNS Terraform module
        try:
            tf_module = dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        # Generate and mount backend.tf if using remote backend
        if backend_type != "local":
            try:
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file("/module/backend.tf", backend_hcl)
            except Exception as e:
                return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                # Convert YAML to HCL if necessary
                config_content, _ = await _process_backend_config(backend_config_file)
                # Mount the processed content as a .tfbackend file
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
            except Exception as e:
                return f"✗ Failed: Could not process backend config file\n{str(e)}"

        # Set up environment variables for Terraform
        ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
        ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
        ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())

        # Add authentication secrets via environment variables
        if using_api_key and unifi_api_key:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
        elif using_password and unifi_username and unifi_password:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
            ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

        # Handle state directory mounting and setup (persistent local state)
        using_persistent_state = state_dir is not None
        if using_persistent_state:
            # Mount state directory
            ctr = ctr.with_directory("/state", state_dir)
            # Copy module files to state directory
            ctr = ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
            # Set working directory to state directory
            ctr = ctr.with_workdir("/state")
        else:
            # Set working directory to the module (ephemeral or remote backend)
            ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        # Run terraform init (with backend config if provided)
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])
        
        try:
            init_result = await ctr.with_exec(init_cmd).stdout()
        except dagger.ExecError as e:
            error_msg = f"✗ Failed: Terraform init failed\n{str(e)}"
            if backend_type != "local":
                error_msg += (
                    "\n\nBackend configuration troubleshooting:\n"
                    "  - Verify backend config file is valid HCL\n"
                    "  - Check credentials in environment variables\n"
                    "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                )
            return error_msg

        # Run terraform apply
        try:
            apply_result = await ctr.with_exec([
                "terraform", "apply", "-auto-approve"
            ]).stdout()
            
            result_msg = "✓ Success: UniFi DNS deployment completed"
            if backend_type != "local":
                result_msg += f"\n  Backend: {backend_type}"
            elif using_persistent_state:
                result_msg += "\n  State: Persistent local (mounted state directory)"
            result_msg += f"\n\n{apply_result}"
            return result_msg
        except dagger.ExecError as e:
            return f"✗ Failed: Terraform apply failed\n{str(e)}"

    @function
    async def deploy_cloudflare(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing cloudflare.json")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
        zone_name: Annotated[str, Doc("DNS zone name (e.g., example.com)")],
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
    ) -> str:
        """
        Deploy Cloudflare Tunnel configuration using Terraform.

        This function runs Terraform to deploy Cloudflare Tunnels and DNS records
        from the generated cloudflare.json configuration.

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            source: Directory containing cloudflare.json configuration file
            cloudflare_token: Cloudflare API Token (Secret)
            cloudflare_account_id: Cloudflare Account ID
            zone_name: DNS zone name
            terraform_version: Terraform version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)

        Returns:
            Status message indicating success or failure of deployment

        Example:
            dagger call deploy-cloudflare \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com

            # With persistent local state
            dagger call deploy-cloudflare \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --state-dir=./terraform-state
        """
        # Validate backend configuration
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            return error_msg

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            return error_msg

        # Check for cloudflare.json
        try:
            config_file = source.file("cloudflare.json")
            _ = await config_file.contents()
        except Exception:
            return "✗ Failed: cloudflare.json not found in source directory. Run generate-cloudflare-config first."

        # Create Terraform container
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

        # Mount source directory with cloudflare.json
        ctr = ctr.with_directory("/workspace", source)

        # Mount the Cloudflare Tunnel Terraform module
        try:
            tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        # Generate and mount backend.tf if using remote backend
        if backend_type != "local":
            try:
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file("/module/backend.tf", backend_hcl)
            except Exception as e:
                return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                # Convert YAML to HCL if necessary
                config_content, _ = await _process_backend_config(backend_config_file)
                # Mount the processed content as a .tfbackend file
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
            except Exception as e:
                return f"✗ Failed: Could not process backend config file\n{str(e)}"

        # Set up environment variables
        ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
        ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

        # Add Cloudflare token as secret (both as TF variable and env var for provider auth)
        ctr = ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
        ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

        # Handle state directory mounting and setup (persistent local state)
        using_persistent_state = state_dir is not None
        if using_persistent_state:
            # Mount state directory
            ctr = ctr.with_directory("/state", state_dir)
            # Copy module files to state directory
            ctr = ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
            # Set working directory to state directory
            ctr = ctr.with_workdir("/state")
        else:
            # Set working directory to the module (ephemeral or remote backend)
            ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        # Run terraform init (with backend config if provided)
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])
        
        try:
            init_result = await ctr.with_exec(init_cmd).stdout()
        except dagger.ExecError as e:
            error_msg = f"✗ Failed: Terraform init failed\n{str(e)}"
            if backend_type != "local":
                error_msg += (
                    "\n\nBackend configuration troubleshooting:\n"
                    "  - Verify backend config file is valid HCL\n"
                    "  - Check credentials in environment variables\n"
                    "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                )
            return error_msg

        # Run terraform apply
        try:
            apply_result = await ctr.with_exec([
                "terraform", "apply", "-auto-approve"
            ]).stdout()

            result_msg = "✓ Success: Cloudflare Tunnel deployment completed"
            if backend_type != "local":
                result_msg += f"\n  Backend: {backend_type}"
            elif using_persistent_state:
                result_msg += "\n  State: Persistent local (mounted state directory)"

            # Build tunnel token retrieval guidance
            guidance_lines = [
                "",
                "-" * 60,
                "Next Step: Retrieve Tunnel Credentials",
                "-" * 60,
                "",
                "Your Cloudflare tunnels have been deployed. To configure cloudflared",
                "on your devices, you need to retrieve the tunnel credentials.",
                "",
                "Option 1: Using Terraform (if you have Terraform installed):",
                "  terraform output -json cloudflare_tunnel_tokens",
                "",
                "Option 2: Using Dagger (recommended):",
            ]

            # Build Dagger command with actual deployment parameters
            dagger_cmd_parts = [
                "dagger call get-tunnel-secrets \\",
                f"    --source=. \\",
                f"    --cloudflare-token=env:CF_TOKEN \\",
                f"    --cloudflare-account-id={cloudflare_account_id} \\",
                f"    --zone-name={zone_name}",
            ]

            # Add backend-specific flags for remote backends
            if backend_type != "local":
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --backend-type={backend_type} \\")
                dagger_cmd_parts.append(f"    --backend-config-file=./backend.hcl")

            # Add state-dir flag for persistent local state
            if using_persistent_state:
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --state-dir=./terraform-state")

            guidance_lines.extend(dagger_cmd_parts)
            guidance_lines.extend([
                "",
                "Option 3: Install cloudflared service directly:",
                "  cloudflared service install <tunnel-token-from-option-1-or-2>",
                "",
                "For detailed setup instructions, see:",
                "  examples/homelab-media-stack/README.md",
                "-" * 60,
            ])

            result_msg += "\n".join(guidance_lines)
            result_msg += f"\n\n{apply_result}"
            return result_msg
        except dagger.ExecError as e:
            return f"✗ Failed: Terraform apply failed\n{str(e)}"

    @function
    async def deploy(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
        zone_name: Annotated[str, Doc("DNS zone name")],
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
    ) -> str:
        """
        Orchestrate full deployment: UniFi DNS first, then Cloudflare Tunnels.

        This function generates KCL configurations and deploys them in the correct
        order: UniFi first (creates local DNS), then Cloudflare (points to local DNS).

        Authentication (pick one method for UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            kcl_source: Directory containing KCL module
            unifi_url: UniFi Controller URL
            cloudflare_token: Cloudflare API Token
            cloudflare_account_id: Cloudflare Account ID
            zone_name: DNS zone name
            api_url: Optional UniFi API URL
            unifi_api_key: UniFi API key (optional)
            unifi_username: UniFi username (optional)
            unifi_password: UniFi password (optional)
            unifi_insecure: Skip TLS verification for self-signed certificates
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)

        Returns:
            Combined status message for both deployments

        Example:
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY

            # With insecure TLS for self-signed certificates
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://192.168.10.1 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-insecure

            # With persistent local state
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --state-dir=./terraform-state

            # With YAML backend config (automatically converted to HCL)
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --backend-type=s3 \\
                --backend-config-file=./s3-backend.yaml

            # Using vals for secret injection into YAML backend config:
            #   vals eval -f backend.yaml.tmpl > backend.yaml
            #   dagger call deploy ... --backend-config-file=./backend.yaml
        """
        results = []

        # Phase 1: Generate KCL configurations
        results.append("=" * 60)
        results.append("PHASE 1: Generating KCL configurations")
        results.append("=" * 60)

        try:
            unifi_file = await self.generate_unifi_config(kcl_source, kcl_version)
            unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
            results.append("✓ UniFi configuration generated")
        except Exception as e:
            return f"✗ Failed: Could not generate UniFi config\n{str(e)}"

        try:
            cloudflare_file = await self.generate_cloudflare_config(kcl_source, kcl_version)
            cloudflare_dir = dagger.dag.directory().with_file("cloudflare.json", cloudflare_file)
            results.append("✓ Cloudflare configuration generated")
        except Exception as e:
            return f"✗ Failed: Could not generate Cloudflare config\n{str(e)}"

        # Phase 2: Deploy UniFi (must complete first)
        results.append("")
        results.append("=" * 60)
        results.append("PHASE 2: Deploying UniFi DNS")
        results.append("=" * 60)

        unifi_result = await self.deploy_unifi(
            source=unifi_dir,
            unifi_url=unifi_url,
            api_url=api_url,
            unifi_api_key=unifi_api_key,
            unifi_username=unifi_username,
            unifi_password=unifi_password,
            unifi_insecure=unifi_insecure,
            terraform_version=terraform_version,
            backend_type=backend_type,
            backend_config_file=backend_config_file,
            state_dir=state_dir,
        )

        if "✗ Failed" in unifi_result:
            results.append(unifi_result)
            results.append("")
            results.append("=" * 60)
            results.append("DEPLOYMENT HALTED")
            results.append("=" * 60)
            results.append("UniFi deployment failed. Cloudflare deployment was not attempted.")
            return "\n".join(results)

        results.append(unifi_result)

        # Phase 3: Deploy Cloudflare
        results.append("")
        results.append("=" * 60)
        results.append("PHASE 3: Deploying Cloudflare Tunnels")
        results.append("=" * 60)

        cloudflare_result = await self.deploy_cloudflare(
            source=cloudflare_dir,
            cloudflare_token=cloudflare_token,
            cloudflare_account_id=cloudflare_account_id,
            zone_name=zone_name,
            terraform_version=terraform_version,
            backend_type=backend_type,
            backend_config_file=backend_config_file,
            state_dir=state_dir,
        )

        results.append(cloudflare_result)

        # Final summary
        results.append("")
        results.append("=" * 60)
        results.append("DEPLOYMENT SUMMARY")
        results.append("=" * 60)

        if "✓ Success" in unifi_result and "✓ Success" in cloudflare_result:
            results.append("✓ Both deployments completed successfully")

            # Add tunnel token retrieval guidance only when both deployments succeed
            # Cloudflare tunnels exist and are ready for device configuration
            guidance_lines = [
                "",
                "-" * 60,
                "Next Step: Retrieve Tunnel Credentials",
                "-" * 60,
                "",
                "Your Cloudflare tunnels have been deployed. To configure cloudflared",
                "on your devices, you need to retrieve the tunnel credentials.",
                "",
                "Option 1: Using Terraform (if you have Terraform installed):",
                "  terraform output -json cloudflare_tunnel_tokens",
                "",
                "Option 2: Using Dagger (recommended):",
            ]

            # Build Dagger command with actual deployment parameters
            # Note: deploy() uses KCL-generated configs in ./kcl directory
            dagger_cmd_parts = [
                "dagger call get-tunnel-secrets \\",
                f"    --source=./kcl \\",
                f"    --cloudflare-token=env:CF_TOKEN \\",
                f"    --cloudflare-account-id={cloudflare_account_id} \\",
                f"    --zone-name={zone_name}",
            ]

            # Add backend-specific flags for remote backends
            if backend_type != "local":
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --backend-type={backend_type} \\")
                dagger_cmd_parts.append(f"    --backend-config-file=./backend.hcl")

            # Add state-dir flag for persistent local state
            if state_dir is not None:
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --state-dir=./terraform-state")

            guidance_lines.extend(dagger_cmd_parts)
            guidance_lines.extend([
                "",
                "Option 3: Install cloudflared service directly:",
                "  cloudflared service install <tunnel-token-from-option-1-or-2>",
                "",
                "For detailed setup instructions, see:",
                "  examples/homelab-media-stack/README.md",
                "-" * 60,
            ])

            results.extend(guidance_lines)
        elif "✓ Success" in unifi_result:
            results.append("○ UniFi: Success")
            results.append("✗ Cloudflare: Failed")
        else:
            results.append("✗ UniFi: Failed")
            results.append("○ Cloudflare: Not attempted")

        return "\n".join(results)

    @function
    async def plan(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
        zone_name: Annotated[str, Doc("DNS zone name")],
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username (use with password)")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password (use with username)")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller (useful for self-signed certificates)")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
        no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution by auto-generating epoch timestamp")] = False,
        cache_buster: Annotated[str, Doc("Custom cache key for advanced use (cannot be used with --no-cache)")] = "",
    ) -> dagger.Directory:
        """
        Generate Terraform plans for both UniFi DNS and Cloudflare Tunnel configurations.

        This function creates execution plans without applying changes, enabling the
        standard plan → review → apply workflow. It generates three output formats
        per module: binary plan files, JSON for automation, and human-readable text.

        Authentication (pick one method for UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            kcl_source: Directory containing KCL module
            unifi_url: UniFi Controller URL
            cloudflare_token: Cloudflare API Token
            cloudflare_account_id: Cloudflare Account ID
            zone_name: DNS zone name
            api_url: Optional UniFi API URL
            unifi_api_key: UniFi API key (optional)
            unifi_username: UniFi username (optional)
            unifi_password: UniFi password (optional)
            unifi_insecure: Skip TLS verification for self-signed certificates
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)
            no_cache: Bypass Dagger cache by auto-generating an epoch timestamp
            cache_buster: Custom cache key for advanced use cases

        Returns:
            dagger.Directory containing all plan artifacts:
            - unifi-plan.tfplan, unifi-plan.json, unifi-plan.txt
            - cloudflare-plan.tfplan, cloudflare-plan.json, cloudflare-plan.txt
            - plan-summary.txt

        Example:
            # Basic usage - export plans to ./plans directory
            dagger call plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                export --path=./plans

            # With persistent local state
            dagger call plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --state-dir=./terraform-state \\
                export --path=./plans

            # With remote backend (S3) using HCL config
            dagger call plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --backend-type=s3 \\
                --backend-config-file=./s3-backend.hcl \\
                export --path=./plans

            # With YAML backend config (automatically converted)
            dagger call plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --backend-type=s3 \\
                --backend-config-file=./s3-backend.yaml \\
                export --path=./plans
        """
        # Validate cache control options
        if no_cache and cache_buster:
            raise ValueError("✗ Failed: Cannot use both --no-cache and --cache-buster")

        # Determine effective cache buster value
        effective_cache_buster = cache_buster
        if no_cache:
            effective_cache_buster = str(int(time.time()))

        # Validate UniFi authentication
        using_api_key = unifi_api_key is not None
        using_password = unifi_username is not None and unifi_password is not None

        if not using_api_key and not using_password:
            raise ValueError("✗ Failed: Must provide either unifi_api_key OR both unifi_username and unifi_password")

        if using_api_key and using_password:
            raise ValueError("✗ Failed: Cannot use both API key and username/password. Choose one authentication method.")

        # Validate backend configuration
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            raise ValueError(error_msg)

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            raise ValueError(error_msg)

        actual_api_url = api_url if api_url else unifi_url
        using_persistent_state = state_dir is not None

        # Phase 1: Generate KCL configurations
        try:
            unifi_file = await self.generate_unifi_config(kcl_source, kcl_version)
            unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
        except Exception as e:
            raise RuntimeError(f"✗ Failed: Could not generate UniFi config\n{str(e)}")

        try:
            cloudflare_file = await self.generate_cloudflare_config(kcl_source, kcl_version)
            cloudflare_dir = dagger.dag.directory().with_file("cloudflare.json", cloudflare_file)
        except Exception as e:
            raise RuntimeError(f"✗ Failed: Could not generate Cloudflare config\n{str(e)}")

        # Create output directory
        output_dir = dagger.dag.directory()

        # Phase 2: UniFi Plan Generation
        try:
            # Create Terraform container for UniFi
            unifi_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")
            unifi_ctr = unifi_ctr.with_directory("/workspace", unifi_dir)

            # Mount the UniFi DNS Terraform module
            try:
                tf_module = dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")
                unifi_ctr = unifi_ctr.with_directory("/module", tf_module)
            except Exception:
                pass

            # Generate and mount backend.tf if using remote backend
            if backend_type != "local":
                backend_hcl = self._generate_backend_block(backend_type)
                unifi_ctr = unifi_ctr.with_new_file("/module/backend.tf", backend_hcl)

            # Process and mount backend config file if provided
            if backend_config_file is not None:
                # Convert YAML to HCL if necessary
                config_content, _ = await _process_backend_config(backend_config_file)
                # Mount the processed content as a .tfbackend file
                unifi_ctr = unifi_ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)

            # Set up environment variables
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())

            # Add authentication secrets
            if using_api_key and unifi_api_key:
                unifi_ctr = unifi_ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
            elif using_password and unifi_username and unifi_password:
                unifi_ctr = unifi_ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
                unifi_ctr = unifi_ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

            # Add cache buster if provided
            if effective_cache_buster:
                unifi_ctr = unifi_ctr.with_env_variable("CACHE_BUSTER", effective_cache_buster)

            # Handle state directory mounting and setup
            if using_persistent_state:
                unifi_ctr = unifi_ctr.with_directory("/state", state_dir)
                unifi_ctr = unifi_ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
                unifi_ctr = unifi_ctr.with_workdir("/state")
            else:
                unifi_ctr = unifi_ctr.with_workdir("/module")

            # Run terraform init
            init_cmd = ["terraform", "init"]
            if backend_config_file is not None:
                init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

            unifi_ctr = unifi_ctr.with_exec(init_cmd)
            _ = await unifi_ctr.stdout()

            # Run terraform plan - CRITICAL: Preserve container reference
            unifi_ctr = unifi_ctr.with_exec(["terraform", "plan", "-out=unifi-plan.tfplan"])
            _ = await unifi_ctr.stdout()

            # Generate JSON output
            unifi_ctr = unifi_ctr.with_exec(["sh", "-c", "terraform show -json unifi-plan.tfplan > unifi-plan.json"])
            _ = await unifi_ctr.stdout()

            # Generate text output
            unifi_ctr = unifi_ctr.with_exec(["sh", "-c", "terraform show unifi-plan.tfplan > unifi-plan.txt"])
            _ = await unifi_ctr.stdout()

            # Extract plan files from POST-execution container
            unifi_plan_binary = await unifi_ctr.file("/state/unifi-plan.tfplan" if using_persistent_state else "/module/unifi-plan.tfplan")
            unifi_plan_json = await unifi_ctr.file("/state/unifi-plan.json" if using_persistent_state else "/module/unifi-plan.json")
            unifi_plan_txt = await unifi_ctr.file("/state/unifi-plan.txt" if using_persistent_state else "/module/unifi-plan.txt")

            # Add to output directory
            output_dir = output_dir.with_file("unifi-plan.tfplan", unifi_plan_binary)
            output_dir = output_dir.with_file("unifi-plan.json", unifi_plan_json)
            output_dir = output_dir.with_file("unifi-plan.txt", unifi_plan_txt)

            # Parse UniFi plan for resource counts
            try:
                unifi_json_content = await unifi_plan_json.contents()
                unifi_plan_data = json.loads(unifi_json_content)
                unifi_changes = unifi_plan_data.get("resource_changes", [])
                unifi_add = sum(1 for c in unifi_changes if any(a.get("action") in ["create", "add"] for a in c.get("change", {}).get("actions", [])))
                unifi_change = sum(1 for c in unifi_changes if any(a.get("action") in ["update", "change"] for a in c.get("change", {}).get("actions", [])))
                unifi_destroy = sum(1 for c in unifi_changes if any(a.get("action") in ["delete", "destroy"] for a in c.get("change", {}).get("actions", [])))
            except Exception:
                # Fallback: parse from text
                unifi_txt_content = await unifi_plan_txt.contents()
                unifi_add = unifi_txt_content.count("will be created")
                unifi_change = unifi_txt_content.count("will be changed")
                unifi_destroy = unifi_txt_content.count("will be destroyed")

        except Exception as e:
            raise RuntimeError(f"✗ Failed: UniFi Terraform plan failed\n{str(e)}")

        # Phase 3: Cloudflare Plan Generation
        try:
            # Create Terraform container for Cloudflare
            cf_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")
            cf_ctr = cf_ctr.with_directory("/workspace", cloudflare_dir)

            # Mount the Cloudflare Tunnel Terraform module
            try:
                tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
                cf_ctr = cf_ctr.with_directory("/module", tf_module)
            except Exception:
                pass

            # Generate and mount backend.tf if using remote backend
            if backend_type != "local":
                backend_hcl = self._generate_backend_block(backend_type)
                cf_ctr = cf_ctr.with_new_file("/module/backend.tf", backend_hcl)

            # Process and mount backend config file if provided
            if backend_config_file is not None:
                # Convert YAML to HCL if necessary
                config_content, _ = await _process_backend_config(backend_config_file)
                # Mount the processed content as a .tfbackend file
                cf_ctr = cf_ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)

            # Set up environment variables
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_zone_name", zone_name)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

            # Add Cloudflare token as secret
            cf_ctr = cf_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
            cf_ctr = cf_ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

            # Add cache buster if provided
            if effective_cache_buster:
                cf_ctr = cf_ctr.with_env_variable("CACHE_BUSTER", effective_cache_buster)

            # Handle state directory mounting and setup
            if using_persistent_state:
                cf_ctr = cf_ctr.with_directory("/state", state_dir)
                cf_ctr = cf_ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
                cf_ctr = cf_ctr.with_workdir("/state")
            else:
                cf_ctr = cf_ctr.with_workdir("/module")

            # Run terraform init
            init_cmd = ["terraform", "init"]
            if backend_config_file is not None:
                init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

            cf_ctr = cf_ctr.with_exec(init_cmd)
            _ = await cf_ctr.stdout()

            # Run terraform plan - CRITICAL: Preserve container reference
            cf_ctr = cf_ctr.with_exec(["terraform", "plan", "-out=cloudflare-plan.tfplan"])
            _ = await cf_ctr.stdout()

            # Generate JSON output
            cf_ctr = cf_ctr.with_exec(["sh", "-c", "terraform show -json cloudflare-plan.tfplan > cloudflare-plan.json"])
            _ = await cf_ctr.stdout()

            # Generate text output
            cf_ctr = cf_ctr.with_exec(["sh", "-c", "terraform show cloudflare-plan.tfplan > cloudflare-plan.txt"])
            _ = await cf_ctr.stdout()

            # Extract plan files from POST-execution container
            cf_plan_binary = await cf_ctr.file("/state/cloudflare-plan.tfplan" if using_persistent_state else "/module/cloudflare-plan.tfplan")
            cf_plan_json = await cf_ctr.file("/state/cloudflare-plan.json" if using_persistent_state else "/module/cloudflare-plan.json")
            cf_plan_txt = await cf_ctr.file("/state/cloudflare-plan.txt" if using_persistent_state else "/module/cloudflare-plan.txt")

            # Add to output directory
            output_dir = output_dir.with_file("cloudflare-plan.tfplan", cf_plan_binary)
            output_dir = output_dir.with_file("cloudflare-plan.json", cf_plan_json)
            output_dir = output_dir.with_file("cloudflare-plan.txt", cf_plan_txt)

            # Parse Cloudflare plan for resource counts
            try:
                cf_json_content = await cf_plan_json.contents()
                cf_plan_data = json.loads(cf_json_content)
                cf_changes = cf_plan_data.get("resource_changes", [])
                cf_add = sum(1 for c in cf_changes if any(a.get("action") in ["create", "add"] for a in c.get("change", {}).get("actions", [])))
                cf_change = sum(1 for c in cf_changes if any(a.get("action") in ["update", "change"] for a in c.get("change", {}).get("actions", [])))
                cf_destroy = sum(1 for c in cf_changes if any(a.get("action") in ["delete", "destroy"] for a in c.get("change", {}).get("actions", [])))
            except Exception:
                # Fallback: parse from text
                cf_txt_content = await cf_plan_txt.contents()
                cf_add = cf_txt_content.count("will be created")
                cf_change = cf_txt_content.count("will be changed")
                cf_destroy = cf_txt_content.count("will be destroyed")

        except Exception as e:
            raise RuntimeError(f"✗ Failed: Cloudflare Terraform plan failed\n{str(e)}")

        # Phase 4: Create plan summary
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        total_add = unifi_add + cf_add
        total_change = unifi_change + cf_change
        total_destroy = unifi_destroy + cf_destroy

        summary_content = f"""Terraform Plan Summary
======================

Generated: {timestamp}
Terraform Version: {terraform_version}
KCL Version: {kcl_version}
Backend Type: {backend_type}

UniFi DNS Module
----------------
Resources to add:     {unifi_add}
Resources to change:  {unifi_change}
Resources to destroy: {unifi_destroy}

Cloudflare Tunnel Module
------------------------
Resources to add:     {cf_add}
Resources to change:  {cf_change}
Resources to destroy: {cf_destroy}

Overall Totals
--------------
Resources to add:     {total_add}
Resources to change:  {total_change}
Resources to destroy: {total_destroy}
Total changes:        {total_add + total_change + total_destroy}

Output Files
------------
- unifi-plan.tfplan      (binary plan for terraform apply)
- unifi-plan.json        (structured JSON for automation)
- unifi-plan.txt         (human-readable format)
- cloudflare-plan.tfplan (binary plan for terraform apply)
- cloudflare-plan.json   (structured JSON for automation)
- cloudflare-plan.txt    (human-readable format)

Notes
-----
- Binary plan files (*.tfplan) can be used with 'terraform apply <planfile>'
- JSON files are suitable for policy-as-code tools (OPA, Sentinel)
- Text files are optimized for manual review and diffing
- Plan files may contain sensitive values - handle securely
"""

        output_dir = output_dir.with_new_file("plan-summary.txt", summary_content)

        return output_dir

    @function
    async def destroy(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
        zone_name: Annotated[str, Doc("DNS zone name")],
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
    ) -> str:
        """
        Destroy all resources in reverse order: Cloudflare first, then UniFi.

        Destroys Cloudflare Tunnels first (to avoid DNS loops), then UniFi DNS records.

        Authentication (pick one method for UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            kcl_source: Directory containing KCL module
            unifi_url: UniFi Controller URL
            cloudflare_token: Cloudflare API Token
            cloudflare_account_id: Cloudflare Account ID
            zone_name: DNS zone name
            api_url: Optional UniFi API URL
            unifi_api_key: UniFi API key (optional)
            unifi_username: UniFi username (optional)
            unifi_password: UniFi password (optional)
            unifi_insecure: Skip TLS verification for self-signed certificates
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)

        Returns:
            Combined status message for destruction

        Example:
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY

            # With insecure TLS for self-signed certificates
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://192.168.10.1 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-insecure

            # With persistent local state
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --state-dir=./terraform-state

            # With YAML backend config (automatically converted to HCL)
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --backend-type=s3 \\
                --backend-config-file=./s3-backend.yaml
        """
        results = []

        # Generate configurations first (needed for destroy)
        results.append("=" * 60)
        results.append("GENERATING CONFIGURATIONS FOR DESTROY")
        results.append("=" * 60)

        try:
            unifi_file = await self.generate_unifi_config(kcl_source, kcl_version)
            unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
            results.append("✓ UniFi configuration generated")
        except Exception as e:
            return f"✗ Failed: Could not generate UniFi config\n{str(e)}"

        try:
            cloudflare_file = await self.generate_cloudflare_config(kcl_source, kcl_version)
            cloudflare_dir = dagger.dag.directory().with_file("cloudflare.json", cloudflare_file)
            results.append("✓ Cloudflare configuration generated")
        except Exception as e:
            return f"✗ Failed: Could not generate Cloudflare config\n{str(e)}"

        actual_api_url = api_url if api_url else unifi_url

        # Validate backend configuration
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            return error_msg

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            return error_msg

        # Track if using persistent local state
        using_persistent_state = state_dir is not None

        # Phase 1: Destroy Cloudflare first (reverse order)
        results.append("")
        results.append("=" * 60)
        results.append("PHASE 1: Destroying Cloudflare Tunnels")
        results.append("=" * 60)

        # Check for cloudflare.json
        try:
            config_file = cloudflare_dir.file("cloudflare.json")
            _ = await config_file.contents()
        except Exception:
            return "✗ Failed: cloudflare.json not found"

        # Create Terraform container for Cloudflare
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")
        ctr = ctr.with_directory("/workspace", cloudflare_dir)

        try:
            tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        # Generate and mount backend.tf if using remote backend
        if backend_type != "local":
            try:
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file("/module/backend.tf", backend_hcl)
            except Exception as e:
                return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                # Convert YAML to HCL if necessary
                config_content, _ = await _process_backend_config(backend_config_file)
                # Mount the processed content as a .tfbackend file
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
            except Exception as e:
                return f"✗ Failed: Could not process backend config file\n{str(e)}"

        ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
        ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")
        ctr = ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
        ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

        # Handle state directory mounting and setup (persistent local state)
        if using_persistent_state:
            # Mount state directory
            ctr = ctr.with_directory("/state", state_dir)
            # Copy module files to state directory
            ctr = ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
            # Set working directory to state directory
            ctr = ctr.with_workdir("/state")
        else:
            # Set working directory to the module (ephemeral or remote backend)
            ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        # Run terraform init (with backend config if provided)
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

        try:
            await ctr.with_exec(init_cmd).stdout()
        except dagger.ExecError as e:
            error_msg = f"✗ Terraform init failed: {str(e)}"
            if backend_type != "local":
                error_msg += (
                    "\n\nBackend configuration troubleshooting:\n"
                    "  - Verify backend config file is valid HCL\n"
                    "  - Check credentials in environment variables\n"
                    "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                )
            results.append(error_msg)
            return "\n".join(results)

        try:
            destroy_result = await ctr.with_exec([
                "terraform", "destroy", "-auto-approve"
            ]).stdout()
            results.append("✓ Cloudflare resources destroyed")
            cloudflare_success = True
        except dagger.ExecError as e:
            results.append(f"✗ Cloudflare destroy failed: {str(e)}")
            cloudflare_success = False

        # Phase 2: Destroy UniFi
        results.append("")
        results.append("=" * 60)
        results.append("PHASE 2: Destroying UniFi DNS")
        results.append("=" * 60)

        if not cloudflare_success:
            results.append("SKIPPED: Cloudflare destroy failed, stopping to prevent DNS issues")
            results.append("")
            results.append("⚠ WARNING: Resources may still exist!")
            return "\n".join(results)

        # Check for unifi.json
        try:
            config_file = unifi_dir.file("unifi.json")
            _ = await config_file.contents()
        except Exception:
            return "✗ Failed: unifi.json not found"

        # Create Terraform container for UniFi
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")
        ctr = ctr.with_directory("/workspace", unifi_dir)

        try:
            tf_module = dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        # Generate and mount backend.tf if using remote backend
        if backend_type != "local":
            try:
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file("/module/backend.tf", backend_hcl)
            except Exception as e:
                return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                # Convert YAML to HCL if necessary
                config_content, _ = await _process_backend_config(backend_config_file)
                # Mount the processed content as a .tfbackend file
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
            except Exception as e:
                return f"✗ Failed: Could not process backend config file\n{str(e)}"

        ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
        ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
        ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())

        if unifi_api_key:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
        elif unifi_username and unifi_password:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
            ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

        # Handle state directory mounting and setup (persistent local state)
        if using_persistent_state:
            # Mount state directory
            ctr = ctr.with_directory("/state", state_dir)
            # Copy module files to state directory
            ctr = ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
            # Set working directory to state directory
            ctr = ctr.with_workdir("/state")
        else:
            # Set working directory to the module (ephemeral or remote backend)
            ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        # Run terraform init (with backend config if provided)
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

        try:
            await ctr.with_exec(init_cmd).stdout()
        except dagger.ExecError as e:
            error_msg = f"✗ Terraform init failed: {str(e)}"
            if backend_type != "local":
                error_msg += (
                    "\n\nBackend configuration troubleshooting:\n"
                    "  - Verify backend config file is valid HCL\n"
                    "  - Check credentials in environment variables\n"
                    "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                )
            results.append(error_msg)
            return "\n".join(results)

        try:
            destroy_result = await ctr.with_exec([
                "terraform", "destroy", "-auto-approve"
            ]).stdout()
            results.append("✓ UniFi resources destroyed")
            unifi_success = True
        except dagger.ExecError as e:
            results.append(f"✗ UniFi destroy failed: {str(e)}")
            unifi_success = False

        # Final summary
        results.append("")
        results.append("=" * 60)
        results.append("DESTRUCTION SUMMARY")
        results.append("=" * 60)

        if cloudflare_success and unifi_success:
            results.append("✓ All resources destroyed successfully")
        elif cloudflare_success:
            results.append("○ Cloudflare: Destroyed")
            results.append("✗ UniFi: Failed - potential orphaned resources")
        else:
            results.append("✗ Cloudflare: Failed")
            results.append("○ UniFi: Not attempted")

        results.append("")
        results.append("⚠ NOTE: If using local state, manually clean up Terraform state files")

        return "\n".join(results)

    @function
    async def generate_cloudflare_config(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
    ) -> dagger.File:
        """
        Generate Cloudflare JSON configuration from KCL schemas.

        This function runs the KCL Cloudflare generator in a containerized environment
        and returns the generated JSON configuration as a File object.

        Args:
            source: Directory containing KCL module (must have kcl.mod)
            kcl_version: KCL version to use (default: "latest")

        Returns:
            dagger.File containing the generated Cloudflare JSON configuration

        Example:
            dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
        """
        # Check for kcl.mod
        try:
            mod_file = source.file("kcl.mod")
            _ = await mod_file.contents()
        except Exception:
            raise KCLGenerationError(
                "✗ No kcl.mod found in source directory. "
                "Is this a valid KCL module?\n"
                "Hint: Run 'kcl mod init' in your KCL directory to create a module."
            )

        # Check for main.k entry point
        try:
            main_file = source.file("main.k")
            _ = await main_file.contents()
        except Exception:
            raise KCLGenerationError(
                "✗ Entry point file not found: main.k\n"
                "The module requires main.k as the entry point.\n"
                "Hint: Ensure your KCL module has a main.k file that exports cf_output."
            )

        # Create container with KCL and yq for YAML to JSON conversion
        base_ctr = dagger.dag.container().from_(f"kcllang/kcl:{kcl_version}")
        
        # Install curl and yq for YAML to JSON conversion
        ctr = base_ctr.with_exec([
            "sh", "-c",
            "apt-get update && apt-get install -y curl && curl -sL https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64 -o /usr/local/bin/yq && chmod +x /usr/local/bin/yq"
        ])
        
        # Mount source directory
        ctr = ctr.with_directory("/src", source).with_workdir("/src")

        # Step 1: Download KCL dependencies to prevent git clone messages in output
        # This must be done before 'kcl run' to ensure clean YAML output
        try:
            ctr = ctr.with_exec(["kcl", "mod", "update"])
            await ctr.stdout()  # Wait for completion but don't capture output
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ Failed to download KCL dependencies:\n"
                f"Exit code: {e.exit_code}\n"
                f"Stderr: {e.stderr}\n"
                f"\nPossible causes:\n"
                f"  - Network connectivity issues\n"
                f"  - Invalid kcl.mod syntax\n"
                f"  - Git repository not accessible\n"
                f"\nSuggested fixes:\n"
                f"  - Check your network connection\n"
                f"  - Validate kcl.mod syntax with 'kcl mod graph' locally\n"
                f"  - Ensure git dependencies are accessible from this environment"
            )

        # Step 2: Run KCL main.k and capture full output
        try:
            ctr = ctr.with_exec(["kcl", "run", "main.k"])
            kcl_output = await ctr.stdout()
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ KCL execution failed:\n"
                f"Exit code: {e.exit_code}\n"
                f"Stdout: {e.stdout}\n"
                f"Stderr: {e.stderr}\n"
                f"\nHint: Check your KCL syntax with 'kcl run main.k' locally."
            )

        # Step 3: Check for validation errors in output
        # When KCL validation fails, generate_with_output() prints errors and returns no JSON
        if "✗" in kcl_output or "VALIDATION" in kcl_output:
            raise KCLGenerationError(
                f"✗ KCL validation failed:\n\n{kcl_output}\n"
                f"\nThe KCL configuration has validation errors that must be fixed.\n"
                f"See the error messages above for details on what needs to be corrected."
            )

        # Step 4: Validate empty output
        if not kcl_output or not kcl_output.strip():
            raise KCLGenerationError(
                "✗ KCL produced empty output:\n"
                "Possible causes:\n"
                "  - main.k is empty or has no output statements\n"
                "  - KCL module has no output statements\n"
                "  - All configurations are commented out\n"
                "\nHint: Run 'kcl run main.k' locally to see the raw output."
            )

        # Step 5: Write KCL output to temporary file for yq extraction
        ctr = ctr.with_new_file("/tmp/kcl-output.yaml", kcl_output)

        # Step 6: Extract cf_output section using yq
        try:
            ctr = ctr.with_exec(["yq", "eval", ".cf_output", "/tmp/kcl-output.yaml"])
            cf_yaml = await ctr.stdout()
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ Failed to extract cf_output from YAML:\n"
                f"yq error: {e.stderr}\n"
                f"\nHint: Ensure your main.k exports 'cf_output' as a public variable."
            )

        # Step 7: Check for null output (missing key)
        if not cf_yaml or cf_yaml.strip() == "null" or not cf_yaml.strip():
            raise KCLGenerationError(
                "✗ main.k does not export 'cf_output':\n"
                "The main.k file must export a public variable named 'cf_output'.\n"
                "\nExample:\n"
                "  import unifi_cloudflare_glue.generators.cloudflare as cf_gen\n"
                "  cf_output = cf_gen.generate_with_output(config)\n"
                "\nHint: Run 'kcl run main.k' locally to inspect the output structure."
            )

        # Step 8: Convert extracted YAML to JSON
        ctr = ctr.with_new_file("/tmp/cf-output.yaml", cf_yaml)
        try:
            ctr = ctr.with_exec(["yq", "eval", "-o=json", "/tmp/cf-output.yaml"])
            json_result = await ctr.stdout()
        except dagger.ExecError as e:
            # Truncate output to 1000 characters for error display
            truncated_output = cf_yaml[:1000] if len(cf_yaml) > 1000 else cf_yaml
            ellipsis_indicator = "... (truncated)" if len(cf_yaml) > 1000 else ""
            raise KCLGenerationError(
                f"✗ YAML to JSON conversion failed:\n"
                f"yq error: {e.stderr}\n"
                f"\nExtracted cf_output that failed to parse:\n"
                f"{'-' * 60}\n"
                f"{truncated_output}{ellipsis_indicator}\n"
                f"{'-' * 60}\n"
                f"\nPossible causes:\n"
                f"  - KCL validation warnings in output\n"
                f"  - Invalid YAML structure in cf_output\n"
                f"  - KCL syntax errors that produced partial output\n"
                f"\nHint: Run 'kcl run main.k' locally to see the raw output."
            )

        # Step 9: Validate JSON output
        try:
            json.loads(json_result)
        except json.JSONDecodeError as je:
            # Truncate JSON result to 500 characters for error display
            truncated_json = json_result[:500] if len(json_result) > 500 else json_result
            json_ellipsis = "... (truncated)" if len(json_result) > 500 else ""
            raise KCLGenerationError(
                f"✗ Invalid JSON output after yq conversion:\n"
                f"JSON parse error: {str(je)}\n"
                f"\nInvalid output preview:\n"
                f"{'-' * 60}\n"
                f"{truncated_json}{json_ellipsis}\n"
                f"{'-' * 60}\n"
                f"\nHint: This may indicate a bug in yq or unexpected KCL output format."
            )

        # Step 10: Return as file
        return dagger.dag.directory().with_new_file("cloudflare.json", json_result).file("cloudflare.json")

    def _generate_test_id(self) -> str:
        """Generate a random test identifier."""
        return "test-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

    def _generate_test_configs(
        self,
        test_id: str,
        cloudflare_zone: str,
        cloudflare_account_id: str,
        test_mac: str = "aa:bb:cc:dd:ee:ff",
        unifi_domain: str = ""
    ) -> dict:
        """
        Generate test configuration JSON for Cloudflare and UniFi Terraform modules.

        This method generates JSON configuration files that match the variable structures
        expected by the Terraform modules for Cloudflare Tunnel and UniFi DNS.

        Args:
            test_id: Unique test identifier (e.g., "test-abc12")
            cloudflare_zone: DNS zone name (e.g., "example.com")
            cloudflare_account_id: Cloudflare account ID
            test_mac: MAC address to use for the test device (default: "aa:bb:cc:dd:ee:ff")
            unifi_domain: Domain for UniFi DNS records. If empty, defaults to cloudflare_zone.
                Use this to ensure test DNS records use the correct FQDN matching the Cloudflare zone.

        Returns:
            dict with "cloudflare" and "unifi" keys containing JSON configuration strings:
            {
                "cloudflare": '{"zone_name": "...", "account_id": "...", "tunnels": {...}}',
                "unifi": '{"devices": [...], "default_domain": "...", "site": "..."}'
            }

        Example:
            >>> configs = self._generate_test_configs("test-abc12", "example.com", "12345")
            >>> cloudflare_json = json.loads(configs["cloudflare"])
            >>> unifi_json = json.loads(configs["unifi"])
        """
        # Use provided MAC address (consistent across both configs)
        # Default unifi_domain to cloudflare_zone if not provided
        effective_unifi_domain = unifi_domain if unifi_domain else cloudflare_zone

        # Generate identifiers
        test_hostname = f"{test_id}.{cloudflare_zone}"
        tunnel_name = f"tunnel-{test_id}"

        # Build Cloudflare config matching terraform/modules/cloudflare-tunnel/variables.tf
        cloudflare_config = {
            "zone_name": cloudflare_zone,
            "account_id": cloudflare_account_id,
            "tunnels": {
                test_mac: {
                    "tunnel_name": tunnel_name,
                    "mac_address": test_mac,
                    "services": [
                        {
                            "public_hostname": test_hostname,
                            "local_service_url": "http://192.168.1.100:8080",
                            "no_tls_verify": False
                        }
                    ]
                }
            }
        }

        # Build UniFi config matching terraform/modules/unifi-dns/variables.tf
        unifi_config = {
            "devices": [
                {
                    "friendly_hostname": test_id,
                    "domain": effective_unifi_domain,
                    "service_cnames": [],
                    "nics": [
                        {
                            "mac_address": test_mac,
                            "nic_name": "eth0",
                            "service_cnames": []
                        }
                    ]
                }
            ],
            "default_domain": effective_unifi_domain,
            "site": "default"
        }

        return {
            "cloudflare": json.dumps(cloudflare_config, indent=2),
            "unifi": json.dumps(unifi_config, indent=2)
        }

    @function
    async def test_integration(
        self,
        source: Annotated[Directory, Doc("Project source directory containing KCL and Terraform configs")],
        cloudflare_zone: Annotated[str, Doc("DNS zone for test records (e.g., test.example.com)")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API token")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare account ID")],
        unifi_url: Annotated[str, Doc("UniFi controller URL (e.g., https://unifi.local:8443)")],
        api_url: Annotated[str, Doc("UniFi API URL (often same as unifi_url)")],
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username (use with password)")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password (use with username)")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller (useful for self-signed certificates)")] = False,
        cleanup: Annotated[bool, Doc("Whether to cleanup resources after test (default: true)")] = True,
        validate_connectivity: Annotated[bool, Doc("Whether to test actual HTTP connectivity")] = False,
        test_timeout: Annotated[str, Doc("Timeout for test operations (e.g., 5m)")] = "5m",
        no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution by auto-generating epoch timestamp")] = False,
        cache_buster: Annotated[str, Doc("Custom cache key for advanced use (cannot be used with --no-cache)")] = "",
        wait_before_cleanup: Annotated[int, Doc("Seconds to wait between validation and cleanup for manual verification")] = 0,
        test_mac_address: Annotated[str, Doc("MAC address for test device (must exist in UniFi controller, e.g., 'aa:bb:cc:dd:ee:ff')")] = "aa:bb:cc:dd:ee:ff",
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
    ) -> str:
        """
        Run integration test creating ephemeral DNS resources with real APIs.

        Creates temporary Cloudflare tunnel and DNS records, UniFi DNS records,
        validates the setup, and guarantees cleanup regardless of test outcome.

        Authentication options (pick one):
        1. API Key: Provide unifi_api_key
        2. Username/Password: Provide both unifi_username AND unifi_password

        Args:
            source: Project source directory containing KCL and Terraform configs
            cloudflare_zone: DNS zone for test records (e.g., test.example.com)
            cloudflare_token: Cloudflare API token
            cloudflare_account_id: Cloudflare account ID
            unifi_url: UniFi controller URL (e.g., https://unifi.local:8443)
            api_url: UniFi API URL (often same as unifi_url)
            unifi_api_key: UniFi API key (mutually exclusive with username/password)
            unifi_username: UniFi username (use with password)
            unifi_password: UniFi password (use with username)
            unifi_insecure: Skip TLS verification for self-signed certificates
            cleanup: Whether to cleanup resources after test (default: true)
            validate_connectivity: Whether to test actual HTTP connectivity
            test_timeout: Timeout for test operations (e.g., 5m)
            no_cache: Bypass Dagger cache by auto-generating an epoch timestamp.
                This is the preferred way to force fresh test execution.
                Cannot be used together with --cache-buster.
            cache_buster: Custom cache key for advanced use cases requiring
                specific cache invalidation values. Cannot be used with --no-cache.
            wait_before_cleanup: Seconds to wait between validation and cleanup.
                Allows manual verification of created resources before they are destroyed.
            test_mac_address: MAC address for the test device. This MAC must exist in your
                UniFi controller. Use a real device MAC from your network (default: "aa:bb:cc:dd:ee:ff")
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")

        Returns:
            Detailed test report with created resources, validation results, and cleanup status.

        Example usage:
            # Basic usage
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443

            # With insecure TLS for self-signed certificates
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://192.168.10.1 \\
                --api-url=https://192.168.10.1 \\
                --unifi-insecure

            # Force fresh execution (bypass Dagger cache)
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --no-cache

            # With custom cache buster (advanced use)
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --cache-buster=custom-key-123

            # With wait for manual verification
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --wait-before-cleanup=30

            # With a real MAC address from your UniFi controller
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --test-mac-address=de:ad:be:ef:12:34

            # With pinned versions
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --terraform-version=1.10.0 \\
                --kcl-version=0.11.0
        """
        # Validate that --no-cache and --cache-buster are not used together
        if no_cache and cache_buster:
            return "✗ Failed: Cannot use both --no-cache and --cache-buster"

        # Determine effective cache buster value
        effective_cache_buster = cache_buster
        if no_cache:
            effective_cache_buster = str(int(time.time()))

        # Validate UniFi authentication
        using_api_key = unifi_api_key is not None
        using_password = unifi_username is not None and unifi_password is not None

        if not using_api_key and not using_password:
            return "✗ Failed: Must provide either unifi_api_key OR both unifi_username and unifi_password"

        if using_api_key and using_password:
            return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."

        # Generate random test ID
        test_id = self._generate_test_id()
        test_hostname = f"{test_id}.{cloudflare_zone}"
        tunnel_name = f"tunnel-{test_id}"
        unifi_hostname = f"{test_id}.{cloudflare_zone}"

        report_lines = [
            "=" * 60,
            "INTEGRATION TEST REPORT",
            "=" * 60,
            f"Test ID: {test_id}",
            f"Cloudflare Zone: {cloudflare_zone}",
            f"Test Hostname: {test_hostname}",
            f"UniFi Hostname: {unifi_hostname}",
            f"Tunnel Name: {tunnel_name}",
            f"Test MAC Address: {test_mac_address}",
            f"Cleanup Enabled: {cleanup}",
            f"Connectivity Check: {validate_connectivity}",
        ]

        # Add cache buster info if provided
        if effective_cache_buster:
            report_lines.append(f"Cache Buster: {effective_cache_buster}")

        # Add wait info if enabled
        if wait_before_cleanup > 0:
            report_lines.append(f"Wait Before Cleanup: {wait_before_cleanup}s")

        report_lines.append("-" * 60)

        # Create test configurations (Cloudflare and UniFi JSON)
        test_configs = self._generate_test_configs(
            test_id, cloudflare_zone, cloudflare_account_id, test_mac_address,
            unifi_domain=cloudflare_zone
        )
        cloudflare_json = test_configs["cloudflare"]
        unifi_json = test_configs["unifi"]

        # Track cleanup status
        cleanup_status = {"cloudflare": "pending", "unifi": "pending", "state_files": "pending"}
        validation_results = {}

        # Initialize state directory variables for cleanup phase
        cloudflare_state_dir = None
        unifi_state_dir = None

        try:
            # Phase 1: Generate JSON configs for Terraform modules
            report_lines.append("PHASE 1: Generating Terraform JSON configurations...")

            # Get the secret values for use in containers
            cf_token_plain = await cloudflare_token.plaintext()

            # Create a container with the source code
            base_container = (
                dagger.dag.container()
                .from_(f"hashicorp/terraform:{terraform_version}")
                .with_exec(["sh", "-c", "apk add --no-cache curl jq || apt-get update && apt-get install -y curl jq"])
            )

            # Add cache buster as environment variable if provided (forces cache invalidation)
            if effective_cache_buster:
                base_container = base_container.with_env_variable("CACHE_BUSTER", effective_cache_buster)

            # Add source to container
            src_container = base_container.with_directory("/src", source)

            # Write test JSON configs for Terraform modules
            src_container = src_container.with_new_file("/src/cloudflare.json", cloudflare_json)
            src_container = src_container.with_new_file("/src/unifi.json", unifi_json)

            report_lines.append(f"  ✓ Generated JSON configs for test ID: {test_id}")
            report_lines.append(f"  ✓ Test hostname: {test_hostname}")

            # Phase 2: Create Cloudflare resources
            report_lines.append("")
            report_lines.append("PHASE 2: Creating Cloudflare resources...")

            # Create directory with Cloudflare config for Terraform
            cloudflare_dir = dagger.dag.directory().with_new_file("cloudflare.json", cloudflare_json)

            # Create Terraform container following deploy_cloudflare() pattern
            cf_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

            # Mount Cloudflare config at /workspace
            cf_ctr = cf_ctr.with_directory("/workspace", cloudflare_dir)

            # Mount the Cloudflare Tunnel Terraform module
            try:
                tf_module = source.directory("terraform/modules/cloudflare-tunnel")
                cf_ctr = cf_ctr.with_directory("/module", tf_module)
            except Exception:
                # If module not in source, try project root
                try:
                    tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
                    cf_ctr = cf_ctr.with_directory("/module", tf_module)
                except Exception:
                    raise RuntimeError("Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel")

            # Set environment variables
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_zone_name", cloudflare_zone)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

            # Pass Cloudflare token as secret (both as TF variable and env var for provider auth)
            cf_ctr = cf_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
            cf_ctr = cf_ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

            # Set working directory to module
            cf_ctr = cf_ctr.with_workdir("/module")

            # Execute terraform init
            try:
                init_result = await cf_ctr.with_exec(["terraform", "init"]).stdout()
                report_lines.append("  ✓ Terraform init completed")
            except dagger.ExecError as e:
                error_msg = f"Terraform init failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["cloudflare_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Execute terraform apply
            try:
                # Save container reference after execution
                cf_ctr = cf_ctr.with_exec(["terraform", "apply", "-auto-approve"])
                apply_result = await cf_ctr.stdout()
                report_lines.append(f"  ✓ Created tunnel: {tunnel_name}")
                report_lines.append(f"  ✓ Created DNS record: {test_hostname}")
                validation_results["cloudflare_tunnel"] = "created"
                validation_results["cloudflare_dns"] = "created"
            except dagger.ExecError as e:
                error_msg = f"Terraform apply failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["cloudflare_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Export Cloudflare state for cleanup phase
            try:
                # Now cf_ctr contains the executed container with the state file
                cf_state_file = await cf_ctr.file("/module/terraform.tfstate")
                cloudflare_state_dir = dagger.dag.directory().with_file("terraform.tfstate", cf_state_file)
                report_lines.append("  ✓ Cloudflare state exported")
            except Exception as e:
                report_lines.append(f"  ⚠ Cloudflare state export failed: {str(e)}")
                cloudflare_state_dir = None

            # Phase 3: Create UniFi resources
            report_lines.append("")
            report_lines.append("PHASE 3: Creating UniFi resources...")

            # Note: UniFi will fail if the test MAC address doesn't exist in the
            # UniFi controller. Use --test-mac-address to specify a real device MAC.

            # Create directory with UniFi config for Terraform
            unifi_dir = dagger.dag.directory().with_new_file("unifi.json", unifi_json)

            # Create Terraform container following deploy_unifi() pattern
            unifi_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

            # Mount UniFi config at /workspace
            unifi_ctr = unifi_ctr.with_directory("/workspace", unifi_dir)

            # Mount the UniFi DNS Terraform module
            try:
                tf_module = source.directory("terraform/modules/unifi-dns")
                unifi_ctr = unifi_ctr.with_directory("/module", tf_module)
            except Exception:
                # If module not in source, try project root
                try:
                    tf_module = dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")
                    unifi_ctr = unifi_ctr.with_directory("/module", tf_module)
                except Exception:
                    raise RuntimeError("UniFi DNS Terraform module not found at terraform/modules/unifi-dns")

            # Set environment variables
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_api_url", api_url if api_url else unifi_url)
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())

            # Pass authentication credentials as secrets
            if unifi_api_key:
                unifi_ctr = unifi_ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
            elif unifi_username and unifi_password:
                unifi_ctr = unifi_ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
                unifi_ctr = unifi_ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

            # Set working directory to module
            unifi_ctr = unifi_ctr.with_workdir("/module")

            # Execute terraform init
            try:
                init_result = await unifi_ctr.with_exec(["terraform", "init"]).stdout()
                report_lines.append("  ✓ Terraform init completed")
            except dagger.ExecError as e:
                error_msg = f"Terraform init failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["unifi_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Execute terraform apply
            try:
                # Save container reference after execution
                unifi_ctr = unifi_ctr.with_exec(["terraform", "apply", "-auto-approve"])
                apply_result = await unifi_ctr.stdout()
                report_lines.append(f"  ✓ Created UniFi DNS record: {unifi_hostname}")
                validation_results["unifi_dns"] = "created"
            except dagger.ExecError as e:
                error_msg = f"Terraform apply failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["unifi_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Export UniFi state for cleanup phase
            try:
                # Now unifi_ctr contains the executed container with the state file
                unifi_state_file = await unifi_ctr.file("/module/terraform.tfstate")
                unifi_state_dir = dagger.dag.directory().with_file("terraform.tfstate", unifi_state_file)
                report_lines.append("  ✓ UniFi state exported")
            except Exception as e:
                report_lines.append(f"  ⚠ UniFi state export failed: {str(e)}")
                unifi_state_dir = None

            # Phase 4: Credential Retrieval via get_tunnel_secrets
            report_lines.append("")
            report_lines.append("PHASE 4: Retrieving tunnel secrets...")

            try:
                # Create a directory with the Cloudflare state for credential retrieval
                cf_state_for_secrets = dagger.dag.directory().with_file("terraform.tfstate", cf_state_file)

                # Call get_tunnel_secrets to verify credential retrieval works
                secrets_result = await self.get_tunnel_secrets(
                    source=source,
                    cloudflare_token=cloudflare_token,
                    cloudflare_account_id=cloudflare_account_id,
                    zone_name=cloudflare_zone,
                    terraform_version=terraform_version,
                    state_dir=cf_state_for_secrets,
                    output_format="json",
                )

                # Verify the result is valid JSON
                secrets_data = json.loads(secrets_result)

                # Validate required fields exist
                assert "tunnel_tokens" in secrets_data, "Missing tunnel_tokens in response"
                assert "credentials_json" in secrets_data, "Missing credentials_json in response"
                assert "count" in secrets_data, "Missing count in response"

                # Verify tokens are non-empty strings
                for mac, token in secrets_data["tunnel_tokens"].items():
                    assert isinstance(token, str), f"Token for {mac} is not a string"
                    assert len(token) > 0, f"Token for {mac} is empty"

                # Verify credentials contain required fields
                for mac, creds in secrets_data["credentials_json"].items():
                    assert "AccountTag" in creds, f"Missing AccountTag for {mac}"
                    assert "TunnelID" in creds, f"Missing TunnelID for {mac}"
                    assert "TunnelName" in creds, f"Missing TunnelName for {mac}"
                    assert "TunnelSecret" in creds, f"Missing TunnelSecret for {mac}"

                report_lines.append(f"  ✓ Retrieved secrets for {secrets_data['count']} tunnel(s)")
                report_lines.append(f"  ✓ Verified tunnel_tokens format")
                report_lines.append(f"  ✓ Verified credentials_json contains required fields")
                validation_results["secrets_retrieval"] = "success"

                # Also test human-readable format
                secrets_human = await self.get_tunnel_secrets(
                    source=source,
                    cloudflare_token=cloudflare_token,
                    cloudflare_account_id=cloudflare_account_id,
                    zone_name=cloudflare_zone,
                    terraform_version=terraform_version,
                    state_dir=cf_state_for_secrets,
                    output_format="human",
                )

                assert "CLOUDFLARE TUNNEL SECRETS" in secrets_human
                assert "TUNNEL TOKENS" in secrets_human
                assert "CREDENTIALS JSON" in secrets_human
                report_lines.append(f"  ✓ Human-readable format verified")
                validation_results["secrets_human_format"] = "success"

            except json.JSONDecodeError as e:
                error_msg = f"Secrets retrieval returned invalid JSON: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["secrets_retrieval"] = f"failed: {error_msg}"
            except AssertionError as e:
                error_msg = f"Secrets validation failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["secrets_retrieval"] = f"failed: {error_msg}"
            except Exception as e:
                error_msg = f"Secrets retrieval failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["secrets_retrieval"] = f"failed: {error_msg}"

            # Phase 5: Resource Validation
            report_lines.append("")
            report_lines.append("PHASE 5: Validating resources...")

            # Create validation container with curl and jq for API calls
            validate_ctr = dagger.dag.container().from_("alpine/curl:latest")
            validate_ctr = validate_ctr.with_exec(["apk", "add", "--no-cache", "jq"])

            # Cloudflare API Validation
            # Required permissions: Zone:Read, DNS Records:Read, Cloudflare Tunnel:Read
            try:
                # Validate Cloudflare tunnel via API
                tunnel_list_result = await validate_ctr.with_exec([
                    "sh", "-c",
                    f'curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/cfd_tunnel?name={tunnel_name}" \
                     -H "Authorization: Bearer {cf_token_plain}" \
                     -H "Content-Type: application/json"'
                ]).stdout()

                # Parse result to check if tunnel exists
                tunnel_count = await validate_ctr.with_exec([
                    "sh", "-c",
                    f'echo {shlex.quote(tunnel_list_result)} | jq \'.result | length\''
                ]).stdout()

                if tunnel_count.strip() == "1":
                    report_lines.append(f"  ✓ Cloudflare tunnel validated: {tunnel_name}")
                    validation_results["cloudflare_tunnel"] = "validated"
                else:
                    report_lines.append(f"  ✗ Cloudflare tunnel not found: {tunnel_name}")
                    validation_results["cloudflare_tunnel"] = "not_found"
            except Exception as e:
                report_lines.append(f"  ✗ Cloudflare tunnel validation failed: {str(e)}")
                validation_results["cloudflare_tunnel"] = f"error: {str(e)}"

            # Validate Cloudflare DNS record via API
            try:
                # First get zone ID from zone name
                zone_list_result = await validate_ctr.with_exec([
                    "sh", "-c",
                    f'curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name={cloudflare_zone}" \
                     -H "Authorization: Bearer {cf_token_plain}" \
                     -H "Content-Type: application/json"'
                ]).stdout()

                # Extract zone ID
                zone_id = await validate_ctr.with_exec([
                    "sh", "-c",
                    f'echo {shlex.quote(zone_list_result)} | jq -r \'.result[0].id\''
                ]).stdout()

                if zone_id and zone_id.strip() != "null":
                    # Query DNS records for the hostname
                    dns_record_result = await validate_ctr.with_exec([
                        "sh", "-c",
                        f'curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id.strip()}/dns_records?name={test_hostname}" \
                         -H "Authorization: Bearer {cf_token_plain}" \
                         -H "Content-Type: application/json"'
                    ]).stdout()

                    # Check if record exists
                    dns_count = await validate_ctr.with_exec([
                        "sh", "-c",
                        f'echo {shlex.quote(dns_record_result)} | jq \'.result | length\''
                    ]).stdout()

                    if dns_count.strip() == "1":
                        report_lines.append(f"  ✓ Cloudflare DNS validated: {test_hostname}")
                        validation_results["cloudflare_dns"] = "validated"
                    else:
                        report_lines.append(f"  ✗ Cloudflare DNS not found: {test_hostname}")
                        validation_results["cloudflare_dns"] = "not_found"
                else:
                    report_lines.append(f"  ✗ Could not find zone: {cloudflare_zone}")
                    validation_results["cloudflare_dns"] = "zone_not_found"
            except Exception as e:
                report_lines.append(f"  ✗ Cloudflare DNS validation failed: {str(e)}")
                validation_results["cloudflare_dns"] = f"error: {str(e)}"

            # UniFi Validation (uses Terraform success as proxy due to API complexity)
            try:
                # UniFi API validation is complex due to authentication requirements
                # For integration testing, we validate based on Terraform apply success
                if validation_results.get("unifi_dns") == "created":
                    report_lines.append(f"  ✓ UniFi DNS validated (Terraform apply succeeded)")
                    validation_results["unifi_validation"] = "validated"
                else:
                    report_lines.append(f"  ○ UniFi DNS validation skipped (creation may have failed)")
                    validation_results["unifi_validation"] = "skipped"
            except Exception as e:
                report_lines.append(f"  ○ UniFi validation skipped: {str(e)}")
                validation_results["unifi_validation"] = f"skipped: {str(e)}"

            # Optional connectivity check (future enhancement)
            if validate_connectivity:
                report_lines.append("  ○ HTTP connectivity check skipped (would test actual connectivity)")
                validation_results["connectivity"] = "skipped"

            # Validation summary based on actual API responses
            cf_success = validation_results.get("cloudflare_tunnel") == "validated" and \
                         validation_results.get("cloudflare_dns") == "validated"

            report_lines.append("")
            report_lines.append("-" * 60)
            if cf_success:
                report_lines.append("VALIDATION SUMMARY: ✓ CLOUDFLARE RESOURCES VALIDATED")
            else:
                report_lines.append("VALIDATION SUMMARY: ✗ SOME RESOURCES NOT FOUND")
            report_lines.append("-" * 60)

            # Phase 5.5: Wait before cleanup (if enabled)
            if wait_before_cleanup > 0:
                report_lines.append("")
                report_lines.append(f"PHASE 5.5: Waiting {wait_before_cleanup}s before cleanup...")
                report_lines.append("  (Use this time to manually verify created resources)")
                await asyncio.sleep(wait_before_cleanup)
                report_lines.append(f"  ✓ Wait completed ({wait_before_cleanup}s)")

        except Exception as e:
            report_lines.append("")
            report_lines.append(f"✗ ERROR DURING TEST: {str(e)}")
            validation_results["error"] = str(e)

        finally:
            # Phase 6: Guaranteed Cleanup
            if cleanup:
                report_lines.append("")
                report_lines.append("PHASE 5: Cleanup (guaranteed execution)...")

                # Cleanup Cloudflare resources first (reverse order of creation)
                # NOTE: Implements retry logic for Cloudflare provider issue #5255
                # where tunnel deletion fails on first attempt due to "active connections"
                report_lines.append("  Cleaning up Cloudflare resources...")
                last_error = None
                cf_cleanup_success = False

                try:
                    # Create Cloudflare cleanup container
                    cf_cleanup_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

                    # Mount Cloudflare config at /workspace
                    cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/workspace", cloudflare_dir)

                    # Mount the Cloudflare Tunnel Terraform module
                    try:
                        tf_module = source.directory("terraform/modules/cloudflare-tunnel")
                        cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
                    except Exception:
                        # If module not in source, try project root
                        try:
                            tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
                            cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
                        except Exception:
                            raise RuntimeError("Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel")

                    # Mount preserved state file if available
                    if cloudflare_state_dir:
                        try:
                            # Extract state file from directory and mount it without overwriting module files
                            cf_state_file = cloudflare_state_dir.file("terraform.tfstate")
                            cf_cleanup_ctr = cf_cleanup_ctr.with_file("/module/terraform.tfstate", cf_state_file)
                            report_lines.append("    ✓ Cloudflare state file mounted for state-based destroy")
                        except Exception as e:
                            report_lines.append(f"    ⚠ Failed to mount Cloudflare state file: {str(e)}")
                            cloudflare_state_dir = None
                    else:
                        report_lines.append("    ⚠ No state file available for Cloudflare cleanup")

                    # Set environment variables
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_zone_name", cloudflare_zone)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

                    # Pass Cloudflare token as secret (both as TF variable and env var for provider auth)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

                    # Set working directory to module
                    cf_cleanup_ctr = cf_cleanup_ctr.with_workdir("/module")

                    # Execute terraform init (no retry for init failures - fail fast)
                    try:
                        await cf_cleanup_ctr.with_exec(["terraform", "init"]).stdout()
                    except dagger.ExecError as e:
                        raise RuntimeError(f"Terraform init failed: {str(e)}")

                    # Execute terraform destroy with retry logic
                    # Retry is needed due to Cloudflare provider issue #5255
                    for attempt in range(1, 3):  # 2 attempts max
                        try:
                            destroy_result = await cf_cleanup_ctr.with_exec([
                                "terraform", "destroy", "-auto-approve"
                            ]).stdout()

                            if attempt == 1:
                                report_lines.append(f"    ✓ Destroyed tunnel: {tunnel_name}")
                                report_lines.append(f"    ✓ Deleted DNS record: {test_hostname}")
                                cleanup_status["cloudflare"] = "success"
                            else:
                                report_lines.append(f"    ✓ Destroy succeeded on retry")
                                cleanup_status["cloudflare"] = "success_after_retry"
                            cf_cleanup_success = True
                            break  # Success, exit retry loop

                        except dagger.ExecError as e:
                            last_error = str(e)
                            if attempt == 1:
                                report_lines.append("    First destroy attempt failed, retrying in 5 seconds...")
                                await asyncio.sleep(5)
                            else:
                                # Second attempt failed - provide manual cleanup instructions
                                cleanup_status["cloudflare"] = "failed_needs_manual_cleanup"
                                report_lines.append("    ✗ Cloudflare cleanup failed after 2 attempts")
                                report_lines.append("")
                                report_lines.append("    The following resources may need manual deletion via Cloudflare Dashboard:")
                                report_lines.append(f"      - Tunnel: {tunnel_name}")
                                report_lines.append(f"      - DNS Record: {test_hostname}")
                                report_lines.append("")
                                report_lines.append("    Manual cleanup steps:")
                                report_lines.append("      1. Visit https://dash.cloudflare.com/ > Zero Trust > Networks > Tunnels")
                                report_lines.append(f"      2. Find and delete tunnel: {tunnel_name}")
                                report_lines.append(f"      3. Visit DNS > Records for zone {cloudflare_zone}")
                                report_lines.append(f"      4. Delete CNAME record: {test_hostname}")
                                report_lines.append("")
                                report_lines.append(f"    Original error: {last_error}")

                except Exception as e:
                    cleanup_status["cloudflare"] = f"failed: {str(e)}"
                    report_lines.append(f"    ✗ Failed to cleanup Cloudflare: {str(e)}")

                # Cleanup UniFi resources second
                report_lines.append("  Cleaning up UniFi resources...")
                try:
                    # Create UniFi cleanup container
                    unifi_cleanup_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

                    # Mount UniFi config at /workspace
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_directory("/workspace", unifi_dir)

                    # Mount the UniFi DNS Terraform module
                    try:
                        tf_module = source.directory("terraform/modules/unifi-dns")
                        unifi_cleanup_ctr = unifi_cleanup_ctr.with_directory("/module", tf_module)
                    except Exception:
                        # If module not in source, try project root
                        try:
                            tf_module = dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")
                            unifi_cleanup_ctr = unifi_cleanup_ctr.with_directory("/module", tf_module)
                        except Exception:
                            raise RuntimeError("UniFi DNS Terraform module not found at terraform/modules/unifi-dns")

                    # Mount preserved state file if available
                    if unifi_state_dir:
                        try:
                            # Extract state file from directory and mount it without overwriting module files
                            unifi_state_file = unifi_state_dir.file("terraform.tfstate")
                            unifi_cleanup_ctr = unifi_cleanup_ctr.with_file("/module/terraform.tfstate", unifi_state_file)
                            report_lines.append("    ✓ UniFi state file mounted for state-based destroy")
                        except Exception as e:
                            report_lines.append(f"    ⚠ Failed to mount UniFi state file: {str(e)}")
                            unifi_state_dir = None
                    else:
                        report_lines.append("    ⚠ No state file available for UniFi cleanup")

                    # Set environment variables
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_api_url", api_url if api_url else unifi_url)
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())

                    # Pass authentication credentials as secrets
                    if unifi_api_key:
                        unifi_cleanup_ctr = unifi_cleanup_ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
                    elif unifi_username and unifi_password:
                        unifi_cleanup_ctr = unifi_cleanup_ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
                        unifi_cleanup_ctr = unifi_cleanup_ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

                    # Set working directory to module
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_workdir("/module")

                    # Execute terraform init
                    try:
                        await unifi_cleanup_ctr.with_exec(["terraform", "init"]).stdout()
                    except dagger.ExecError as e:
                        raise RuntimeError(f"Terraform init failed: {str(e)}")

                    # Execute terraform destroy
                    try:
                        destroy_result = await unifi_cleanup_ctr.with_exec([
                            "terraform", "destroy", "-auto-approve"
                        ]).stdout()
                        report_lines.append(f"    ✓ Deleted UniFi DNS record: {unifi_hostname}")
                        cleanup_status["unifi"] = "success"
                    except dagger.ExecError as e:
                        raise RuntimeError(f"Terraform destroy failed: {str(e)}")
                except Exception as e:
                    cleanup_status["unifi"] = f"failed: {str(e)}"
                    report_lines.append(f"    ✗ Failed to cleanup UniFi: {str(e)}")

                # Cleanup local state files (state is container-local, so just document)
                report_lines.append("  Cleaning up local state files...")
                report_lines.append("    ✓ Terraform state is container-local (automatically cleaned up)")
                cleanup_status["state_files"] = "success"

                # Cleanup summary with warnings
                report_lines.append("")
                report_lines.append("-" * 60)
                report_lines.append("CLEANUP SUMMARY")
                report_lines.append("-" * 60)
                report_lines.append(f"  Cloudflare: {cleanup_status['cloudflare']}")
                report_lines.append(f"  UniFi: {cleanup_status['unifi']}")
                report_lines.append(f"  State Files: {cleanup_status['state_files']}")

                # Display warning if any cleanup step failed
                if not all(status == "success" for status in cleanup_status.values()):
                    report_lines.append("")
                    report_lines.append("⚠ WARNING: Some cleanup steps failed!")
                    report_lines.append("  Manual cleanup may be required:")
                    if cleanup_status["cloudflare"] != "success":
                        report_lines.append(f"    - Check Cloudflare dashboard for remaining resources: {tunnel_name}, {test_hostname}")
                    if cleanup_status["unifi"] != "success":
                        report_lines.append(f"    - Check UniFi controller for remaining DNS record: {unifi_hostname}")
            else:
                report_lines.append("")
                report_lines.append("PHASE 5: Cleanup SKIPPED (cleanup=false)")
                report_lines.append("  WARNING: Resources may still exist!")
                cleanup_status = {"cloudflare": "skipped", "unifi": "skipped", "state_files": "skipped"}

        # Final summary
        report_lines.append("")
        report_lines.append("=" * 60)
        report_lines.append("FINAL SUMMARY")
        report_lines.append("=" * 60)
        report_lines.append(f"Test ID: {test_id}")
        report_lines.append(f"Resources Created:")
        report_lines.append(f"  - Tunnel: {tunnel_name}")
        report_lines.append(f"  - External DNS: {test_hostname}")
        report_lines.append(f"  - Internal DNS: {unifi_hostname}")
        report_lines.append(f"")
        report_lines.append(f"Validation Results:")
        for key, value in validation_results.items():
            report_lines.append(f"  - {key}: {value}")
        report_lines.append(f"")
        report_lines.append(f"Cleanup Status: {'COMPLETED' if cleanup else 'SKIPPED'}")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    @function
    async def get_tunnel_secrets(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory (for accessing terraform modules)")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token for authentication")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
        zone_name: Annotated[str, Doc("DNS zone name (e.g., example.com)")],
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
        output_format: Annotated[str, Doc("Output format: 'human' for readable text, 'json' for machine-parseable")] = "human",
    ) -> str:
        """
        Retrieve Cloudflare tunnel secrets from Terraform state.

        This function extracts tunnel tokens and credentials from Terraform state
        after deployment, enabling configuration of cloudflared on devices.

        State Management (must match deployment configuration):
        1. Ephemeral (default): State stored in container from previous deploy
        2. Persistent Local: Use --state-dir=./terraform-state where state was saved
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... to access remote state

        Args:
            source: Source directory containing Terraform modules
            cloudflare_token: Cloudflare API Token for authentication
            cloudflare_account_id: Cloudflare Account ID
            zone_name: DNS zone name
            terraform_version: Terraform version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (must match deployment)
            output_format: Output format - 'human' for readable text, 'json' for automation

        Returns:
            Tunnel secrets in requested format (human-readable or JSON)

        Example:
            # Retrieve secrets with local ephemeral state (default)
            dagger call get-tunnel-secrets \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com

            # Retrieve secrets from persistent state directory
            dagger call get-tunnel-secrets \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --state-dir=./terraform-state

            # Retrieve secrets from remote backend (S3) using HCL config
            dagger call get-tunnel-secrets \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --backend-type=s3 \\
                --backend-config-file=./s3-backend.hcl

            # Retrieve secrets using YAML backend config (auto-converted)
            dagger call get-tunnel-secrets \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --backend-type=s3 \\
                --backend-config-file=./s3-backend.yaml

            # Get JSON output for automation
            dagger call get-tunnel-secrets \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --output-format=json
        """
        try:
            # Validate output format
            if output_format not in ["human", "json"]:
                return (
                    "✗ Failed: Invalid output format. Must be 'human' or 'json'\n\n"
                    "Example:\n"
                    "  dagger call get-tunnel-secrets \\\n"
                    "      --source=. \\\n"
                    "      --cloudflare-token=env:CF_TOKEN \\\n"
                    "      --cloudflare-account-id=xxx \\\n"
                    "      --zone-name=example.com \\\n"
                    "      --output-format=json"
                )

            # Validate backend configuration (reuse existing helper)
            is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
            if not is_valid:
                return error_msg

            # Validate state storage configuration (reuse existing helper)
            is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
            if not is_valid:
                return error_msg

            # Check if state directory exists when provided
            if state_dir is not None:
                try:
                    # Try to access the directory to verify it exists
                    _ = await state_dir.entries()
                except Exception:
                    return "✗ Failed: State directory not found. Check --state-dir path."

            # Create Terraform container
            tf_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

            # Mount source directory at /src
            tf_ctr = tf_ctr.with_directory("/src", source)

            # Mount the Cloudflare Tunnel Terraform module
            try:
                tf_module = source.directory("terraform/modules/cloudflare-tunnel")
                tf_ctr = tf_ctr.with_directory("/module", tf_module)
            except Exception:
                # If module not in source, try project root
                try:
                    tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
                    tf_ctr = tf_ctr.with_directory("/module", tf_module)
                except Exception:
                    return "✗ Failed: Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel"

            # Generate and mount backend.tf if using remote backend
            if backend_type != "local":
                try:
                    backend_hcl = self._generate_backend_block(backend_type)
                    tf_ctr = tf_ctr.with_new_file("/module/backend.tf", backend_hcl)
                except Exception as e:
                    return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

            # Process and mount backend config file if provided
            if backend_config_file is not None:
                try:
                    # Convert YAML to HCL if necessary
                    config_content, _ = await _process_backend_config(backend_config_file)
                    # Mount the processed content as a .tfbackend file
                    tf_ctr = tf_ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
                except Exception as e:
                    return f"✗ Failed: Could not process backend config file\n{str(e)}"

            # Set up environment variables for Cloudflare provider
            tf_ctr = tf_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
            tf_ctr = tf_ctr.with_env_variable("TF_VAR_zone_name", zone_name)
            tf_ctr = tf_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
            tf_ctr = tf_ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

            # Handle state directory mounting for persistent local state
            using_persistent_state = state_dir is not None
            if using_persistent_state:
                # Mount state directory
                tf_ctr = tf_ctr.with_directory("/state", state_dir)
                # Copy module files to state directory
                tf_ctr = tf_ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
                # Set working directory to state directory
                tf_ctr = tf_ctr.with_workdir("/state")
            else:
                # Set working directory to module
                tf_ctr = tf_ctr.with_workdir("/module")

            # Run terraform init
            init_cmd = ["terraform", "init"]
            if backend_config_file is not None:
                init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

            try:
                tf_ctr = tf_ctr.with_exec(init_cmd)
                _ = await tf_ctr.stdout()
            except dagger.ExecError as e:
                error_msg = f"✗ Failed: Terraform init failed\n{str(e)}"
                if backend_type != "local":
                    error_msg += (
                        "\n\nEnsure backend-type matches your deployment.\n"
                        "Backend configuration troubleshooting:\n"
                        "  - Verify backend config file is valid HCL\n"
                        "  - Check credentials in environment variables\n"
                        "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                    )
                return error_msg

            # Run terraform output to get tunnel_tokens
            try:
                tf_ctr = tf_ctr.with_exec(["terraform", "output", "-json", "tunnel_tokens"])
                tokens_json_str = await tf_ctr.stdout()
            except dagger.ExecError as e:
                error_str = str(e)
                if "No outputs found" in error_str or "output" in error_str.lower():
                    return "✗ Failed: No tunnels found in Terraform outputs. State may be corrupted."
                elif "state" in error_str.lower() or "tfstate" in error_str.lower():
                    return "✗ Failed: No Terraform state found. Have you run deploy-cloudflare yet?"
                else:
                    return f"✗ Failed: Could not retrieve tunnel tokens\n{str(e)}"

            # Run terraform output to get credentials_json
            try:
                tf_ctr = tf_ctr.with_exec(["terraform", "output", "-json", "credentials_json"])
                credentials_json_str = await tf_ctr.stdout()
            except dagger.ExecError as e:
                error_str = str(e)
                if "No outputs found" in error_str or "output" in error_str.lower():
                    return "✗ Failed: No tunnels found in Terraform outputs. State may be corrupted."
                else:
                    return f"✗ Failed: Could not retrieve credentials\n{str(e)}"

            # Parse JSON outputs
            try:
                tunnel_tokens = json.loads(tokens_json_str.strip())
                credentials = json.loads(credentials_json_str.strip())
            except json.JSONDecodeError as e:
                return f"✗ Failed: Could not parse Terraform output as JSON\n{str(e)}"

            # Validate that we have data
            if not tunnel_tokens or not credentials:
                return "✗ Failed: No tunnels found in Terraform outputs. State may be corrupted."

            # Format and return output
            if output_format == "json":
                result = {
                    "tunnel_tokens": tunnel_tokens,
                    "credentials_json": credentials,
                    "count": len(tunnel_tokens)
                }
                return json.dumps(result, indent=2)
            else:
                # Human-readable format
                output_lines = [
                    "=" * 60,
                    "CLOUDFLARE TUNNEL SECRETS",
                    "=" * 60,
                    "",
                    f"Zone: {zone_name}",
                    f"Total Tunnels: {len(tunnel_tokens)}",
                    "",
                    "-" * 60,
                    "TUNNEL TOKENS (for cloudflared login)",
                    "-" * 60,
                    "",
                ]

                for mac, token in tunnel_tokens.items():
                    output_lines.append(f"MAC Address: {mac}")
                    output_lines.append(f"Token: {token}")
                    output_lines.append("")

                output_lines.extend([
                    "-" * 60,
                    "CREDENTIALS JSON (for cloudflared config.yml)",
                    "-" * 60,
                    "",
                ])

                for mac, creds in credentials.items():
                    output_lines.append(f"MAC Address: {mac}")
                    output_lines.append(f"  Account Tag: {creds.get('AccountTag', 'N/A')}")
                    output_lines.append(f"  Tunnel ID: {creds.get('TunnelID', 'N/A')}")
                    output_lines.append(f"  Tunnel Name: {creds.get('TunnelName', 'N/A')}")
                    output_lines.append(f"  Tunnel Secret: {creds.get('TunnelSecret', 'N/A')}")
                    output_lines.append("")

                output_lines.extend([
                    "-" * 60,
                    "USAGE INSTRUCTIONS",
                    "-" * 60,
                    "",
                    "1. Install cloudflared on your device:",
                    "   https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/",
                    "",
                    "2. Authenticate using tunnel token (interactive):",
                    "   cloudflared tunnel login",
                    "",
                    "3. Or use credentials JSON for automated setup:",
                    "   Create /etc/cloudflared/config.yml with the credentials above",
                    "",
                    "4. Run cloudflared:",
                    "   cloudflared tunnel run",
                    "",
                    "=" * 60,
                ])

                return "\n".join(output_lines)

        except Exception as e:
            return f"✗ Failed: Unexpected error retrieving tunnel secrets\n{str(e)}"
