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

        # Check for generator file
        try:
            gen_file = source.file("generators/unifi.k")
            _ = await gen_file.contents()
        except Exception:
            raise KCLGenerationError(
                "✗ Generator file not found: generators/unifi.k\n"
                "Available generators should be in the 'generators/' subdirectory."
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

        # Run KCL generator and convert YAML output to JSON, extracting just the 'result' key
        try:
            result = await ctr.with_exec([
                "sh", "-c",
                "kcl run generators/unifi.k | yq -o=json '.result'"
            ]).stdout()
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ KCL execution failed:\n"
                f"Exit code: {e.exit_code}\n"
                f"Stderr: {e.stderr}\n"
                f"\nHint: Check your KCL syntax with 'kcl run generators/unifi.k' locally."
            )

        # Validate JSON output
        try:
            json.loads(result)
        except json.JSONDecodeError as e:
            raise KCLGenerationError(
                f"✗ Invalid JSON output from KCL generator:\n{str(e)}\n"
                f"Hint: Ensure the generator outputs valid YAML that can be converted to JSON."
            )

        # Return as file
        return dagger.dag.directory().with_new_file("unifi.json", result).file("unifi.json")

    @function
    async def deploy_unifi(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing unifi.json")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL (e.g., https://unifi.local:8443)")],
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")] = None,
        unifi_username: Annotated[Optional[Secret], Doc("UniFi username (use with password)")] = None,
        unifi_password: Annotated[Optional[Secret], Doc("UniFi password (use with username)")] = None,
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
    ) -> str:
        """
        Deploy UniFi DNS configuration using Terraform.

        This function runs Terraform to deploy UniFi DNS records from the generated
        unifi.json configuration. Supports both API key and username/password authentication.

        Authentication (pick one method):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        Args:
            source: Directory containing unifi.json configuration file
            unifi_url: UniFi Controller URL
            api_url: Optional UniFi API URL (defaults to unifi_url)
            unifi_api_key: UniFi API key for authentication
            unifi_username: UniFi username for authentication
            unifi_password: UniFi password for authentication
            terraform_version: Terraform version to use (default: "latest")

        Returns:
            Status message indicating success or failure of deployment

        Example:
            dagger call deploy-unifi \\
                --source=. \\
                --unifi-url=https://unifi.local:8443 \\
                --unifi-api-key=env:UNIFI_API_KEY
        """
        # Validate authentication - either API key OR username/password, not both
        using_api_key = unifi_api_key is not None
        using_password = unifi_username is not None and unifi_password is not None

        if not using_api_key and not using_password:
            return "✗ Failed: Must provide either unifi_api_key OR both unifi_username and unifi_password"

        if using_api_key and using_password:
            return "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."

        # Use unifi_url as default for api_url if not provided
        actual_api_url = api_url if api_url else unifi_url

        # Check for unifi.json
        try:
            config_file = source.file("unifi.json")
            _ = await config_file.contents()
        except Exception:
            return "✗ Failed: unifi.json not found in source directory. Run generate-unifi-config first."

        # Get project root directory (parent of source)
        # We need to mount the terraform modules from the project
        project_dir = dagger.dag.directory()

        # Create Terraform container
        ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

        # Mount source directory with unifi.json
        ctr = ctr.with_directory("/workspace", source)

        # Mount the UniFi DNS Terraform module
        # Note: The module should be available in the project
        try:
            # Try to get the terraform module from the project
            tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            # If not available, we'll use the config directly
            pass

        # Set up environment variables for Terraform
        ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
        ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")

        # Add authentication secrets via environment variables
        if using_api_key and unifi_api_key:
            api_key_value = await unifi_api_key.plaintext()
            ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
        elif using_password and unifi_username and unifi_password:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
            ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

        # Set working directory to the module
        ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        # Run terraform init
        try:
            init_result = await ctr.with_exec(["terraform", "init"]).stdout()
        except dagger.ExecError as e:
            return f"✗ Failed: Terraform init failed\n{str(e)}"

        # Run terraform apply
        try:
            apply_result = await ctr.with_exec([
                "terraform", "apply", "-auto-approve"
            ]).stdout()
            return f"✓ Success: UniFi DNS deployment completed\n\n{apply_result}"
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
    ) -> str:
        """
        Deploy Cloudflare Tunnel configuration using Terraform.

        This function runs Terraform to deploy Cloudflare Tunnels and DNS records
        from the generated cloudflare.json configuration.

        Args:
            source: Directory containing cloudflare.json configuration file
            cloudflare_token: Cloudflare API Token (Secret)
            cloudflare_account_id: Cloudflare Account ID
            zone_name: DNS zone name
            terraform_version: Terraform version to use (default: "latest")

        Returns:
            Status message indicating success or failure of deployment

        Example:
            dagger call deploy-cloudflare \\
                --source=. \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com
        """
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
            tf_module = dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        # Set up environment variables
        ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
        ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

        # Add Cloudflare token as secret
        ctr = ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)

        # Set working directory
        ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        # Run terraform init
        try:
            init_result = await ctr.with_exec(["terraform", "init"]).stdout()
        except dagger.ExecError as e:
            return f"✗ Failed: Terraform init failed\n{str(e)}"

        # Run terraform apply
        try:
            apply_result = await ctr.with_exec([
                "terraform", "apply", "-auto-approve"
            ]).stdout()
            return f"✓ Success: Cloudflare Tunnel deployment completed\n\n{apply_result}"
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
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
    ) -> str:
        """
        Orchestrate full deployment: UniFi DNS first, then Cloudflare Tunnels.

        This function generates KCL configurations and deploys them in the correct
        order: UniFi first (creates local DNS), then Cloudflare (points to local DNS).

        Authentication (pick one method for UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

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
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")

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
            terraform_version=terraform_version,
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
        )

        results.append(cloudflare_result)

        # Final summary
        results.append("")
        results.append("=" * 60)
        results.append("DEPLOYMENT SUMMARY")
        results.append("=" * 60)

        if "✓ Success" in unifi_result and "✓ Success" in cloudflare_result:
            results.append("✓ Both deployments completed successfully")
        elif "✓ Success" in unifi_result:
            results.append("○ UniFi: Success")
            results.append("✗ Cloudflare: Failed")
        else:
            results.append("✗ UniFi: Failed")
            results.append("○ Cloudflare: Not attempted")

        return "\n".join(results)

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
        terraform_version: Annotated[str, Doc("Terraform version to use (e.g., '1.10.0' or 'latest')")] = "latest",
        kcl_version: Annotated[str, Doc("KCL version to use (e.g., '0.11.0' or 'latest')")] = "latest",
    ) -> str:
        """
        Destroy all resources in reverse order: Cloudflare first, then UniFi.

        Destroys Cloudflare Tunnels first (to avoid DNS loops), then UniFi DNS records.

        Authentication (pick one method for UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

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
            terraform_version: Terraform version to use (default: "latest")
            kcl_version: KCL version to use (default: "latest")

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
            tf_module = dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
        ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")
        ctr = ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
        ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        try:
            await ctr.with_exec(["terraform", "init"]).stdout()
        except dagger.ExecError as e:
            results.append(f"✗ Terraform init failed: {str(e)}")
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
            tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
            ctr = ctr.with_directory("/module", tf_module)
        except Exception:
            pass

        ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
        ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
        ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")

        if unifi_api_key:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
        elif unifi_username and unifi_password:
            ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
            ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)

        ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

        try:
            await ctr.with_exec(["terraform", "init"]).stdout()
        except dagger.ExecError as e:
            results.append(f"✗ Terraform init failed: {str(e)}")
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

        # Check for generator file
        try:
            gen_file = source.file("generators/cloudflare.k")
            _ = await gen_file.contents()
        except Exception:
            raise KCLGenerationError(
                "✗ Generator file not found: generators/cloudflare.k\n"
                "Available generators should be in the 'generators/' subdirectory."
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

        # Run KCL generator and convert YAML output to JSON, extracting just the 'result' key
        try:
            result = await ctr.with_exec([
                "sh", "-c",
                "kcl run generators/cloudflare.k | yq -o=json '.result'"
            ]).stdout()
        except dagger.ExecError as e:
            raise KCLGenerationError(
                f"✗ KCL execution failed:\n"
                f"Exit code: {e.exit_code}\n"
                f"Stderr: {e.stderr}\n"
                f"\nHint: Check your KCL syntax with 'kcl run generators/cloudflare.k' locally."
            )

        # Validate JSON output
        try:
            json.loads(result)
        except json.JSONDecodeError as e:
            raise KCLGenerationError(
                f"✗ Invalid JSON output from KCL generator:\n{str(e)}\n"
                f"Hint: Ensure the generator outputs valid YAML that can be converted to JSON."
            )

        # Return as file
        return dagger.dag.directory().with_new_file("cloudflare.json", result).file("cloudflare.json")

    def _generate_test_id(self) -> str:
        """Generate a random test identifier."""
        return "test-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

    def _generate_test_configs(
        self,
        test_id: str,
        cloudflare_zone: str,
        cloudflare_account_id: str
    ) -> dict:
        """
        Generate test configuration JSON for Cloudflare and UniFi Terraform modules.

        This method generates JSON configuration files that match the variable structures
        expected by the Terraform modules for Cloudflare Tunnel and UniFi DNS.

        Args:
            test_id: Unique test identifier (e.g., "test-abc12")
            cloudflare_zone: DNS zone name (e.g., "example.com")
            cloudflare_account_id: Cloudflare account ID

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
        # Test MAC address (consistent across both configs)
        test_mac = "aa:bb:cc:dd:ee:ff"

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
                    "domain": "local",
                    "nics": [
                        {
                            "mac_address": test_mac,
                            "nic_name": "eth0"
                        }
                    ]
                }
            ],
            "default_domain": "local",
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
        cleanup: Annotated[bool, Doc("Whether to cleanup resources after test (default: true)")] = True,
        validate_connectivity: Annotated[bool, Doc("Whether to test actual HTTP connectivity")] = False,
        test_timeout: Annotated[str, Doc("Timeout for test operations (e.g., 5m)")] = "5m",
        cache_buster: Annotated[str, Doc("Cache buster value to force re-execution (e.g., timestamp, random string)")] = "",
        wait_before_cleanup: Annotated[int, Doc("Seconds to wait between validation and cleanup for manual verification")] = 0,
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
            cleanup: Whether to cleanup resources after test (default: true)
            validate_connectivity: Whether to test actual HTTP connectivity
            test_timeout: Timeout for test operations (e.g., 5m)
            cache_buster: Cache buster value to force re-execution. Use a unique value
                (timestamp, random string) to invalidate Dagger's cache and force fresh execution.
            wait_before_cleanup: Seconds to wait between validation and cleanup.
                Allows manual verification of created resources before they are destroyed.
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

            # With cache buster to force re-execution
            dagger call test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env:CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env:UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --cache-buster=$(date +%s)

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

        report_lines = [
            "=" * 60,
            "INTEGRATION TEST REPORT",
            "=" * 60,
            f"Test ID: {test_id}",
            f"Cloudflare Zone: {cloudflare_zone}",
            f"Test Hostname: {test_hostname}",
            f"Tunnel Name: {tunnel_name}",
            f"Cleanup Enabled: {cleanup}",
            f"Connectivity Check: {validate_connectivity}",
        ]

        # Add cache buster info if provided
        if cache_buster:
            report_lines.append(f"Cache Buster: {cache_buster}")

        # Add wait info if enabled
        if wait_before_cleanup > 0:
            report_lines.append(f"Wait Before Cleanup: {wait_before_cleanup}s")

        report_lines.append("-" * 60)

        # Create test configurations (Cloudflare and UniFi JSON)
        test_configs = self._generate_test_configs(test_id, cloudflare_zone, cloudflare_account_id)
        cloudflare_json = test_configs["cloudflare"]
        unifi_json = test_configs["unifi"]

        # Track cleanup status
        cleanup_status = {"cloudflare": "pending", "unifi": "pending", "state_files": "pending"}
        validation_results = {}

        # Initialize state variables (will be populated during apply phases)
        cloudflare_state = ""
        unifi_state = ""

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
            if cache_buster:
                base_container = base_container.with_env_variable("CACHE_BUSTER", cache_buster)

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
                    tf_module = dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")
                    cf_ctr = cf_ctr.with_directory("/module", tf_module)
                except Exception:
                    raise RuntimeError("Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel")

            # Set environment variables
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_zone_name", cloudflare_zone)
            cf_ctr = cf_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

            # Pass Cloudflare token as secret
            cf_ctr = cf_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)

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
                apply_result = await cf_ctr.with_exec(["terraform", "apply", "-auto-approve"]).stdout()
                report_lines.append(f"  ✓ Created tunnel: {tunnel_name}")
                report_lines.append(f"  ✓ Created DNS record: {test_hostname}")
                validation_results["cloudflare_tunnel"] = "created"
                validation_results["cloudflare_dns"] = "created"

                # Export Terraform state for cleanup
                try:
                    cloudflare_state = await cf_ctr.file("/module/terraform.tfstate").contents()
                    report_lines.append(f"  ✓ Cloudflare state exported ({len(cloudflare_state)} bytes)")
                except Exception as state_err:
                    report_lines.append(f"  ⚠ Cloudflare state export failed: {str(state_err)}")
                    cloudflare_state = ""
            except dagger.ExecError as e:
                error_msg = f"Terraform apply failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["cloudflare_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Phase 3: Create UniFi resources
            report_lines.append("")
            report_lines.append("PHASE 3: Creating UniFi resources...")

            # Note: UniFi may fail because the test MAC (aa:bb:cc:dd:ee:ff) won't exist
            # in real UniFi controllers. This is expected behavior for integration testing.

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
                    tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
                    unifi_ctr = unifi_ctr.with_directory("/module", tf_module)
                except Exception:
                    raise RuntimeError("UniFi DNS Terraform module not found at terraform/modules/unifi-dns")

            # Set environment variables
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_api_url", api_url if api_url else unifi_url)
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")

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
                apply_result = await unifi_ctr.with_exec(["terraform", "apply", "-auto-approve"]).stdout()
                report_lines.append(f"  ✓ Created UniFi DNS record: {test_id}.local")
                validation_results["unifi_dns"] = "created"

                # Export Terraform state for cleanup
                try:
                    unifi_state = await unifi_ctr.file("/module/terraform.tfstate").contents()
                    report_lines.append(f"  ✓ UniFi state exported ({len(unifi_state)} bytes)")
                except Exception as state_err:
                    report_lines.append(f"  ⚠ UniFi state export failed: {str(state_err)}")
                    unifi_state = ""
            except dagger.ExecError as e:
                error_msg = f"Terraform apply failed: {str(e)}"
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["unifi_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Phase 4: Validation
            report_lines.append("")
            report_lines.append("PHASE 4: Validating resources...")

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
                    f'echo \'{tunnel_list_result}\' | jq \'.result | length\''
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
                    f'echo \'{zone_list_result}\' | jq -r \'.result[0].id\''
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
                        f'echo \'{dns_record_result}\' | jq \'.result | length\''
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

            # Phase 4.5: Wait before cleanup (if enabled)
            if wait_before_cleanup > 0:
                report_lines.append("")
                report_lines.append(f"PHASE 4.5: Waiting {wait_before_cleanup}s before cleanup...")
                report_lines.append("  (Use this time to manually verify created resources)")
                await asyncio.sleep(wait_before_cleanup)
                report_lines.append(f"  ✓ Wait completed ({wait_before_cleanup}s)")

        except Exception as e:
            report_lines.append("")
            report_lines.append(f"✗ ERROR DURING TEST: {str(e)}")
            validation_results["error"] = str(e)

        finally:
            # Phase 5: Guaranteed Cleanup
            if cleanup:
                report_lines.append("")
                report_lines.append("PHASE 5: Cleanup (guaranteed execution)...")

                # Cleanup Cloudflare resources first (reverse order of creation)
                report_lines.append("  Cleaning up Cloudflare resources...")
                cf_cleanup_method = "config-based"  # Track cleanup method
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
                            tf_module = dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")
                            cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
                        except Exception:
                            raise RuntimeError("Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel")

                    # Import state if available (state-based cleanup)
                    if cloudflare_state:
                        try:
                            cf_cleanup_ctr = cf_cleanup_ctr.with_new_file("/module/terraform.tfstate", cloudflare_state)
                            cf_cleanup_method = "state-based"
                            report_lines.append("    ✓ Cloudflare state imported for cleanup")
                        except Exception as state_err:
                            report_lines.append(f"    ⚠ State import failed, using config-based cleanup: {str(state_err)}")
                            cf_cleanup_method = "config-based"

                    # Set environment variables
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_zone_name", cloudflare_zone)
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

                    # Pass Cloudflare token as secret
                    cf_cleanup_ctr = cf_cleanup_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)

                    # Set working directory to module
                    cf_cleanup_ctr = cf_cleanup_ctr.with_workdir("/module")

                    # Execute terraform init
                    try:
                        await cf_cleanup_ctr.with_exec(["terraform", "init"]).stdout()
                    except dagger.ExecError as e:
                        raise RuntimeError(f"Terraform init failed: {str(e)}")

                    # Execute terraform destroy
                    try:
                        destroy_result = await cf_cleanup_ctr.with_exec([
                            "terraform", "destroy", "-auto-approve"
                        ]).stdout()
                        report_lines.append(f"    ✓ Destroyed tunnel: {tunnel_name} ({cf_cleanup_method})")
                        report_lines.append(f"    ✓ Deleted DNS record: {test_hostname}")
                        cleanup_status["cloudflare"] = "success"
                    except dagger.ExecError as e:
                        raise RuntimeError(f"Terraform destroy failed: {str(e)}")
                except Exception as e:
                    cleanup_status["cloudflare"] = f"failed: {str(e)}"
                    report_lines.append(f"    ✗ Failed to cleanup Cloudflare: {str(e)}")

                # Cleanup UniFi resources second
                report_lines.append("  Cleaning up UniFi resources...")
                unifi_cleanup_method = "config-based"  # Track cleanup method
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
                            tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
                            unifi_cleanup_ctr = unifi_cleanup_ctr.with_directory("/module", tf_module)
                        except Exception:
                            raise RuntimeError("UniFi DNS Terraform module not found at terraform/modules/unifi-dns")

                    # Import state if available (state-based cleanup)
                    if unifi_state:
                        try:
                            unifi_cleanup_ctr = unifi_cleanup_ctr.with_new_file("/module/terraform.tfstate", unifi_state)
                            unifi_cleanup_method = "state-based"
                            report_lines.append("    ✓ UniFi state imported for cleanup")
                        except Exception as state_err:
                            report_lines.append(f"    ⚠ State import failed, using config-based cleanup: {str(state_err)}")
                            unifi_cleanup_method = "config-based"

                    # Set environment variables
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_api_url", api_url if api_url else unifi_url)
                    unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")

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
                        report_lines.append(f"    ✓ Deleted UniFi DNS record: {test_id}.local ({unifi_cleanup_method})")
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
                report_lines.append(f"  Cloudflare: {cleanup_status['cloudflare']} ({cf_cleanup_method})")
                report_lines.append(f"  UniFi: {cleanup_status['unifi']} ({unifi_cleanup_method})")
                report_lines.append(f"  State Files: {cleanup_status['state_files']}")

                # Display warning if any cleanup step failed
                if not all(status == "success" for status in cleanup_status.values()):
                    report_lines.append("")
                    report_lines.append("⚠ WARNING: Some cleanup steps failed!")
                    report_lines.append("  Manual cleanup may be required:")
                    if cleanup_status["cloudflare"] != "success":
                        report_lines.append(f"    - Check Cloudflare dashboard for remaining resources: {tunnel_name}, {test_hostname}")
                    if cleanup_status["unifi"] != "success":
                        report_lines.append(f"    - Check UniFi controller for remaining DNS record: {test_id}.local")
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
        report_lines.append(f"  - Internal DNS: {test_id}.local")
        report_lines.append(f"")
        report_lines.append(f"Validation Results:")
        for key, value in validation_results.items():
            report_lines.append(f"  - {key}: {value}")
        report_lines.append(f"")
        report_lines.append(f"Cleanup Status: {'COMPLETED' if cleanup else 'SKIPPED'}")
        report_lines.append("=" * 60)

        return "\n".join(report_lines)
