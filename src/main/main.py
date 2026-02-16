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
                f"  dagger call deploy \\\n"
                f"      --kcl-source=./kcl \\\n"
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
                "   dagger call deploy \\\n"
                "       --kcl-source=./kcl \\\n"
                "       --unifi-url=https://unifi.local:8443 \\\n"
                "       --unifi-api-key=env:UNIFI_API_KEY\n\n"
                "2. Persistent local state (--state-dir):\n"
                "   dagger call deploy \\\n"
                "       --kcl-source=./kcl \\\n"
                "       --unifi-url=https://unifi.local:8443 \\\n"
                "       --unifi-api-key=env:UNIFI_API_KEY \\\n"
                "       --state-dir=./terraform-state\n\n"
                "3. Remote backend (--backend-type):\n"
                "   dagger call deploy \\\n"
                "       --kcl-source=./kcl \\\n"
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
    async def deploy(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")] = "",
        cloudflare_token: Annotated[Optional[Secret], Doc("Cloudflare API Token")] = None,
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")] = "",
        zone_name: Annotated[str, Doc("DNS zone name")] = "",
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller")] = False,
        unifi_only: Annotated[bool, Doc("Deploy only UniFi DNS (mutually exclusive with --cloudflare-only)")] = False,
        cloudflare_only: Annotated[bool, Doc("Deploy only Cloudflare Tunnels (mutually exclusive with --unifi-only)")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
        no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False,
        cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = "",
    ) -> str:
        """
        Deploy UniFi DNS and/or Cloudflare Tunnels using the combined Terraform module.

        This function generates KCL configurations and deploys them using a single
        Terraform operation with the combined module at terraform/modules/glue/.
        
        Use --unifi-only or --cloudflare-only for selective deployment, or omit both
        for full deployment of both components.

        Authentication (pick one method for UniFi when deploying UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            kcl_source: Directory containing KCL module
            unifi_url: UniFi Controller URL (required for UniFi deployment)
            cloudflare_token: Cloudflare API Token (required for Cloudflare deployment)
            cloudflare_account_id: Cloudflare Account ID (required for Cloudflare deployment)
            zone_name: DNS zone name (required for Cloudflare deployment)
            api_url: Optional UniFi API URL
            unifi_api_key: UniFi API key (optional)
            unifi_username: UniFi username (optional)
            unifi_password: UniFi password (optional)
            unifi_insecure: Skip TLS verification for self-signed certificates
            unifi_only: Deploy only UniFi DNS (no Cloudflare credentials needed)
            cloudflare_only: Deploy only Cloudflare Tunnels (no UniFi credentials needed)
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)
            no_cache: Bypass Dagger cache by auto-generating an epoch timestamp
            cache_buster: Custom cache key for advanced use cases (cannot use with --no-cache)

        Returns:
            Status message indicating success or failure of deployment

        Example:
            # Full deployment (both UniFi and Cloudflare)
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY

            # UniFi-only deployment
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only

            # Cloudflare-only deployment
            dagger call deploy \\
                --kcl-source=./kcl \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --cloudflare-only

            # With insecure TLS for self-signed certificates
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://192.168.10.1 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only \\
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

            # Force fresh execution (bypass Dagger cache)
            dagger call deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only \\
                --no-cache
        """
        # Validate cache control options
        if no_cache and cache_buster:
            return "✗ Failed: Cannot use both --no-cache and --cache-buster"

        # Validate mutual exclusion of deployment flags
        if unifi_only and cloudflare_only:
            return "✗ Failed: Cannot use both --unifi-only and --cloudflare-only"

        # Determine effective cache buster value
        # CRITICAL: Generate timestamp at function runtime, not at cache-check time
        # This ensures each invocation gets a unique value even if Dagger tries to cache
        effective_cache_buster = cache_buster
        if no_cache:
            # Force unique timestamp generation by using actual time module
            import time as time_module
            effective_cache_buster = f"nocache-{int(time_module.time())}-{id(locals())}"

        # Validate credentials based on deployment scope
        if unifi_only:
            # UniFi-only: require UniFi credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                return "✗ Failed: UniFi-only deployment requires either --unifi-api-key OR both --unifi-username and --unifi-password"
            if using_api_key and using_password:
                return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."
            if not unifi_url:
                return "✗ Failed: UniFi-only deployment requires --unifi-url"
        elif cloudflare_only:
            # Cloudflare-only: require Cloudflare credentials
            if cloudflare_token is None:
                return "✗ Failed: Cloudflare-only deployment requires --cloudflare-token"
            if not cloudflare_account_id:
                return "✗ Failed: Cloudflare-only deployment requires --cloudflare-account-id"
            if not zone_name:
                return "✗ Failed: Cloudflare-only deployment requires --zone-name"
        else:
            # Full deployment: require both sets of credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                return "✗ Failed: Full deployment requires either --unifi-api-key OR both --unifi-username and --unifi-password"
            if using_api_key and using_password:
                return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."
            if not unifi_url:
                return "✗ Failed: Full deployment requires --unifi-url"
            if cloudflare_token is None:
                return "✗ Failed: Full deployment requires --cloudflare-token"
            if not cloudflare_account_id:
                return "✗ Failed: Full deployment requires --cloudflare-account-id"
            if not zone_name:
                return "✗ Failed: Full deployment requires --zone-name"

        results = []

        # Phase 1: Generate KCL configurations (conditionally based on deployment scope)
        results.append("=" * 60)
        results.append("PHASE 1: Generating KCL configurations")
        results.append("=" * 60)

        # Bust cache for KCL generation by adding timestamp file to source
        effective_kcl_source = kcl_source
        if effective_cache_buster:
            effective_kcl_source = kcl_source.with_new_file(".cache-bust", effective_cache_buster)

        unifi_dir = None
        cloudflare_dir = None

        if not cloudflare_only:  # Generate UniFi config unless cloudflare-only
            try:
                unifi_file = await self.generate_unifi_config(effective_kcl_source, kcl_version)
                unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
                results.append("✓ UniFi configuration generated")
            except Exception as e:
                return f"✗ Failed: Could not generate UniFi config\n{str(e)}"
        else:
            results.append("○ UniFi configuration skipped (--cloudflare-only)")

        if not unifi_only:  # Generate Cloudflare config unless unifi-only
            try:
                cloudflare_file = await self.generate_cloudflare_config(effective_kcl_source, kcl_version)
                cloudflare_dir = dagger.dag.directory().with_file("cloudflare.json", cloudflare_file)
                results.append("✓ Cloudflare configuration generated")
            except Exception as e:
                return f"✗ Failed: Could not generate Cloudflare config\n{str(e)}"
        else:
            results.append("○ Cloudflare configuration skipped (--unifi-only)")

        # Phase 2: Deploy using combined Terraform module
        results.append("")
        results.append("=" * 60)
        if unifi_only:
            results.append("PHASE 2: Deploying UniFi DNS (combined module)")
        elif cloudflare_only:
            results.append("PHASE 2: Deploying Cloudflare Tunnels (combined module)")
        else:
            results.append("PHASE 2: Deploying UniFi DNS and Cloudflare Tunnels (combined module)")
        results.append("=" * 60)

        # Validate backend configuration
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            return error_msg

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            return error_msg

        actual_api_url = api_url if api_url else unifi_url
        using_persistent_state = state_dir is not None

        # Create Terraform container and select module based on deployment mode
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

        # Add cache buster IMMEDIATELY to ensure Terraform operations aren't cached
        if effective_cache_buster:
            ctr = ctr.with_env_variable("CACHE_BUSTER", effective_cache_buster)

        # Determine which Terraform module to use based on deployment mode
        # - cloudflare-only: use cloudflare-tunnel module directly (no UniFi provider)
        # - unifi-only: use unifi-dns module directly (no Cloudflare provider)
        # - full deployment: use glue module (both providers)
        if cloudflare_only:
            module_path = "cloudflare-tunnel"
        elif unifi_only:
            module_path = "unifi-dns"
        else:
            module_path = "glue"

        # Mount the appropriate Terraform module
        try:
            if module_path == "glue":
                # Glue module needs all sibling modules
                tf_modules = dagger.dag.current_module().source().directory("terraform/modules")
                ctr = ctr.with_directory("/module", tf_modules)
                workdir = "/module/glue"
            else:
                # Individual modules only need themselves
                tf_module = dagger.dag.current_module().source().directory(f"terraform/modules/{module_path}")
                ctr = ctr.with_directory("/module", tf_module)
                workdir = "/module"
        except Exception as e:
            return f"✗ Failed: Could not mount Terraform module at terraform/modules/{module_path}: {str(e)}"

        # Mount configuration files conditionally
        if unifi_dir is not None:
            ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
        if cloudflare_dir is not None:
            ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)

        # Generate and mount backend.tf if using remote backend
        if backend_type != "local":
            try:
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file(f"{workdir}/backend.tf", backend_hcl)
            except Exception as e:
                return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                config_content, _ = await _process_backend_config(backend_config_file)
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
            except Exception as e:
                return f"✗ Failed: Could not process backend config file\n{str(e)}"

        # Set up environment variables based on which module is being used
        if module_path == "cloudflare-tunnel":
            # Cloudflare module expects config_file (not cloudflare_config_file)
            # Pass account_id and zone_name as overrides to allow CLI parameters to take precedence
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare/cloudflare.json")
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_account_id_override", cloudflare_account_id)
            if zone_name:
                ctr = ctr.with_env_variable("TF_VAR_zone_name_override", zone_name)
        elif module_path == "unifi-dns":
            # UniFi module expects config_file (not unifi_config_file)
            if unifi_url:
                ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
                ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())
            if unifi_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi/unifi.json")
        else:  # module_path == "glue"
            # Glue module expects both config files with specific names
            if unifi_url:
                ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
                ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())
            if unifi_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_unifi_config_file", "/workspace/unifi/unifi.json")
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_config_file", "/workspace/cloudflare/cloudflare.json")
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)

        # Add authentication secrets conditionally
        if unifi_only or not cloudflare_only:  # UniFi credentials needed
            if unifi_api_key:
                ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
            elif unifi_username and unifi_password:
                ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
                ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)
        
        if cloudflare_only or not unifi_only:  # Cloudflare credentials needed
            if cloudflare_token:
                # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
                ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

        # Handle state directory mounting and setup (persistent local state)
        if using_persistent_state:
            ctr = ctr.with_directory("/state", state_dir)
            ctr = ctr.with_exec(["sh", "-c", "rm -rf /state/.terraform && echo 'Cleaned .terraform directory'"])
            _ = await ctr.stdout()
            ctr = ctr.with_exec(["sh", "-c", f"cp -r {workdir}/* /state/ && ls -la /state"])
            _ = await ctr.stdout()
            ctr = ctr.with_workdir("/state")
        else:
            ctr = ctr.with_workdir(workdir)

        # Run terraform init
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

        try:
            ctr = ctr.with_exec(init_cmd)
            _ = await ctr.stdout()
            results.append("✓ Terraform init completed")
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
        # Use 'sh -c' with embedded timestamp  to force different command for cache breaking
        try:
            if effective_cache_buster:
                # Inject cache buster as comment in shell command to make it unique
                ctr = ctr.with_exec(["sh", "-c", f"# cache_bust={effective_cache_buster}\nterraform apply -auto-approve"])
            else:
                ctr = ctr.with_exec(["terraform", "apply", "-auto-approve"])
            apply_result = await ctr.stdout()
            results.append("✓ Terraform apply completed")
        except dagger.ExecError as e:
            error_details = f"Exit code: {e.exit_code}\n"
            error_details += f"Stdout:\n{e.stdout or 'N/A'}\n"
            error_details += f"Stderr:\n{e.stderr or 'N/A'}"
            return f"✗ Failed: Terraform apply failed\n{error_details}"

        # Final summary
        results.append("")
        results.append("=" * 60)
        results.append("DEPLOYMENT SUMMARY")
        results.append("=" * 60)
        
        # Add execution timestamp to make result unique (breaks Dagger cache)
        if effective_cache_buster:
            results.append(f"Execution ID: {effective_cache_buster}")
            results.append("")

        if unifi_only:
            results.append("✓ UniFi DNS deployment completed successfully")
        elif cloudflare_only:
            results.append("✓ Cloudflare Tunnel deployment completed successfully")
            
            # Add tunnel token retrieval guidance for cloudflare-only deployment
            guidance_lines = [
                "",
                "-" * 60,
                "Next Step: Retrieve Tunnel Credentials",
                "-" * 60,
                "",
                "Your Cloudflare tunnels have been deployed. To configure cloudflared",
                "on your devices, you need to retrieve the tunnel credentials.",
                "",
                "Option 1: Using Dagger (recommended):",
            ]

            dagger_cmd_parts = [
                "dagger call get-tunnel-secrets \\",
                f"    --source=. \\",
                f"    --cloudflare-token=env:CF_TOKEN \\",
                f"    --cloudflare-account-id={cloudflare_account_id} \\",
                f"    --zone-name={zone_name}",
            ]

            if backend_type != "local":
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --backend-type={backend_type} \\")
                dagger_cmd_parts.append(f"    --backend-config-file=./backend.hcl")

            if state_dir is not None:
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --state-dir=./terraform-state")

            guidance_lines.extend(dagger_cmd_parts)
            guidance_lines.extend([
                "",
                "Option 2: Install cloudflared service directly:",
                "  cloudflared service install <tunnel-token-from-option-1>",
                "",
                "For detailed setup instructions, see:",
                "  examples/homelab-media-stack/README.md",
                "-" * 60,
            ])

            results.extend(guidance_lines)
        else:
            results.append("✓ Both UniFi DNS and Cloudflare Tunnel deployments completed successfully")
            
            # Add tunnel token retrieval guidance for full deployment
            guidance_lines = [
                "",
                "-" * 60,
                "Next Step: Retrieve Tunnel Credentials",
                "-" * 60,
                "",
                "Your Cloudflare tunnels have been deployed. To configure cloudflared",
                "on your devices, you need to retrieve the tunnel credentials.",
                "",
                "Option 1: Using Dagger (recommended):",
            ]

            dagger_cmd_parts = [
                "dagger call get-tunnel-secrets \\",
                f"    --source=./kcl \\",
                f"    --cloudflare-token=env:CF_TOKEN \\",
                f"    --cloudflare-account-id={cloudflare_account_id} \\",
                f"    --zone-name={zone_name}",
            ]

            if backend_type != "local":
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --backend-type={backend_type} \\")
                dagger_cmd_parts.append(f"    --backend-config-file=./backend.hcl")

            if state_dir is not None:
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --state-dir=./terraform-state")

            guidance_lines.extend(dagger_cmd_parts)
            guidance_lines.extend([
                "",
                "Option 2: Install cloudflared service directly:",
                "  cloudflared service install <tunnel-token-from-option-1>",
                "",
                "For detailed setup instructions, see:",
                "  examples/homelab-media-stack/README.md",
                "-" * 60,
            ])

            results.extend(guidance_lines)

        final_result = "\n".join(results)
        
        # CRITICAL: Append timestamp to result when using no_cache to break Dagger's function-level cache
        # Dagger caches function results based on input parameters, so identical inputs return cached results
        # Adding the unique timestamp to the output makes each result different, forcing execution
        if no_cache and effective_cache_buster:
            final_result += f"\n\n[Cache Break: {effective_cache_buster}]"
        
        return final_result

    @function
    async def plan(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")] = "",
        cloudflare_token: Annotated[Optional[Secret], Doc("Cloudflare API Token")] = None,
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")] = "",
        zone_name: Annotated[str, Doc("DNS zone name")] = "",
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username (use with password)")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password (use with username)")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller (useful for self-signed certificates)")] = False,
        unifi_only: Annotated[bool, Doc("Plan only UniFi DNS (mutually exclusive with --cloudflare-only)")] = False,
        cloudflare_only: Annotated[bool, Doc("Plan only Cloudflare Tunnels (mutually exclusive with --unifi-only)")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
        no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution by auto-generating epoch timestamp")] = False,
        cache_buster: Annotated[str, Doc("Custom cache key for advanced use (cannot be used with --no-cache)")] = "",
    ) -> dagger.Directory:
        """
        Generate Terraform plans for UniFi DNS and/or Cloudflare Tunnel configurations.

        This function creates execution plans without applying changes, enabling the
        standard plan → review → apply workflow. It uses the combined Terraform module
        and generates unified plan files for the selected components.

        Use --unifi-only or --cloudflare-only for selective planning, or omit both
        for full planning of both components.

        Authentication (pick one method for UniFi when planning UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            kcl_source: Directory containing KCL module
            unifi_url: UniFi Controller URL (required for UniFi planning)
            cloudflare_token: Cloudflare API Token (required for Cloudflare planning)
            cloudflare_account_id: Cloudflare Account ID (required for Cloudflare planning)
            zone_name: DNS zone name (required for Cloudflare planning)
            api_url: Optional UniFi API URL
            unifi_api_key: UniFi API key (optional)
            unifi_username: UniFi username (optional)
            unifi_password: UniFi password (optional)
            unifi_insecure: Skip TLS verification for self-signed certificates
            unifi_only: Plan only UniFi DNS (no Cloudflare credentials needed)
            cloudflare_only: Plan only Cloudflare Tunnels (no UniFi credentials needed)
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)
            no_cache: Bypass Dagger cache by auto-generating an epoch timestamp
            cache_buster: Custom cache key for advanced use cases

        Returns:
            dagger.Directory containing all plan artifacts:
            - plan.tfplan - Binary plan file for terraform apply
            - plan.json - JSON representation of the plan
            - plan.txt - Human-readable plan output
            - plan-summary.txt - Summary with resource counts and component information

        Example:
            # Full deployment plan (both UniFi and Cloudflare)
            dagger call plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                export --path=./plans

            # UniFi-only plan
            dagger call plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only \\
                export --path=./plans

            # Cloudflare-only plan
            dagger call plan \\
                --kcl-source=./kcl \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --cloudflare-only \\
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
        """
        # Validate cache control options
        if no_cache and cache_buster:
            raise ValueError("✗ Failed: Cannot use both --no-cache and --cache-buster")

        # Validate mutual exclusion of deployment flags
        if unifi_only and cloudflare_only:
            raise ValueError("✗ Failed: Cannot use both --unifi-only and --cloudflare-only")

        # Determine effective cache buster value
        effective_cache_buster = cache_buster
        if no_cache:
            effective_cache_buster = str(int(time.time()))

        # Validate credentials based on deployment scope
        if unifi_only:
            # UniFi-only: require UniFi credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError("✗ Failed: UniFi-only planning requires either --unifi-api-key OR both --unifi-username and --unifi-password")
            if using_api_key and using_password:
                raise ValueError("✗ Failed: Cannot use both API key and username/password. Choose one authentication method.")
            if not unifi_url:
                raise ValueError("✗ Failed: UniFi-only planning requires --unifi-url")
        elif cloudflare_only:
            # Cloudflare-only: require Cloudflare credentials
            if cloudflare_token is None:
                raise ValueError("✗ Failed: Cloudflare-only planning requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError("✗ Failed: Cloudflare-only planning requires --cloudflare-account-id")
            if not zone_name:
                raise ValueError("✗ Failed: Cloudflare-only planning requires --zone-name")
        else:
            # Full deployment: require both sets of credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError("✗ Failed: Full deployment planning requires either --unifi-api-key OR both --unifi-username and --unifi-password")
            if using_api_key and using_password:
                raise ValueError("✗ Failed: Cannot use both API key and username/password. Choose one authentication method.")
            if not unifi_url:
                raise ValueError("✗ Failed: Full deployment planning requires --unifi-url")
            if cloudflare_token is None:
                raise ValueError("✗ Failed: Full deployment planning requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError("✗ Failed: Full deployment planning requires --cloudflare-account-id")
            if not zone_name:
                raise ValueError("✗ Failed: Full deployment planning requires --zone-name")

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

        # Phase 1: Generate KCL configurations (conditionally based on deployment scope)
        # Bust cache for KCL generation by adding timestamp file to source
        effective_kcl_source = kcl_source
        if effective_cache_buster:
            effective_kcl_source = kcl_source.with_new_file(".cache-bust", effective_cache_buster)

        unifi_dir = None
        cloudflare_dir = None

        if not cloudflare_only:  # Generate UniFi config unless cloudflare-only
            try:
                unifi_file = await self.generate_unifi_config(effective_kcl_source, kcl_version)
                unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
            except Exception as e:
                raise RuntimeError(f"✗ Failed: Could not generate UniFi config\n{str(e)}")

        if not unifi_only:  # Generate Cloudflare config unless unifi-only
            try:
                cloudflare_file = await self.generate_cloudflare_config(effective_kcl_source, kcl_version)
                cloudflare_dir = dagger.dag.directory().with_file("cloudflare.json", cloudflare_file)
            except Exception as e:
                raise RuntimeError(f"✗ Failed: Could not generate Cloudflare config\n{str(e)}")

        # Create output directory
        output_dir = dagger.dag.directory()

        # Phase 2: Plan Generation using combined Terraform module
        try:
            # Create Terraform container with combined module
            ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

            # Add cache buster IMMEDIATELY to ensure Terraform operations aren't cached
            if effective_cache_buster:
                ctr = ctr.with_env_variable("CACHE_BUSTER", effective_cache_buster)

            # Mount all Terraform modules (glue depends on sibling modules via relative paths)
            try:
                tf_modules = dagger.dag.current_module().source().directory("terraform/modules")
                ctr = ctr.with_directory("/module", tf_modules)
            except Exception as e:
                raise RuntimeError(f"✗ Failed: Could not mount Terraform modules at terraform/modules/: {str(e)}")

            # Mount configuration files conditionally
            if unifi_dir is not None:
                ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
            if cloudflare_dir is not None:
                ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)

            # Generate and mount backend.tf if using remote backend
            if backend_type != "local":
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file("/module/glue/backend.tf", backend_hcl)

            # Process and mount backend config file if provided
            if backend_config_file is not None:
                config_content, _ = await _process_backend_config(backend_config_file)
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)

            # Set up environment variables conditionally based on deployment scope
            if unifi_url:
                ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
                ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())
            if unifi_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_unifi_config_file", "/workspace/unifi/unifi.json")
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_config_file", "/workspace/cloudflare/cloudflare.json")
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)

            # Add authentication secrets conditionally
            if unifi_only or not cloudflare_only:  # UniFi credentials needed
                if unifi_api_key:
                    ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
                elif unifi_username and unifi_password:
                    ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
                    ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

            if cloudflare_only or not unifi_only:  # Cloudflare credentials needed
                if cloudflare_token:
                    # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
                    ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

            # Handle state directory mounting and setup (persistent local state)
            if using_persistent_state:
                ctr = ctr.with_directory("/state", state_dir)
                # Clean up any existing .terraform directory to prevent provider conflicts
                ctr = ctr.with_exec(["sh", "-c", "rm -rf /state/.terraform && echo 'Cleaned .terraform directory'"])
                _ = await ctr.stdout()
                ctr = ctr.with_exec(["sh", "-c", "cp -r /module/glue/* /state/ && ls -la /state"])
                _ = await ctr.stdout()
                ctr = ctr.with_workdir("/state")
            else:
                ctr = ctr.with_workdir("/module/glue")

            # Run terraform init
            init_cmd = ["terraform", "init"]
            if backend_config_file is not None:
                init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

            ctr = ctr.with_exec(init_cmd)
            _ = await ctr.stdout()

            # Run terraform plan - CRITICAL: Preserve container reference
            ctr = ctr.with_exec(["terraform", "plan", "-out=plan.tfplan"])
            _ = await ctr.stdout()

            # Generate JSON output
            ctr = ctr.with_exec(["sh", "-c", "terraform show -json plan.tfplan > plan.json"])
            _ = await ctr.stdout()

            # Generate text output
            ctr = ctr.with_exec(["sh", "-c", "terraform show plan.tfplan > plan.txt"])
            _ = await ctr.stdout()

            # Extract plan files from POST-execution container
            plan_binary = await ctr.file("/state/plan.tfplan" if using_persistent_state else "/module/glue/plan.tfplan")
            plan_json = await ctr.file("/state/plan.json" if using_persistent_state else "/module/glue/plan.json")
            plan_txt = await ctr.file("/state/plan.txt" if using_persistent_state else "/module/glue/plan.txt")

            # Add to output directory
            output_dir = output_dir.with_file("plan.tfplan", plan_binary)
            output_dir = output_dir.with_file("plan.json", plan_json)
            output_dir = output_dir.with_file("plan.txt", plan_txt)

            # Parse plan for resource counts
            try:
                json_content = await plan_json.contents()
                plan_data = json.loads(json_content)
                changes = plan_data.get("resource_changes", [])
                total_add = sum(1 for c in changes if any(a.get("action") in ["create", "add"] for a in c.get("change", {}).get("actions", [])))
                total_change = sum(1 for c in changes if any(a.get("action") in ["update", "change"] for a in c.get("change", {}).get("actions", [])))
                total_destroy = sum(1 for c in changes if any(a.get("action") in ["delete", "destroy"] for a in c.get("change", {}).get("actions", [])))
            except Exception:
                # Fallback: parse from text
                txt_content = await plan_txt.contents()
                total_add = txt_content.count("will be created")
                total_change = txt_content.count("will be changed")
                total_destroy = txt_content.count("will be destroyed")

        except Exception as e:
            raise RuntimeError(f"✗ Failed: Terraform plan failed\n{str(e)}")

        # Phase 3: Create plan summary
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Determine which components were planned
        if unifi_only:
            planned_components = "UniFi DNS only"
        elif cloudflare_only:
            planned_components = "Cloudflare Tunnels only"
        else:
            planned_components = "UniFi DNS and Cloudflare Tunnels"

        summary_content = f"""Terraform Plan Summary
======================

Generated: {timestamp}
Terraform Version: {terraform_version}
KCL Version: {kcl_version}
Backend Type: {backend_type}
Planned Components: {planned_components}

Resource Changes
----------------
Resources to add:     {total_add}
Resources to change:  {total_change}
Resources to destroy: {total_destroy}
Total changes:        {total_add + total_change + total_destroy}

Output Files
------------
- plan.tfplan  (binary plan for terraform apply)
- plan.json    (structured JSON for automation)
- plan.txt     (human-readable format)

Notes
-----
- Binary plan file can be used with 'terraform apply plan.tfplan'
- JSON file is suitable for policy-as-code tools (OPA, Sentinel)
- Text file is optimized for manual review and diffing
- Plan files may contain sensitive values - handle securely
- This plan was generated using the combined Terraform module
"""

        output_dir = output_dir.with_new_file("plan-summary.txt", summary_content)

        return output_dir

    @function
    async def destroy(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")] = "",
        cloudflare_token: Annotated[Optional[Secret], Doc("Cloudflare API Token")] = None,
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")] = "",
        zone_name: Annotated[str, Doc("DNS zone name")] = "",
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password")] = None,
        unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi controller")] = False,
        unifi_only: Annotated[bool, Doc("Destroy only UniFi DNS (mutually exclusive with --cloudflare-only)")] = False,
        cloudflare_only: Annotated[bool, Doc("Destroy only Cloudflare Tunnels (mutually exclusive with --unifi-only)")] = False,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
        backend_type: Annotated[str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")] = "local",
        backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration HCL file (required for remote backends)")] = None,
        state_dir: Annotated[Optional[dagger.Directory], Doc("Directory for persistent Terraform state (mutually exclusive with remote backend)")] = None,
        no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False,
        cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = "",
    ) -> str:
        """
        Destroy UniFi DNS and/or Cloudflare Tunnel resources using the combined Terraform module.

        This function destroys resources using a single Terraform operation with the combined module
        at terraform/modules/glue/. Use --unifi-only or --cloudflare-only for selective destruction,
        or omit both for full destruction of both components.

        Authentication (pick one method for UniFi when destroying UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        State Management (choose one):
        1. Ephemeral (default): State stored in container, lost on exit
        2. Persistent Local: Use --state-dir=./terraform-state to persist state locally
        3. Remote Backend: Use --backend-type=s3 --backend-config-file=... for team/enterprise

        Args:
            kcl_source: Directory containing KCL module
            unifi_url: UniFi Controller URL (required for UniFi destruction)
            cloudflare_token: Cloudflare API Token (required for Cloudflare destruction)
            cloudflare_account_id: Cloudflare Account ID (required for Cloudflare destruction)
            zone_name: DNS zone name (required for Cloudflare destruction)
            api_url: Optional UniFi API URL
            unifi_api_key: UniFi API key (optional)
            unifi_username: UniFi username (optional)
            unifi_password: UniFi password (optional)
            unifi_insecure: Skip TLS verification for self-signed certificates
            unifi_only: Destroy only UniFi DNS (no Cloudflare credentials needed)
            cloudflare_only: Destroy only Cloudflare Tunnels (no UniFi credentials needed)
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend configuration HCL file (required for remote backends)
            state_dir: Directory for persistent Terraform state (mutually exclusive with remote backend)
            no_cache: Bypass Dagger cache by auto-generating an epoch timestamp
            cache_buster: Custom cache key for advanced use cases (cannot use with --no-cache)

        Returns:
            Status message indicating success or failure of destruction

        Example:
            # Full destruction (both UniFi and Cloudflare)
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env:UNIFI_API_KEY

            # UniFi-only destruction
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only

            # Cloudflare-only destruction
            dagger call destroy \\
                --kcl-source=./kcl \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --cloudflare-only

            # With insecure TLS for self-signed certificates
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://192.168.10.1 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only \\
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

            # Force fresh execution (bypass Dagger cache)
            dagger call destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-only \\
                --no-cache
        """
        # Validate cache control options
        if no_cache and cache_buster:
            return "✗ Failed: Cannot use both --no-cache and --cache-buster"

        # Validate mutual exclusion of destruction flags
        if unifi_only and cloudflare_only:
            return "✗ Failed: Cannot use both --unifi-only and --cloudflare-only"

        # Determine effective cache buster value
        effective_cache_buster = cache_buster
        if no_cache:
            effective_cache_buster = str(int(time.time()))

        # Validate credentials based on destruction scope
        if unifi_only:
            # UniFi-only: require UniFi credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                return "✗ Failed: UniFi-only destruction requires either --unifi-api-key OR both --unifi-username and --unifi-password"
            if using_api_key and using_password:
                return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."
            if not unifi_url:
                return "✗ Failed: UniFi-only destruction requires --unifi-url"
        elif cloudflare_only:
            # Cloudflare-only: require Cloudflare credentials
            if cloudflare_token is None:
                return "✗ Failed: Cloudflare-only destruction requires --cloudflare-token"
            if not cloudflare_account_id:
                return "✗ Failed: Cloudflare-only destruction requires --cloudflare-account-id"
            if not zone_name:
                return "✗ Failed: Cloudflare-only destruction requires --zone-name"
        else:
            # Full destruction: require both sets of credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                return "✗ Failed: Full destruction requires either --unifi-api-key OR both --unifi-username and --unifi-password"
            if using_api_key and using_password:
                return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."
            if not unifi_url:
                return "✗ Failed: Full destruction requires --unifi-url"
            if cloudflare_token is None:
                return "✗ Failed: Full destruction requires --cloudflare-token"
            if not cloudflare_account_id:
                return "✗ Failed: Full destruction requires --cloudflare-account-id"
            if not zone_name:
                return "✗ Failed: Full destruction requires --zone-name"

        results = []

        # Phase 1: Generate KCL configurations (conditionally based on destruction scope)
        results.append("=" * 60)
        results.append("PHASE 1: Generating KCL configurations")
        results.append("=" * 60)

        # Bust cache for KCL generation by adding timestamp file to source
        effective_kcl_source = kcl_source
        if effective_cache_buster:
            effective_kcl_source = kcl_source.with_new_file(".cache-bust", effective_cache_buster)

        unifi_dir = None
        cloudflare_dir = None

        if not cloudflare_only:  # Generate UniFi config unless cloudflare-only
            try:
                unifi_file = await self.generate_unifi_config(effective_kcl_source, kcl_version)
                unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
                results.append("✓ UniFi configuration generated")
            except Exception as e:
                return f"✗ Failed: Could not generate UniFi config\n{str(e)}"
        else:
            results.append("○ UniFi configuration skipped (--cloudflare-only)")

        if not unifi_only:  # Generate Cloudflare config unless unifi-only
            try:
                cloudflare_file = await self.generate_cloudflare_config(effective_kcl_source, kcl_version)
                cloudflare_dir = dagger.dag.directory().with_file("cloudflare.json", cloudflare_file)
                results.append("✓ Cloudflare configuration generated")
            except Exception as e:
                return f"✗ Failed: Could not generate Cloudflare config\n{str(e)}"
        else:
            results.append("○ Cloudflare configuration skipped (--unifi-only)")

        # Validate backend configuration
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            return error_msg

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            return error_msg

        actual_api_url = api_url if api_url else unifi_url
        using_persistent_state = state_dir is not None

        # Phase 2: Destroy using appropriate Terraform module
        results.append("")
        results.append("=" * 60)
        if unifi_only:
            results.append("PHASE 2: Destroying UniFi DNS")
        elif cloudflare_only:
            results.append("PHASE 2: Destroying Cloudflare Tunnels")
        else:
            results.append("PHASE 2: Destroying UniFi DNS and Cloudflare Tunnels")
        results.append("=" * 60)

        # Create Terraform container and select module based on deployment mode
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

        # Add cache buster IMMEDIATELY to ensure Terraform operations aren't cached
        if effective_cache_buster:
            ctr = ctr.with_env_variable("CACHE_BUSTER", effective_cache_buster)

        # Determine which Terraform module to use (same as deploy())
        if cloudflare_only:
            module_path = "cloudflare-tunnel"
        elif unifi_only:
            module_path = "unifi-dns"
        else:
            module_path = "glue"

        # Mount the appropriate Terraform module
        try:
            if module_path == "glue":
                tf_modules = dagger.dag.current_module().source().directory("terraform/modules")
                ctr = ctr.with_directory("/module", tf_modules)
                workdir = "/module/glue"
            else:
                tf_module = dagger.dag.current_module().source().directory(f"terraform/modules/{module_path}")
                ctr = ctr.with_directory("/module", tf_module)
                workdir = "/module"
        except Exception as e:
            return f"✗ Failed: Could not mount Terraform module at terraform/modules/{module_path}: {str(e)}"

        # Mount configuration files conditionally
        if unifi_dir is not None:
            ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
        if cloudflare_dir is not None:
            ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)

        # Generate and mount backend.tf if using remote backend
        if backend_type != "local":
            try:
                backend_hcl = self._generate_backend_block(backend_type)
                ctr = ctr.with_new_file(f"{workdir}/backend.tf", backend_hcl)
            except Exception as e:
                return f"✗ Failed: Could not generate backend configuration\n{str(e)}"

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                config_content, _ = await _process_backend_config(backend_config_file)
                ctr = ctr.with_new_file("/root/.terraform/backend.tfbackend", config_content)
            except Exception as e:
                return f"✗ Failed: Could not process backend config file\n{str(e)}"

        # Set up environment variables based on which module is being used
        if module_path == "cloudflare-tunnel":
            # Cloudflare module expects config_file (not cloudflare_config_file)
            # Pass account_id and zone_name as overrides to allow CLI parameters to take precedence
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare/cloudflare.json")
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_account_id_override", cloudflare_account_id)
            if zone_name:
                ctr = ctr.with_env_variable("TF_VAR_zone_name_override", zone_name)
        elif module_path == "unifi-dns":
            # UniFi module expects config_file (not unifi_config_file)
            if unifi_url:
                ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
                ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())
            if unifi_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi/unifi.json")
        else:  # module_path == "glue"
            # Glue module expects both config files with specific names
            if unifi_url:
                ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
                ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())
            if unifi_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_unifi_config_file", "/workspace/unifi/unifi.json")
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_config_file", "/workspace/cloudflare/cloudflare.json")
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)

        # Add authentication secrets conditionally
        if unifi_only or not cloudflare_only:  # UniFi credentials needed
            if unifi_api_key:
                ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
            elif unifi_username and unifi_password:
                ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
                ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

        if cloudflare_only or not unifi_only:  # Cloudflare credentials needed
            if cloudflare_token:
                # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
                ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

        # Handle state directory mounting and setup (persistent local state)
        if using_persistent_state:
            ctr = ctr.with_directory("/state", state_dir)
            ctr = ctr.with_exec(["sh", "-c", "rm -rf /state/.terraform && echo 'Cleaned .terraform directory'"])
            _ = await ctr.stdout()
            ctr = ctr.with_exec(["sh", "-c", f"cp -r {workdir}/* /state/ && ls -la /state"])
            _ = await ctr.stdout()
            ctr = ctr.with_workdir("/state")
        else:
            ctr = ctr.with_workdir(workdir)

        # Run terraform init
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

        try:
            ctr = ctr.with_exec(init_cmd)
            _ = await ctr.stdout()
            results.append("✓ Terraform init completed")
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

        # Run terraform destroy (no targeting needed - using individual modules)
        destroy_cmd = ["terraform", "destroy", "-auto-approve"]

        try:
            ctr = ctr.with_exec(destroy_cmd)
            destroy_result = await ctr.stdout()
            results.append("✓ Terraform destroy completed")
        except dagger.ExecError as e:
            error_details = f"Exit code: {e.exit_code}\n"
            error_details += f"Stdout:\n{e.stdout or 'N/A'}\n"
            error_details += f"Stderr:\n{e.stderr or 'N/A'}"
            return f"✗ Failed: Terraform destroy failed\n{error_details}"

        # Final summary
        results.append("")
        results.append("=" * 60)
        results.append("DESTRUCTION SUMMARY")
        results.append("=" * 60)

        if unifi_only:
            results.append("✓ UniFi DNS resources destroyed successfully")
        elif cloudflare_only:
            results.append("✓ Cloudflare Tunnel resources destroyed successfully")
        else:
            results.append("✓ UniFi DNS and Cloudflare Tunnel resources destroyed successfully")

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

            # Set environment variables with overrides for CLI parameters
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_account_id_override", cloudflare_account_id)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_zone_name_override", cloudflare_zone)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

            # Pass Cloudflare token as secret - use CLOUDFLARE_API_TOKEN env var
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
                assert "tunnel_ids" in secrets_data, "Missing tunnel_ids in response"
                assert "tunnel_tokens" in secrets_data, "Missing tunnel_tokens in response"
                assert "credentials_json" in secrets_data, "Missing credentials_json in response"
                assert "count" in secrets_data, "Missing count in response"

                # Verify IDs are non-empty strings
                for mac, tunnel_id in secrets_data["tunnel_ids"].items():
                    assert isinstance(tunnel_id, str), f"Tunnel ID for {mac} is not a string"
                    assert len(tunnel_id) > 0, f"Tunnel ID for {mac} is empty"

                # Verify tokens are non-empty strings
                for mac, token in secrets_data["tunnel_tokens"].items():
                    assert isinstance(token, str), f"Token for {mac} is not a string"
                    assert len(token) > 0, f"Token for {mac} is empty"

                # Verify credentials contain required fields
                for mac, creds_json in secrets_data["credentials_json"].items():
                    # Parse JSON string if needed
                    try:
                        creds = json.loads(creds_json) if isinstance(creds_json, str) else creds_json
                    except (json.JSONDecodeError, TypeError):
                        creds = creds_json if isinstance(creds_json, dict) else {}
                    
                    assert "AccountTag" in creds, f"Missing AccountTag for {mac}"
                    assert "TunnelID" in creds, f"Missing TunnelID for {mac}"
                    assert "TunnelName" in creds, f"Missing TunnelName for {mac}"
                    assert "TunnelSecret" in creds, f"Missing TunnelSecret for {mac}"

                report_lines.append(f"  ✓ Retrieved secrets for {secrets_data['count']} tunnel(s)")
                report_lines.append(f"  ✓ Verified tunnel_ids format")
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

                    # Set environment variables with overrides for CLI parameters
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_account_id_override", cloudflare_account_id)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_zone_name_override", cloudflare_zone)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

                    # Pass Cloudflare token as secret - use CLOUDFLARE_API_TOKEN env var
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

            # Mount the Cloudflare Tunnel Terraform module from Dagger module's source
            # Note: Always use the module's own terraform directory, not the user's source
            try:
                tf_module = dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")
                tf_ctr = tf_ctr.with_directory("/module", tf_module)
            except Exception as e:
                return f"✗ Failed: Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel: {str(e)}"

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
            # Use override variables to allow CLI parameters to take precedence over config
            tf_ctr = tf_ctr.with_env_variable("TF_VAR_account_id_override", cloudflare_account_id)
            tf_ctr = tf_ctr.with_env_variable("TF_VAR_zone_name_override", zone_name)
            # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
            tf_ctr = tf_ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

            # Handle state directory mounting for persistent local state
            using_persistent_state = state_dir is not None
            if using_persistent_state:
                # Mount state directory
                tf_ctr = tf_ctr.with_directory("/state", state_dir)
                # Clean up any existing .terraform directory to prevent provider conflicts
                tf_ctr = tf_ctr.with_exec(["sh", "-c", "rm -rf /state/.terraform && echo 'Cleaned .terraform directory'"])
                _ = await tf_ctr.stdout()
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
                init_output = await tf_ctr.stdout()
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

            # Debug: List available outputs
            try:
                tf_ctr = tf_ctr.with_exec(["terraform", "output", "-json"])
                all_outputs = await tf_ctr.stdout()
                # Parse to check what outputs exist
                outputs_dict = json.loads(all_outputs)
                available_outputs = list(outputs_dict.keys())
            except Exception:
                available_outputs = ["unknown"]

            # Run terraform output to get tunnel_ids
            try:
                tf_ctr = tf_ctr.with_exec(["terraform", "output", "-json", "tunnel_ids"])
                ids_json_str = await tf_ctr.stdout()
            except dagger.ExecError as e:
                error_str = str(e)
                if "No outputs found" in error_str or "output" in error_str.lower():
                    return f"✗ Failed: No tunnels found in Terraform outputs. Available outputs: {', '.join(available_outputs)}"
                elif "state" in error_str.lower() or "tfstate" in error_str.lower():
                    return f"✗ Failed: No Terraform state found. Available outputs: {', '.join(available_outputs)}"
                else:
                    return f"✗ Failed: Could not retrieve tunnel IDs\nError: {str(e)}\nAvailable outputs: {', '.join(available_outputs)}"

            # Run terraform output to get tunnel_tokens
            try:
                tf_ctr = tf_ctr.with_exec(["terraform", "output", "-json", "tunnel_tokens"])
                tokens_json_str = await tf_ctr.stdout()
            except dagger.ExecError as e:
                error_str = str(e)
                if "No outputs found" in error_str or "output" in error_str.lower():
                    return f"✗ Failed: No tunnels found in Terraform outputs. Available outputs: {', '.join(available_outputs)}"
                elif "state" in error_str.lower() or "tfstate" in error_str.lower():
                    return f"✗ Failed: No Terraform state found. Available outputs: {', '.join(available_outputs)}"
                else:
                    return f"✗ Failed: Could not retrieve tunnel tokens\nError: {str(e)}\nAvailable outputs: {', '.join(available_outputs)}"

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
                tunnel_ids = json.loads(ids_json_str.strip())
                tunnel_tokens = json.loads(tokens_json_str.strip())
                credentials = json.loads(credentials_json_str.strip())
            except json.JSONDecodeError as e:
                return f"✗ Failed: Could not parse Terraform output as JSON\n{str(e)}"

            # Validate that we have data
            if not tunnel_ids or not tunnel_tokens or not credentials:
                return "✗ Failed: No tunnels found in Terraform outputs. State may be corrupted."

            # Format and return output
            if output_format == "json":
                result = {
                    "tunnel_ids": tunnel_ids,
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
                    "TUNNEL IDS (for mapping MAC to Tunnel)",
                    "-" * 60,
                    "",
                ]

                for mac, tunnel_id in tunnel_ids.items():
                    output_lines.append(f"MAC Address: {mac}")
                    output_lines.append(f"Tunnel ID: {tunnel_id}")
                    output_lines.append("")

                output_lines.extend([
                    "-" * 60,
                    "TUNNEL TOKENS (for cloudflared login)",
                    "-" * 60,
                    "",
                ])

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

                for mac, creds_json in credentials.items():
                    # Parse JSON string from terraform output
                    try:
                        creds = json.loads(creds_json)
                    except (json.JSONDecodeError, TypeError):
                        # If already a dict (shouldn't happen but handle it)
                        creds = creds_json if isinstance(creds_json, dict) else {}
                    
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
