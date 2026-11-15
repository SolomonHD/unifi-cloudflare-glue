"""Dagger module for unifi-cloudflare-glue.

This module provides containerized, reproducible pipelines for managing
hybrid DNS infrastructure bridging UniFi network DNS with Cloudflare Tunnel edge DNS.
"""

import asyncio
import json
import random
import re
import string
import time
import tomllib
from typing import Annotated, Optional
from uuid import uuid4

import dagger
from dagger import Directory, Doc, Secret, function, object_type

try:
    from .tunnel_artifacts import protected_tunnel_artifact, verify_tunnel_artifact
except ImportError:
    from tunnel_artifacts import (  # type: ignore[no-redef,import-not-found]
        protected_tunnel_artifact,
        verify_tunnel_artifact,
    )

try:
    from .execution import (
        CLOUDFLARE_QUERY,
        UNIFI_PREFIX_QUERY,
        PhaseFailure,
        live_exec,
        plan_counts,
        prepare_root,
        selected_root,
        terraform_runtime,
        validate_run_label,
        validate_unifi_auth,
    )
    from .toolchains import (
        DEFAULT_KCL_VERSION,
        DEFAULT_TERRAFORM_VERSION,
        PYTHON_IMAGE,
        terraform_image,
    )
except ImportError:
    from execution import (  # type: ignore[no-redef,import-not-found]
        CLOUDFLARE_QUERY,
        UNIFI_PREFIX_QUERY,
        PhaseFailure,
        live_exec,
        plan_counts,
        prepare_root,
        selected_root,
        terraform_runtime,
        validate_run_label,
        validate_unifi_auth,
    )
    from toolchains import (  # type: ignore[no-redef,import-not-found]
        DEFAULT_KCL_VERSION,
        DEFAULT_TERRAFORM_VERSION,
        PYTHON_IMAGE,
        terraform_image,
    )

try:
    from .toolchains import kcl_container, kcl_image
except ImportError:  # Support the repository's direct-module unit test imports.
    from toolchains import kcl_container, kcl_image  # type: ignore[no-redef,import-not-found]

BACKEND_SECRET_PATH = "/root/.terraform/backend.tfbackend"
BACKEND_INPUT_PATH = "/run/secrets/backend-input"


def _parse_duration(value: str) -> float:
    """Parse a positive duration such as ``30s``, ``5m``, or ``1.5h``."""
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smh])\s*", value)
    if not match:
        raise ValueError("test_timeout must be a positive duration ending in s, m, or h")
    amount = float(match.group(1))
    if amount <= 0:
        raise ValueError("test_timeout must be greater than zero")
    return amount * {"s": 1, "m": 60, "h": 3600}[match.group(2)]


def _safe_exec_error(step: str, error: Exception, operation_id: str = "") -> str:
    """Return useful execution context without copying provider output or headers."""
    exit_code = getattr(error, "exit_code", None)
    suffix = f" (exit code {exit_code})" if type(exit_code) is int else ""
    identity = f"; operation {operation_id}" if operation_id else ""
    recovery = (
        "; outcome unknown: reconcile process termination, remote resources and state before retry; "
        "restoring state is not remote rollback"
        if type(exit_code) is not int
        else "; reconcile partial effects and current state before retry"
    )
    return (
        f"{step} failed{suffix}{identity}{recovery}; inspect the redacted Dagger trace for details"
    )


async def _before_deadline(awaitable, deadline: float):
    """Await an operation without allowing it to exceed the shared deadline."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("integration operation deadline exceeded")
    return await asyncio.wait_for(awaitable, timeout=remaining)


def _integration_failure_reasons(
    primary_failure: Optional[str],
    validation_results: dict[str, str],
    cleanup_ledger: list[dict[str, object]],
    cleanup_status: dict[str, str],
) -> list[str]:
    """Evaluate strict integration outcome state without exposing provider output."""
    reasons: list[str] = []
    if primary_failure:
        reasons.append(primary_failure)
    required_validation = {
        "cloudflare_tunnel": "validated",
        "cloudflare_dns": "validated",
        "unifi_validation": "validated",
        "secrets_retrieval": "success",
    }
    for key, expected in required_validation.items():
        if validation_results.get(key) != expected:
            reasons.append(f"{key}={validation_results.get(key, 'missing')}")
    for entry in cleanup_ledger:
        if not entry.get("state_captured"):
            reasons.append(f"{entry['provider']} state was not captured")
    for provider, status in cleanup_status.items():
        if not str(status).startswith("success"):
            reasons.append(f"{provider} cleanup={status}")
    return reasons


async def _with_backend_secret(
    container: dagger.Container,
    backend_config_file: Secret,
    backend_config_format: str,
) -> dagger.Container:
    """Convert inside the secret-mounted runtime, never through application File reads."""
    if backend_config_format not in {"yaml", "hcl"}:
        raise ValueError("backend-config-format must explicitly select yaml or hcl")
    container = container.with_mounted_secret(
        BACKEND_INPUT_PATH,
        backend_config_file,
        owner="root",
        mode=0o600,
    )
    container = container.with_exec(["mkdir", "-p", "/root/.terraform"])
    container = live_exec(
        container,
        [
            "python",
            "/tooling/src/main/backend_runtime.py",
            backend_config_format,
            BACKEND_INPUT_PATH,
            BACKEND_SECRET_PATH,
        ],
    )
    try:
        await container.sync()
    except Exception as error:
        raise RuntimeError(_safe_exec_error("Backend configuration processing", error)) from None
    return container


# Custom exception for KCL generation errors
class KCLGenerationError(Exception):
    """Raised when KCL configuration generation fails."""

    pass


def _validate_generated_config(output: object, provider: str) -> None:
    """Check the existing Terraform input shapes without exposing configuration values."""
    missing = object()
    type_names = {dict: "object", list: "array", str: "string", bool: "boolean"}
    root = "unifi_output" if provider == "unifi" else "cf_output"

    def expect(value: object, kind: type, path: str, nullable: bool = False) -> None:
        if nullable and value is None:
            return
        if type(value) is not kind:
            expected = type_names[kind] + (" or null" if nullable else "")
            found = (
                "missing"
                if value is missing
                else "null" if value is None else type_names.get(type(value), "number")
            )
            raise KCLGenerationError(f"{path}: expected {expected}; found {found}")

    def fields(value: dict, path: str, required: dict[str, type]) -> None:
        for name, kind in required.items():
            expect(value.get(name, missing), kind, f"{path}.{name}")

    def mac(value: object, path: str) -> None:
        expect(value, str, path)
        if not re.fullmatch(r"[0-9a-f]{2}(?::[0-9a-f]{2}){5}", str(value)):
            raise KCLGenerationError(f"{path}: expected normalized MAC string; found string")

    def cnames(value: dict, path: str) -> None:
        names = value.get("service_cnames", missing)
        expect(names, list, f"{path}.service_cnames", nullable=True)
        if isinstance(names, list):
            for index, name in enumerate(names):
                expect(name, str, f"{path}.service_cnames[{index}]")

    expect(output, dict, root)
    assert isinstance(output, dict)
    if provider == "unifi":
        fields(output, root, {"devices": list, "default_domain": str, "site": str})
        for index, device in enumerate(output["devices"]):
            path = f"{root}.devices[{index}]"
            expect(device, dict, path)
            fields(device, path, {"friendly_hostname": str, "nics": list})
            expect(device.get("domain", missing), str, f"{path}.domain", nullable=True)
            cnames(device, path)
            for nic_index, nic in enumerate(device["nics"]):
                nic_path = f"{path}.nics[{nic_index}]"
                expect(nic, dict, nic_path)
                mac(nic.get("mac_address", missing), f"{nic_path}.mac_address")
                if "nic_name" in nic:
                    expect(nic["nic_name"], str, f"{nic_path}.nic_name", nullable=True)
                cnames(nic, nic_path)
    else:
        fields(output, root, {"zone_name": str, "account_id": str, "tunnels": dict})
        # Positional paths avoid copying arbitrary map keys into error messages.
        for index, (key, tunnel) in enumerate(output["tunnels"].items()):
            path = f"{root}.tunnels[{index}]"
            mac(key, f"{path}.key")
            expect(tunnel, dict, path)
            fields(tunnel, path, {"tunnel_name": str, "services": list})
            mac(tunnel.get("mac_address", missing), f"{path}.mac_address")
            for service_index, service in enumerate(tunnel["services"]):
                service_path = f"{path}.services[{service_index}]"
                expect(service, dict, service_path)
                fields(service, service_path, {"public_hostname": str, "local_service_url": str})
                if "no_tls_verify" in service:
                    expect(
                        service["no_tls_verify"],
                        bool,
                        f"{service_path}.no_tls_verify",
                        nullable=True,
                    )


async def _generate_configs(
    source: dagger.Directory,
    kcl_version: str = DEFAULT_KCL_VERSION,
    providers: tuple[str, ...] = ("unifi", "cloudflare"),
) -> dict[str, dagger.File]:
    """Select validated provider files from one deterministic native JSON snapshot."""
    try:
        kcl_image(kcl_version)
    except ValueError:
        raise KCLGenerationError("KCL version has no reviewed image pin") from None
    if not providers or any(provider not in ("unifi", "cloudflare") for provider in providers):
        raise KCLGenerationError("Select unifi and/or cloudflare generation")
    try:
        manifest = tomllib.loads(await source.file("kcl.mod").contents())
    except Exception:
        raise KCLGenerationError("No valid kcl.mod found in source directory") from None
    try:
        await source.file("main.k").contents()
    except Exception:
        raise KCLGenerationError("Entry point file not found: main.k") from None

    dependencies = manifest.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise KCLGenerationError("kcl.mod dependencies must be an object")
    lock_content = None
    if dependencies:
        try:
            lock_content = await source.file("kcl.mod.lock").contents()
            locked = tomllib.loads(lock_content).get("dependencies", {})
        except Exception:
            raise KCLGenerationError("KCL dependencies require a valid kcl.mod.lock") from None
        for dependency, declaration in dependencies.items():
            resolution = locked.get(dependency) if isinstance(locked, dict) else None
            if not isinstance(resolution, dict) or not resolution:
                raise KCLGenerationError("KCL dependency is missing its locked resolution")
            if isinstance(declaration, str):
                pinned = bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", declaration))
                matches = resolution.get("version") == declaration
            elif isinstance(declaration, dict) and "git" in declaration:
                commit, tag = declaration.get("commit"), declaration.get("tag")
                pinned = (
                    bool(
                        isinstance(commit, str)
                        and re.fullmatch(r"[0-9a-fA-F]{40}", commit)
                        or isinstance(tag, str)
                        and re.fullmatch(r"v?\d+\.\d+\.\d+(?:[-+][\w.-]+)?", tag)
                    )
                    and "branch" not in declaration
                )
                matches = resolution.get("url") == declaration["git"] and (
                    resolution.get("commit") == commit
                    if commit
                    else resolution.get("git_tag") == tag
                )
            else:
                pinned = matches = False
            if not pinned or not matches:
                raise KCLGenerationError(
                    "KCL dependency requires a matching exact version/commit lock"
                )

    ctr = kcl_container(kcl_version).with_directory("/src", source).with_workdir("/src")
    try:
        ctr = ctr.with_exec(
            ["kcl", "run", "main.k", "--format", "json", "--output", "/tmp/kcl-output.json"]
        )
        kcl_output = await ctr.file("/tmp/kcl-output.json").contents()
        if lock_content is not None:
            resolved_lock = await ctr.file("/src/kcl.mod.lock").contents()
            if resolved_lock != lock_content:
                raise KCLGenerationError(
                    "KCL changed its dependency lock; perform a reviewed update first"
                )
    except KCLGenerationError:
        raise
    except Exception as error:
        exit_code = getattr(error, "exit_code", None)
        status = f" (exit code {exit_code})" if isinstance(exit_code, int) else ""
        raise KCLGenerationError(
            f"KCL execution failed{status}; check source syntax, validation and locked dependencies"
        ) from None
    if not kcl_output.strip():
        raise KCLGenerationError("KCL produced empty output")
    try:
        snapshot = json.loads(kcl_output)
    except json.JSONDecodeError as error:
        raise KCLGenerationError(
            "KCL snapshot: expected valid JSON; "
            f"parse error at line {error.lineno}, column {error.colno}"
        ) from None
    if not isinstance(snapshot, dict):
        raise KCLGenerationError("KCL snapshot: expected object")

    selected = {}
    for provider in providers:
        key = "unifi_output" if provider == "unifi" else "cf_output"
        output = snapshot.get(key)
        if output is None:
            raise KCLGenerationError(
                f"main.k does not export '{key}'. Hint: Export the selected provider configuration."
            )
        _validate_generated_config(output, provider)
        selected[provider] = output
    # Validate every requested output before publishing any file.
    return {
        provider: dagger.dag.file(
            f"{provider}.json", json.dumps(output, sort_keys=True, indent=2) + "\n"
        )
        for provider, output in selected.items()
    }


@object_type
class UnifiCloudflareGlue:
    """UniFi Cloudflare Glue - Hybrid DNS infrastructure management."""

    @function
    async def hello(self, name: Annotated[str, Doc("Name to greet")] = "World") -> str:
        """Return a greeting message for verification."""
        return f"✓ Hello, {name}! from unifi-cloudflare-glue"

    @function
    async def verify_offline(self, source: dagger.Directory) -> str:
        """Run credential-free verification without exporting checkout files."""
        module_source = dagger.dag.current_module().source()
        for root in ("glue", "unifi-dns", "cloudflare-tunnel"):
            await module_source.directory("terraform/modules/" + root).entries()
        try:
            from offline import offline_verification_container  # type: ignore[import-not-found]
        except ModuleNotFoundError:
            from .offline import offline_verification_container

        return await offline_verification_container(source).stdout()

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
            dagger --engine "$DAGGER_ENGINE" api call -m . version --source=.
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
        kcl_version: Annotated[str, Doc("Pinned KCL version to use")] = "0.12.4",
    ) -> dagger.File:
        """
        Generate UniFi JSON configuration from KCL schemas.

        Select unifi_output from the consumer main.k native JSON snapshot,
        validate its Terraform input shape and return a canonical JSON File.
        No provider credential or live infrastructure access is required.

        Args:
            source: Consumer directory with kcl.mod and main.k exporting unifi_output
            kcl_version: Qualified KCL version (default: "0.12.4")

        Returns:
            dagger.File containing the generated UniFi JSON configuration

        Example:
            dagger --engine "$DAGGER_ENGINE" api call -m . generate-unifi-config \\
                --source=./kcl export --path=./unifi.json
        """
        return (await _generate_configs(source, kcl_version, ("unifi",)))["unifi"]

    def _validate_backend_config(
        self,
        backend_type: str,
        backend_config_file: Optional[Secret],
    ) -> tuple[bool, str]:
        """
        Validate backend configuration parameters.

        Args:
            backend_type: Type of backend (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Optional Secret URI containing backend configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Non-local backend requires config file
        if backend_type != "local" and backend_config_file is None:
            return False, (
                f"✗ Failed: Backend type '{backend_type}' requires --backend-config-file\n\n"
                f"Example:\n"
                f'  dagger --engine "$DAGGER_ENGINE" api call -m . deploy \\\n'
                f"      --kcl-source=./kcl \\\n"
                f"      --backend-type={backend_type} \\\n"
                f"      --backend-config-file=env://TF_BACKEND_CONFIG \\\n"
                f"      --backend-config-format=hcl \\\n"
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
        *,
        for_effects: bool = False,
    ) -> tuple[bool, str]:
        """
        Validate remote effect custody and mutually exclusive local preview input.

        Args:
            backend_type: Type of backend (local, s3, azurerm, gcs, remote, etc.)
            state_dir: Optional protected read-only state snapshot; no host write-back
            for_effects: Reject local deploy/destroy before preparation or mutation

        Returns:
            Tuple of (is_valid, error_message)
        """
        # A Directory is an input snapshot, not durable host write-through.
        if backend_type != "local" and state_dir is not None:
            return False, (
                "✗ Failed: Cannot use both --state-dir and --backend-type (remote backend).\n\n"
                "Use remote state for deploy/destroy, or local input only for a read-only preview."
            )

        if for_effects and backend_type == "local":
            return False, (
                "Public deploy/destroy require an explicit remote backend; "
                "local-state effects are not supported. Durable local custody is tracked "
                "separately as DLR-1; Directory input does not write back to the host."
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
        return f"""terraform {{
  backend "{backend_type}" {{}}
}}
"""

    def _generate_unifi_provider_block(self) -> str:
        """
        Generate provider.tf content for UniFi provider.

        This is used for standalone unifi-dns module deployments where the module
        doesn't have its own provider block. The glue module has its own provider
        configuration, so this is only needed for unifi-only deployments.

        Returns:
            HCL content for provider.tf file
        """
        return f"""# Provider configuration for standalone unifi-dns module
# This file is dynamically generated for unifi-only deployments
provider "unifi" {{}}
"""

    def _with_unifi_provider_environment(
        self,
        container: dagger.Container,
        unifi_url: str,
        api_url: str,
        unifi_insecure: bool,
        unifi_api_key: Optional[Secret],
        unifi_username: Optional[Secret],
        unifi_password: Optional[Secret],
    ) -> dagger.Container:
        """Configure the UniFi provider without Terraform credential variables."""
        actual_api_url = api_url if api_url else unifi_url
        container = container.with_env_variable("UNIFI_API", actual_api_url)
        container = container.with_env_variable("UNIFI_INSECURE", str(unifi_insecure).lower())
        if unifi_api_key is not None:
            return container.with_secret_variable("UNIFI_API_KEY", unifi_api_key)
        if unifi_username is not None and unifi_password is not None:
            container = container.with_secret_variable("UNIFI_USERNAME", unifi_username)
            return container.with_secret_variable("UNIFI_PASSWORD", unifi_password)
        return container

    # SDK v1.8.0 accepts cache at runtime but omits it from decorator overloads.
    @function(cache="never")  # type: ignore[call-overload]
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
        unifi_only: Annotated[
            bool, Doc("Deploy only UniFi DNS (mutually exclusive with --cloudflare-only)")
        ] = False,
        cloudflare_only: Annotated[
            bool, Doc("Deploy only Cloudflare Tunnels (mutually exclusive with --unifi-only)")
        ] = False,
        terraform_version: Annotated[
            str, Doc("Reviewed immutable Terraform release")
        ] = DEFAULT_TERRAFORM_VERSION,
        kcl_version: Annotated[str, Doc("Reviewed KCL release")] = DEFAULT_KCL_VERSION,
        backend_type: Annotated[
            str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")
        ] = "local",
        state_scope: Annotated[
            str, Doc("Existing state root: full, unifi, or cloudflare; must match selective flags")
        ] = "full",
        backend_config_file: Annotated[
            Optional[Secret],
            Doc("Secret backend configuration (required for remote backends)"),
        ] = None,
        backend_config_format: Annotated[str, Doc("Explicit backend syntax: yaml or hcl")] = "",
        state_dir: Annotated[
            Optional[dagger.Directory],
            Doc(
                "Read-only state snapshot for preview; deploy rejects local state; no host write-back"
            ),
        ] = None,
        cache_buster: Annotated[
            str, Doc("Optional non-secret run label, at most 80 letters/digits/._-; not freshness")
        ] = "",
    ) -> str:
        """
        Deploy UniFi DNS and/or Cloudflare Tunnels using one Terraform operation.

        This function generates KCL configurations and deploys them using a single
        Terraform operation. Full deployment uses terraform/modules/glue/; selective
        deployment uses the corresponding provider module without unselected inputs.

        Use --unifi-only or --cloudflare-only for selective deployment, or omit both
        for full deployment of both components.

        Authentication (pick one method for UniFi when deploying UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        Public effects require an explicit remote backend. Local state is rejected
        at entry, before generation or initialization; Directory inputs do not
        write back to the host. Durable local custody is deferred as DLR-1.
        state_scope must match the flags and existing state: full, unifi or
        cloudflare. Selective roots are not a migration from combined state.
        Live function and exec freshness are automatic; labels are metadata only.

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
            terraform_version: Reviewed digest-pinned Terraform (default: "1.13.5")
            kcl_version: Checksum-verified official KCL (default: "0.12.4")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend Secret URI (required for remote backends)
            backend_config_format: Explicit yaml or hcl syntax, never autodetected
            state_scope: Existing root ownership, matching the selected flags
            state_dir: Unsupported for effects; retained only for explicit rejection
            cache_buster: Optional bounded non-secret label, not cache correctness

        Returns:
            Bounded success summary and operation identity. Failures raise sanitized
            exceptions; partial/unknown effects require reconciliation before retry.
            A prior preview is not authorization or an approved saved plan: deploy replans.

        Example:
            # Only after separate effect authorization; DAGGER_ENGINE is the pinned receipt URI.
            dagger --engine "$DAGGER_ENGINE" api call -m . deploy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env://CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env://UNIFI_API_KEY \\
                --state-scope=full --backend-type=s3 \\
                --backend-config-file=env://TF_BACKEND_CONFIG \\
                --backend-config-format=hcl
        """
        valid_state, state_error = self._validate_state_storage_config(
            backend_type, state_dir, for_effects=True
        )
        if not valid_state:
            raise ValueError(state_error)
        validate_run_label(cache_buster)
        module_path = selected_root(unifi_only, cloudflare_only, state_scope)
        if not cloudflare_only:
            validate_unifi_auth(unifi_api_key, unifi_username, unifi_password)
        operation_id = str(uuid4())
        # Validate mutual exclusion of deployment flags
        if unifi_only and cloudflare_only:
            raise ValueError("Cannot use both --unifi-only and --cloudflare-only")

        # Optional non-secret correlation metadata; freshness is automatic.
        effective_cache_buster = cache_buster

        # Validate credentials based on deployment scope
        if unifi_only:
            # UniFi-only: require UniFi credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError(
                    "UniFi-only deployment requires either --unifi-api-key OR both --unifi-username and --unifi-password"
                )
            if using_api_key and using_password:
                raise ValueError(
                    "Cannot use both API key and username/password. Choose one authentication method."
                )
            if not unifi_url:
                raise ValueError("UniFi-only deployment requires --unifi-url")
        elif cloudflare_only:
            # Cloudflare-only: require Cloudflare credentials
            if cloudflare_token is None:
                raise ValueError("Cloudflare-only deployment requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError("Cloudflare-only deployment requires --cloudflare-account-id")
            if not zone_name:
                raise ValueError("Cloudflare-only deployment requires --zone-name")
        else:
            # Full deployment: require both sets of credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError(
                    "Full deployment requires either --unifi-api-key OR both --unifi-username and --unifi-password"
                )
            if using_api_key and using_password:
                raise ValueError(
                    "Cannot use both API key and username/password. Choose one authentication method."
                )
            if not unifi_url:
                raise ValueError("Full deployment requires --unifi-url")
            if cloudflare_token is None:
                raise ValueError("Full deployment requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError("Full deployment requires --cloudflare-account-id")
            if not zone_name:
                raise ValueError("Full deployment requires --zone-name")

        results = []

        # Phase 1: Generate KCL configurations (conditionally based on deployment scope)
        results.append("=" * 60)
        results.append("PHASE 1: Generating KCL configurations")
        results.append("=" * 60)

        # Generation remains deterministic; live execs carry their own nonce.
        effective_kcl_source = kcl_source

        unifi_dir = None
        cloudflare_dir = None
        try:
            selected_configs = await _generate_configs(
                kcl_source,
                kcl_version,
                (
                    ("unifi",)
                    if unifi_only
                    else ("cloudflare",) if cloudflare_only else ("unifi", "cloudflare")
                ),
            )
        except Exception as error:
            raise RuntimeError(_safe_exec_error("Configuration generation", error)) from None

        if not cloudflare_only:  # Generate UniFi config unless cloudflare-only
            try:
                unifi_file = selected_configs["unifi"]
                unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
                results.append("✓ UniFi configuration generated")
            except Exception as e:
                raise RuntimeError(_safe_exec_error("Could not generate UniFi config", e)) from None
        else:
            results.append("○ UniFi configuration skipped (--cloudflare-only)")

        if not unifi_only:  # Generate Cloudflare config unless unifi-only
            try:
                cloudflare_file = selected_configs["cloudflare"]
                cloudflare_dir = dagger.dag.directory().with_file(
                    "cloudflare.json", cloudflare_file
                )
                results.append("✓ Cloudflare configuration generated")
            except Exception as e:
                raise RuntimeError(
                    _safe_exec_error("Could not generate Cloudflare config", e)
                ) from None
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
            raise ValueError(error_msg)

        # Validate mutual exclusion between state_dir and remote backend
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            raise ValueError(error_msg)

        actual_api_url = api_url if api_url else unifi_url
        using_persistent_state = state_dir is not None

        # Prepare the same root and sibling layout used by plan and destroy.
        try:
            ctr, workdir = prepare_root(
                dagger.dag, terraform_image(terraform_version), module_path, backend_type
            )
            ctr = ctr.with_env_variable("OPERATION_ID", operation_id)
        except Exception as e:
            raise RuntimeError(_safe_exec_error("Terraform preparation", e)) from None

        # Mount configuration files conditionally
        if unifi_dir is not None:
            ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
        if cloudflare_dir is not None:
            ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                ctr = await _with_backend_secret(ctr, backend_config_file, backend_config_format)
            except Exception as e:
                raise RuntimeError(
                    _safe_exec_error("Backend configuration processing", e)
                ) from None

        # Set up environment variables based on which module is being used
        if module_path == "cloudflare-tunnel":
            # Cloudflare module expects config_file (not cloudflare_config_file)
            # Pass account_id and zone_name as overrides to allow CLI parameters to take precedence
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable(
                    "TF_VAR_config_file", "/workspace/cloudflare/cloudflare.json"
                )
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
                ctr = ctr.with_env_variable(
                    "TF_VAR_unifi_config_file", "/workspace/unifi/unifi.json"
                )
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable(
                    "TF_VAR_cloudflare_config_file", "/workspace/cloudflare/cloudflare.json"
                )
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)

        # Add authentication secrets conditionally
        if unifi_only or not cloudflare_only:  # UniFi credentials needed
            ctr = self._with_unifi_provider_environment(
                ctr,
                unifi_url,
                actual_api_url,
                unifi_insecure,
                unifi_api_key,
                unifi_username,
                unifi_password,
            )

        if cloudflare_only or not unifi_only:  # Cloudflare credentials needed
            if cloudflare_token:
                # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
                ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

        ctr = ctr.with_workdir(workdir)

        # Run terraform init
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend([f"-backend-config={BACKEND_SECRET_PATH}"])

        try:
            ctr = live_exec(ctr, init_cmd)
            _ = await ctr.stdout()
            results.append("✓ Terraform init completed")
        except Exception as e:
            error_msg = f"✗ Failed: {_safe_exec_error('Terraform init', e, operation_id)}"
            if backend_type != "local":
                error_msg += (
                    "\n\nBackend configuration troubleshooting:\n"
                    "  - Verify the backend Secret matches the explicit yaml/hcl format\n"
                    "  - Check credentials in environment variables\n"
                    "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                )
            raise RuntimeError(error_msg) from None

        # Run terraform apply from the successful initialization snapshot.
        try:
            ctr = live_exec(ctr, ["terraform", "apply", "-auto-approve", "-input=false"])
            apply_result = await ctr.stdout()
            results.append("✓ Terraform apply completed")
        except Exception as e:
            raise RuntimeError(_safe_exec_error("Terraform apply", e, operation_id)) from None

        # Final summary
        results.append("")
        results.append("=" * 60)
        results.append("DEPLOYMENT SUMMARY")
        results.append("=" * 60)

        # Report the caller's optional non-secret correlation label.
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
                "Explicit credential disclosure (separate authorization required):",
                "Use the pinned receipt engine and a protected caller/output, never ordinary logs.",
                "Replace quoted placeholders; original host paths are unavailable.",
                "Use module source and the same backend identity/Secret/format as deploy.",
                "Use an access-controlled export destination; credential files are owner-only.",
            ]

            dagger_cmd_parts = [
                'dagger --engine "$DAGGER_ENGINE" api call -m . get-tunnel-secrets \\',
                "    --source='<module-source>' \\",
                "    --protected-disclosure \\",
                f"    --cloudflare-token=env://CF_TOKEN \\",
                f"    --cloudflare-account-id={cloudflare_account_id} \\",
                f"    --zone-name={zone_name}",
            ]

            if backend_type != "local":
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --backend-type={backend_type} \\")
                dagger_cmd_parts.append("    --backend-config-file=env://TF_BACKEND_CONFIG \\")
                dagger_cmd_parts.append(
                    f"    --backend-config-format={backend_config_format} \\\n"
                    "    export --path='<protected-output-directory>'"
                )

            if state_dir is not None:
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append("    --state-dir='<protected-read-only-state-input>'")

            guidance_lines.extend(dagger_cmd_parts)
            guidance_lines.extend(
                [
                    "",
                    "Export credentials only to the separately approved protected destination.",
                    "Do not paste tunnel tokens into command arguments, chat or CI artifacts.",
                    "",
                    "For detailed setup instructions, see:",
                    "  examples/homelab-media-stack/README.md",
                    "-" * 60,
                ]
            )

            results.extend(guidance_lines)
        else:
            results.append(
                "✓ Both UniFi DNS and Cloudflare Tunnel deployments completed successfully"
            )

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
                "Explicit credential disclosure (separate authorization required):",
                "Use the pinned receipt engine and a protected caller/output, never ordinary logs.",
                "Replace quoted placeholders; original host paths are unavailable.",
                "Use module source and the same backend identity/Secret/format as deploy.",
                "Use an access-controlled export destination; credential files are owner-only.",
            ]

            dagger_cmd_parts = [
                'dagger --engine "$DAGGER_ENGINE" api call -m . get-tunnel-secrets \\',
                "    --source='<module-source>' \\",
                "    --protected-disclosure \\",
                f"    --cloudflare-token=env://CF_TOKEN \\",
                f"    --cloudflare-account-id={cloudflare_account_id} \\",
                f"    --zone-name={zone_name}",
            ]

            if backend_type != "local":
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append(f"    --backend-type={backend_type} \\")
                dagger_cmd_parts.append("    --backend-config-file=env://TF_BACKEND_CONFIG \\")
                dagger_cmd_parts.append(
                    f"    --backend-config-format={backend_config_format} \\\n"
                    "    export --path='<protected-output-directory>'"
                )

            if state_dir is not None:
                dagger_cmd_parts.append(f" \\")
                dagger_cmd_parts.append("    --state-dir='<protected-read-only-state-input>'")

            guidance_lines.extend(dagger_cmd_parts)
            guidance_lines.extend(
                [
                    "",
                    "Export credentials only to the separately approved protected destination.",
                    "Do not paste tunnel tokens into command arguments, chat or CI artifacts.",
                    "",
                    "For detailed setup instructions, see:",
                    "  examples/homelab-media-stack/README.md",
                    "-" * 60,
                ]
            )

            results.extend(guidance_lines)

        final_result = "\n".join(results)
        return f"Operation ID: {operation_id}\n{final_result}"

    @function(cache="never")  # type: ignore[call-overload]
    async def plan(
        self,
        kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        unifi_url: Annotated[str, Doc("UniFi Controller URL")] = "",
        cloudflare_token: Annotated[Optional[Secret], Doc("Cloudflare API Token")] = None,
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")] = "",
        zone_name: Annotated[str, Doc("DNS zone name")] = "",
        api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
        unifi_api_key: Annotated[
            Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")
        ] = None,
        unifi_username: Annotated[
            Optional[Secret], Doc("UniFi username (use with password)")
        ] = None,
        unifi_password: Annotated[
            Optional[Secret], Doc("UniFi password (use with username)")
        ] = None,
        unifi_insecure: Annotated[
            bool,
            Doc("Skip TLS verification for UniFi controller (useful for self-signed certificates)"),
        ] = False,
        unifi_only: Annotated[
            bool, Doc("Plan only UniFi DNS (mutually exclusive with --cloudflare-only)")
        ] = False,
        cloudflare_only: Annotated[
            bool, Doc("Plan only Cloudflare Tunnels (mutually exclusive with --unifi-only)")
        ] = False,
        terraform_version: Annotated[
            str, Doc("Reviewed immutable Terraform release")
        ] = DEFAULT_TERRAFORM_VERSION,
        kcl_version: Annotated[str, Doc("Reviewed KCL release")] = DEFAULT_KCL_VERSION,
        backend_type: Annotated[
            str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")
        ] = "local",
        state_scope: Annotated[
            str, Doc("Existing state root: full, unifi, or cloudflare; must match selective flags")
        ] = "full",
        backend_config_file: Annotated[
            Optional[Secret],
            Doc("Secret backend configuration (required for remote backends)"),
        ] = None,
        backend_config_format: Annotated[str, Doc("Explicit backend syntax: yaml or hcl")] = "",
        state_dir: Annotated[
            Optional[dagger.Directory],
            Doc(
                "Protected read-only state snapshot for preview; no host write-back; excludes remote backend"
            ),
        ] = None,
        sensitive_artifacts: Annotated[
            bool,
            Doc("Include raw .tfplan and JSON artifacts that may contain secrets (owner-only)"),
        ] = False,
        cache_buster: Annotated[
            str, Doc("Optional non-secret run label, at most 80 letters/digits/._-; not freshness")
        ] = "",
    ) -> dagger.Directory:
        """
        Generate Terraform plans for UniFi DNS and/or Cloudflare Tunnel configurations.

        This function previews changes without applying managed-resource changes.
        Deploy replans independently; this output is not saved-plan approval or
        authorization. Full scope uses glue with sibling modules; selective scope
        uses the existing independent state's matching root, never a state migration.

        Use --unifi-only or --cloudflare-only for selective planning, or omit both
        for full planning of both components.

        Authentication (pick one method for UniFi when planning UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        Remote previews require a backend Secret URI and explicit yaml/hcl format.
        Local previews may read a protected state snapshot but do not write back
        to the host or enable local effects. DLR-1 durable local custody is deferred.
        state_scope must match the flags and existing state. Provider/backend reads
        require their own authorization; a no-op is not full-pipeline acceptance.

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
            terraform_version: Reviewed digest-pinned Terraform (default: "1.13.5")
            kcl_version: Checksum-verified official KCL (default: "0.12.4")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend Secret URI (required for remote backends)
            backend_config_format: Explicit yaml or hcl syntax, never autodetected
            state_scope: Existing root ownership, matching the selected flags
            state_dir: Protected read-only state snapshot, mutually exclusive with remote backend
            sensitive_artifacts: Explicitly include raw Terraform plan artifacts
            cache_buster: Optional bounded non-secret label; freshness is automatic

        Returns:
            Directory containing plan.txt and plan-summary.txt by default. Review
            text output for unclassified sensitive data before sharing. When
            sensitive_artifacts is enabled, owner-only plan.tfplan, plan.json, and
            SENSITIVE-ARTIFACTS.md are included as well.

        Example:
            # Separately authorized remote read; DAGGER_ENGINE is the pinned receipt URI.
            dagger --engine "$DAGGER_ENGINE" api call -m . plan \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env://CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env://UNIFI_API_KEY \\
                --state-scope=full --backend-type=s3 \\
                --backend-config-file=env://TF_BACKEND_CONFIG \\
                --backend-config-format=hcl \\
                export --path=./plans
        """
        validate_run_label(cache_buster)
        module_path = selected_root(unifi_only, cloudflare_only, state_scope)
        if not cloudflare_only:
            validate_unifi_auth(unifi_api_key, unifi_username, unifi_password)
        operation_id = str(uuid4())
        # Validate mutual exclusion of deployment flags
        if unifi_only and cloudflare_only:
            raise ValueError("✗ Failed: Cannot use both --unifi-only and --cloudflare-only")

        # Optional non-secret correlation metadata; freshness is automatic.
        effective_cache_buster = cache_buster

        # Validate credentials based on deployment scope
        if unifi_only:
            # UniFi-only: require UniFi credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError(
                    "✗ Failed: UniFi-only planning requires either --unifi-api-key OR both --unifi-username and --unifi-password"
                )
            if using_api_key and using_password:
                raise ValueError(
                    "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."
                )
            if not unifi_url:
                raise ValueError("✗ Failed: UniFi-only planning requires --unifi-url")
        elif cloudflare_only:
            # Cloudflare-only: require Cloudflare credentials
            if cloudflare_token is None:
                raise ValueError("✗ Failed: Cloudflare-only planning requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError(
                    "✗ Failed: Cloudflare-only planning requires --cloudflare-account-id"
                )
            if not zone_name:
                raise ValueError("✗ Failed: Cloudflare-only planning requires --zone-name")
        else:
            # Full deployment: require both sets of credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError(
                    "✗ Failed: Full deployment planning requires either --unifi-api-key OR both --unifi-username and --unifi-password"
                )
            if using_api_key and using_password:
                raise ValueError(
                    "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."
                )
            if not unifi_url:
                raise ValueError("✗ Failed: Full deployment planning requires --unifi-url")
            if cloudflare_token is None:
                raise ValueError("✗ Failed: Full deployment planning requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError(
                    "✗ Failed: Full deployment planning requires --cloudflare-account-id"
                )
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
        # Generation remains deterministic; live execs carry their own nonce.
        effective_kcl_source = kcl_source

        unifi_dir = None
        cloudflare_dir = None
        try:
            selected_configs = await _generate_configs(
                kcl_source,
                kcl_version,
                (
                    ("unifi",)
                    if unifi_only
                    else ("cloudflare",) if cloudflare_only else ("unifi", "cloudflare")
                ),
            )
        except Exception as error:
            raise RuntimeError(_safe_exec_error("Configuration generation", error)) from None

        if not cloudflare_only:  # Generate UniFi config unless cloudflare-only
            try:
                unifi_file = selected_configs["unifi"]
                unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
            except Exception as e:
                raise RuntimeError(_safe_exec_error("Could not generate UniFi config", e)) from None

        if not unifi_only:  # Generate Cloudflare config unless unifi-only
            try:
                cloudflare_file = selected_configs["cloudflare"]
                cloudflare_dir = dagger.dag.directory().with_file(
                    "cloudflare.json", cloudflare_file
                )
            except Exception as e:
                raise RuntimeError(
                    _safe_exec_error("Could not generate Cloudflare config", e)
                ) from None

        # Create output directory
        output_dir = dagger.dag.directory()

        # Phase 2: Plan Generation using combined Terraform module
        try:
            ctr, workdir = prepare_root(
                dagger.dag, terraform_image(terraform_version), module_path, backend_type
            )
            ctr = ctr.with_env_variable("OPERATION_ID", operation_id)

            # Mount configuration files conditionally
            if unifi_dir is not None:
                ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
            if cloudflare_dir is not None:
                ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)

            # Process and mount backend config file if provided
            if backend_config_file is not None:
                ctr = await _with_backend_secret(ctr, backend_config_file, backend_config_format)

            # Set up environment variables conditionally based on deployment scope
            if unifi_url:
                ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
                ctr = ctr.with_env_variable("TF_VAR_api_url", actual_api_url)
                ctr = ctr.with_env_variable("TF_VAR_unifi_insecure", str(unifi_insecure).lower())
            if unifi_dir is not None:
                ctr = ctr.with_env_variable(
                    "TF_VAR_unifi_config_file" if module_path == "glue" else "TF_VAR_config_file",
                    "/workspace/unifi/unifi.json",
                )
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable(
                    (
                        "TF_VAR_cloudflare_config_file"
                        if module_path == "glue"
                        else "TF_VAR_config_file"
                    ),
                    "/workspace/cloudflare/cloudflare.json",
                )
            if cloudflare_account_id:
                ctr = ctr.with_env_variable(
                    (
                        "TF_VAR_cloudflare_account_id"
                        if module_path == "glue"
                        else "TF_VAR_account_id_override"
                    ),
                    cloudflare_account_id,
                )
                ctr = ctr.with_env_variable(
                    "TF_VAR_zone_name" if module_path == "glue" else "TF_VAR_zone_name_override",
                    zone_name,
                )

            # Add authentication secrets conditionally
            if unifi_only or not cloudflare_only:  # UniFi credentials needed
                ctr = self._with_unifi_provider_environment(
                    ctr,
                    unifi_url,
                    actual_api_url,
                    unifi_insecure,
                    unifi_api_key,
                    unifi_username,
                    unifi_password,
                )

            if cloudflare_only or not unifi_only:  # Cloudflare credentials needed
                if cloudflare_token:
                    # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
                    ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

            # Handle state directory mounting and setup (persistent local state)
            if state_dir is not None:
                # Import only state, not cached backend metadata or a flattened root.
                ctr = ctr.with_file(
                    f"{workdir}/terraform.tfstate",
                    state_dir.file("terraform.tfstate"),
                    permissions=0o600,
                )

            # Run terraform init
            init_cmd = ["terraform", "init"]
            if backend_config_file is not None:
                init_cmd.extend([f"-backend-config={BACKEND_SECRET_PATH}"])

            ctr = live_exec(ctr, init_cmd)
            _ = await ctr.stdout()

            # Run terraform plan - CRITICAL: Preserve container reference
            ctr = live_exec(ctr, ["terraform", "plan", "-input=false", "-out=plan.tfplan"])
            _ = await ctr.stdout()

            # Generate JSON output
            ctr = live_exec(
                ctr, ["terraform", "show", "-json", "plan.tfplan"], redirect_stdout="plan.json"
            )
            _ = await ctr.stdout()

            # Generate text output
            ctr = live_exec(
                ctr, ["terraform", "show", "-no-color", "plan.tfplan"], redirect_stdout="plan.txt"
            )
            _ = await ctr.stdout()

            # Extract plan files from POST-execution container
            plan_binary = ctr.file(f"{workdir}/plan.tfplan")
            plan_json = ctr.file(f"{workdir}/plan.json")
            plan_txt = ctr.file(f"{workdir}/plan.txt")

            # The human-readable plan is the only default plan artifact. Terraform
            # redacts values marked sensitive in this representation.
            output_dir = output_dir.with_file("plan.txt", plan_txt)

            if sensitive_artifacts:
                output_dir = output_dir.with_file("plan.tfplan", plan_binary, permissions=0o600)
                output_dir = output_dir.with_file("plan.json", plan_json, permissions=0o600)
                output_dir = output_dir.with_new_file(
                    "SENSITIVE-ARTIFACTS.md",
                    """# Sensitive Terraform plan artifacts

This directory includes raw Terraform plan formats that can retain provider
inputs, credentials, and sensitive values. Keep these files in encrypted,
access-controlled storage; do not upload them as general CI artifacts or commit
them to source control. Securely delete them as soon as review is complete.
""",
                    permissions=0o600,
                )

            # Parse inside the runtime: raw plan values never cross File.contents().
            ctr = live_exec(
                ctr,
                [
                    "python",
                    "-c",
                    "import json,sys; sys.path.insert(0,'/tooling/src/main'); "
                    "from execution import plan_counts; "
                    "print(json.dumps(plan_counts(json.load(open('plan.json')))))",
                ],
            )
            counts = json.loads(await ctr.stdout())
            if (
                not isinstance(counts, dict)
                or set(counts) != {"add", "change", "destroy", "replace"}
                or any(type(value) is not int or value < 0 for value in counts.values())
            ):
                raise RuntimeError("Invalid bounded plan summary response")
            total_add = counts["add"]
            total_change = counts["change"]
            total_destroy = counts["destroy"]

        except Exception as e:
            raise RuntimeError(
                f"✗ Failed: {_safe_exec_error('Terraform plan', e, operation_id)}"
            ) from None

        # Phase 3: Create plan summary
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Determine which components were planned
        if unifi_only:
            planned_components = "UniFi DNS only"
        elif cloudflare_only:
            planned_components = "Cloudflare Tunnels only"
        else:
            planned_components = "UniFi DNS and Cloudflare Tunnels"

        output_files = "- plan.txt     (redacted human-readable format)"
        handling_notes = "- Default safe export: raw Terraform plan formats were omitted"
        if sensitive_artifacts:
            output_files += """
- plan.tfplan  (SENSITIVE binary plan; owner-only)
- plan.json    (SENSITIVE raw JSON plan; owner-only)
- SENSITIVE-ARTIFACTS.md (secure handling and disposal warning)"""
            handling_notes = (
                "- Sensitive artifact export was explicitly enabled; follow the warning manifest"
            )

        summary_content = f"""Terraform Plan Summary
======================

Generated: {timestamp}
Operation ID: {operation_id}
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
{output_files}

Notes
-----
- Text file is optimized for manual review and diffing
{handling_notes}
- Selected Terraform root: {module_path}
- This is a preview, not saved-plan approval. Deploy replans against fresh state
  and requires separate authorization.
"""

        output_dir = output_dir.with_new_file("plan-summary.txt", summary_content)

        return output_dir

    @function(cache="never")  # type: ignore[call-overload]
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
        unifi_only: Annotated[
            bool, Doc("Destroy only UniFi DNS (mutually exclusive with --cloudflare-only)")
        ] = False,
        cloudflare_only: Annotated[
            bool, Doc("Destroy only Cloudflare Tunnels (mutually exclusive with --unifi-only)")
        ] = False,
        terraform_version: Annotated[
            str, Doc("Reviewed immutable Terraform release")
        ] = DEFAULT_TERRAFORM_VERSION,
        kcl_version: Annotated[str, Doc("Reviewed KCL release")] = DEFAULT_KCL_VERSION,
        backend_type: Annotated[
            str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")
        ] = "local",
        state_scope: Annotated[
            str, Doc("Existing state root: full, unifi, or cloudflare; must match selective flags")
        ] = "full",
        backend_config_file: Annotated[
            Optional[Secret],
            Doc("Secret backend configuration (required for remote backends)"),
        ] = None,
        backend_config_format: Annotated[str, Doc("Explicit backend syntax: yaml or hcl")] = "",
        state_dir: Annotated[
            Optional[dagger.Directory],
            Doc("Local state is unsupported for destroy; no Directory host write-back"),
        ] = None,
        cache_buster: Annotated[
            str, Doc("Optional non-secret run label, at most 80 letters/digits/._-; not freshness")
        ] = "",
    ) -> str:
        """
        Destroy resources in the existing selected remote-state root.

        Full scope uses terraform/modules/glue/ with its siblings. Selective flags
        use the matching independently managed provider root; state_scope must
        match full, unifi or cloudflare. Never use a selective flag to split state.
        Destruction requires separate authorization for the selected target.

        Authentication (pick one method for UniFi when destroying UniFi):
        1. API Key: Provide --unifi-api-key
        2. Username/Password: Provide both --unifi-username and --unifi-password

        An explicit remote backend is required. Local state is rejected at entry,
        before generation, initialization or effects. Directory input is not
        host write-through; durable local custody remains deferred as DLR-1.

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
            terraform_version: Reviewed digest-pinned Terraform (default: "1.13.5")
            kcl_version: Checksum-verified official KCL (default: "0.12.4")
            backend_type: Terraform backend type (local, s3, azurerm, gcs, remote, etc.)
            backend_config_file: Backend Secret URI (required for remote backends)
            backend_config_format: Explicit yaml or hcl syntax, never autodetected
            state_scope: Existing root ownership, matching the selected flags
            state_dir: Unsupported for effects; retained only for explicit rejection
            cache_buster: Optional bounded non-secret label; freshness is automatic

        Returns:
            Bounded success summary and operation identity. Failures raise sanitized
            exceptions. Reconcile partial/unknown effects before retry; source or
            state restoration is not remote-resource rollback.

        Example:
            # Only after separate destruction authorization; use the pinned receipt engine URI.
            dagger --engine "$DAGGER_ENGINE" api call -m . destroy \\
                --kcl-source=./kcl \\
                --unifi-url=https://unifi.local:8443 \\
                --cloudflare-token=env://CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --zone-name=example.com \\
                --unifi-api-key=env://UNIFI_API_KEY \\
                --state-scope=full --backend-type=s3 \\
                --backend-config-file=env://TF_BACKEND_CONFIG \\
                --backend-config-format=hcl
        """
        valid_state, state_error = self._validate_state_storage_config(
            backend_type, state_dir, for_effects=True
        )
        if not valid_state:
            raise ValueError(state_error)
        validate_run_label(cache_buster)
        module_path = selected_root(unifi_only, cloudflare_only, state_scope)
        if not cloudflare_only:
            validate_unifi_auth(unifi_api_key, unifi_username, unifi_password)
        operation_id = str(uuid4())
        # Validate mutual exclusion of destruction flags
        if unifi_only and cloudflare_only:
            raise ValueError("Cannot use both --unifi-only and --cloudflare-only")

        # Optional non-secret correlation metadata; freshness is automatic.
        effective_cache_buster = cache_buster

        # Validate credentials based on destruction scope
        if unifi_only:
            # UniFi-only: require UniFi credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError(
                    "UniFi-only destruction requires either --unifi-api-key OR both --unifi-username and --unifi-password"
                )
            if using_api_key and using_password:
                raise ValueError(
                    "Cannot use both API key and username/password. Choose one authentication method."
                )
            if not unifi_url:
                raise ValueError("UniFi-only destruction requires --unifi-url")
        elif cloudflare_only:
            # Cloudflare-only: require Cloudflare credentials
            if cloudflare_token is None:
                raise ValueError("Cloudflare-only destruction requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError("Cloudflare-only destruction requires --cloudflare-account-id")
            if not zone_name:
                raise ValueError("Cloudflare-only destruction requires --zone-name")
        else:
            # Full destruction: require both sets of credentials
            using_api_key = unifi_api_key is not None
            using_password = unifi_username is not None and unifi_password is not None
            if not using_api_key and not using_password:
                raise ValueError(
                    "Full destruction requires either --unifi-api-key OR both --unifi-username and --unifi-password"
                )
            if using_api_key and using_password:
                raise ValueError(
                    "Cannot use both API key and username/password. Choose one authentication method."
                )
            if not unifi_url:
                raise ValueError("Full destruction requires --unifi-url")
            if cloudflare_token is None:
                raise ValueError("Full destruction requires --cloudflare-token")
            if not cloudflare_account_id:
                raise ValueError("Full destruction requires --cloudflare-account-id")
            if not zone_name:
                raise ValueError("Full destruction requires --zone-name")

        results = []

        # Phase 1: Generate KCL configurations (conditionally based on destruction scope)
        results.append("=" * 60)
        results.append("PHASE 1: Generating KCL configurations")
        results.append("=" * 60)

        # Generation remains deterministic; live execs carry their own nonce.
        effective_kcl_source = kcl_source

        unifi_dir = None
        cloudflare_dir = None
        try:
            selected_configs = await _generate_configs(
                kcl_source,
                kcl_version,
                (
                    ("unifi",)
                    if unifi_only
                    else ("cloudflare",) if cloudflare_only else ("unifi", "cloudflare")
                ),
            )
        except Exception as error:
            raise RuntimeError(_safe_exec_error("Configuration generation", error)) from None

        if not cloudflare_only:  # Generate UniFi config unless cloudflare-only
            try:
                unifi_file = selected_configs["unifi"]
                unifi_dir = dagger.dag.directory().with_file("unifi.json", unifi_file)
                results.append("✓ UniFi configuration generated")
            except Exception as e:
                raise RuntimeError(_safe_exec_error("Could not generate UniFi config", e)) from None
        else:
            results.append("○ UniFi configuration skipped (--cloudflare-only)")

        if not unifi_only:  # Generate Cloudflare config unless unifi-only
            try:
                cloudflare_file = selected_configs["cloudflare"]
                cloudflare_dir = dagger.dag.directory().with_file(
                    "cloudflare.json", cloudflare_file
                )
                results.append("✓ Cloudflare configuration generated")
            except Exception as e:
                raise RuntimeError(
                    _safe_exec_error("Could not generate Cloudflare config", e)
                ) from None
        else:
            results.append("○ Cloudflare configuration skipped (--unifi-only)")

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

        # Prepare the same root and sibling layout used by plan and deploy.
        try:
            ctr, workdir = prepare_root(
                dagger.dag, terraform_image(terraform_version), module_path, backend_type
            )
            ctr = ctr.with_env_variable("OPERATION_ID", operation_id)
        except Exception as e:
            raise RuntimeError(_safe_exec_error("Terraform preparation", e)) from None

        # Mount configuration files conditionally
        if unifi_dir is not None:
            ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
        if cloudflare_dir is not None:
            ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)

        # Process and mount backend config file if provided
        if backend_config_file is not None:
            try:
                ctr = await _with_backend_secret(ctr, backend_config_file, backend_config_format)
            except Exception as e:
                raise RuntimeError(
                    _safe_exec_error("Backend configuration processing", e)
                ) from None

        # Set up environment variables based on which module is being used
        if module_path == "cloudflare-tunnel":
            # Cloudflare module expects config_file (not cloudflare_config_file)
            # Pass account_id and zone_name as overrides to allow CLI parameters to take precedence
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable(
                    "TF_VAR_config_file", "/workspace/cloudflare/cloudflare.json"
                )
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
                ctr = ctr.with_env_variable(
                    "TF_VAR_unifi_config_file", "/workspace/unifi/unifi.json"
                )
            if cloudflare_dir is not None:
                ctr = ctr.with_env_variable(
                    "TF_VAR_cloudflare_config_file", "/workspace/cloudflare/cloudflare.json"
                )
            if cloudflare_account_id:
                ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
                ctr = ctr.with_env_variable("TF_VAR_zone_name", zone_name)

        # Add authentication secrets conditionally
        if unifi_only or not cloudflare_only:  # UniFi credentials needed
            ctr = self._with_unifi_provider_environment(
                ctr,
                unifi_url,
                actual_api_url,
                unifi_insecure,
                unifi_api_key,
                unifi_username,
                unifi_password,
            )

        if cloudflare_only or not unifi_only:  # Cloudflare credentials needed
            if cloudflare_token:
                # Use CLOUDFLARE_API_TOKEN env var - more reliable with Dagger secrets
                ctr = ctr.with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)

        ctr = ctr.with_workdir(workdir)

        # Run terraform init
        init_cmd = ["terraform", "init"]
        if backend_config_file is not None:
            init_cmd.extend([f"-backend-config={BACKEND_SECRET_PATH}"])

        try:
            ctr = live_exec(ctr, init_cmd)
            _ = await ctr.stdout()
            results.append("✓ Terraform init completed")
        except Exception as e:
            error_msg = f"✗ Failed: {_safe_exec_error('Terraform init', e, operation_id)}"
            if backend_type != "local":
                error_msg += (
                    "\n\nBackend configuration troubleshooting:\n"
                    "  - Verify backend config file is valid HCL\n"
                    "  - Check credentials in environment variables\n"
                    "  - Ensure backend infrastructure exists (bucket, table, etc.)"
                )
            raise RuntimeError(error_msg) from None

        # Run terraform destroy (no targeting needed - using individual modules)
        destroy_cmd = ["terraform", "destroy", "-auto-approve"]

        try:
            ctr = live_exec(ctr, destroy_cmd)
            destroy_result = await ctr.stdout()
            results.append("✓ Terraform destroy completed")
        except Exception as e:
            raise RuntimeError(_safe_exec_error("Terraform destroy", e, operation_id)) from None

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

        return f"Operation ID: {operation_id}\n" + "\n".join(results)

    @function
    async def generate_cloudflare_config(
        self,
        source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
        kcl_version: Annotated[str, Doc("Pinned KCL version to use")] = "0.12.4",
    ) -> dagger.File:
        """
        Generate Cloudflare JSON configuration from KCL schemas.

        Select cf_output from the consumer main.k native JSON snapshot,
        validate its Terraform input shape and return a canonical JSON File.
        No provider credential or live infrastructure access is required.

        Args:
            source: Consumer directory with kcl.mod and main.k exporting cf_output
            kcl_version: Qualified KCL version (default: "0.12.4")

        Returns:
            dagger.File containing the generated Cloudflare JSON configuration

        Example:
            dagger --engine "$DAGGER_ENGINE" api call -m . generate-cloudflare-config \\
                --source=./kcl export --path=./cloudflare.json
        """
        return (await _generate_configs(source, kcl_version, ("cloudflare",)))["cloudflare"]

    def _generate_test_id(self) -> str:
        """Generate a random test identifier."""
        return "test-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))

    def _generate_test_configs(
        self,
        test_id: str,
        cloudflare_zone: str,
        cloudflare_account_id: str,
        test_mac: str = "aa:bb:cc:dd:ee:ff",
        unifi_domain: str = "",
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
                            "no_tls_verify": False,
                        }
                    ],
                }
            },
        }

        # Build UniFi config matching terraform/modules/unifi-dns/variables.tf
        unifi_config = {
            "devices": [
                {
                    "friendly_hostname": test_id,
                    "domain": effective_unifi_domain,
                    "service_cnames": [],
                    "nics": [{"mac_address": test_mac, "nic_name": "eth0", "service_cnames": []}],
                }
            ],
            "default_domain": effective_unifi_domain,
            "site": "default",
        }

        return {
            "cloudflare": json.dumps(cloudflare_config, indent=2),
            "unifi": json.dumps(unifi_config, indent=2),
        }

    async def _unifi_dns_exists(
        self,
        hostname: str,
        site: str,
        unifi_url: str,
        api_url: str,
        unifi_insecure: bool,
        unifi_api_key: Optional[Secret],
        unifi_username: Optional[Secret],
        unifi_password: Optional[Secret],
        terraform_version: str,
        deadline: float,
    ) -> bool:
        """Query the provider's DNS data source for an externally visible record."""
        if unifi_api_key is not None:
            return bool(
                await self._unifi_dns_prefix_count(
                    hostname,
                    site,
                    unifi_url,
                    api_url,
                    unifi_insecure,
                    unifi_api_key,
                    deadline,
                    exact=True,
                )
            )
        validation_hcl = f"""terraform {{
  required_providers {{
    unifi = {{
      source  = "filipowm/unifi"
      version = "~> 1.1.0"
    }}
  }}
}}

provider "unifi" {{}}

data "unifi_dns_record" "integration" {{
  name = {json.dumps(hostname)}
  site = {json.dumps(site)}
}}

output "record_id" {{
  value = data.unifi_dns_record.integration.id
}}
"""
        validation_dir = dagger.dag.directory().with_new_file("main.tf", validation_hcl)
        container = (
            dagger.dag.container()
            .from_(terraform_image(terraform_version))
            .with_directory("/validation", validation_dir)
            .with_workdir("/validation")
        )
        container = self._with_unifi_provider_environment(
            container,
            unifi_url,
            api_url,
            unifi_insecure,
            unifi_api_key,
            unifi_username,
            unifi_password,
        )
        try:
            container = live_exec(container, ["terraform", "init", "-input=false"])
            await _before_deadline(container.stdout(), deadline)
            container = live_exec(
                container, ["terraform", "apply", "-refresh-only", "-auto-approve", "-input=false"]
            )
            await _before_deadline(container.stdout(), deadline)
            return True
        except dagger.ExecError as error:
            raise RuntimeError(_safe_exec_error("UniFi DNS validation", error)) from None

    async def _unifi_dns_prefix_count(
        self,
        prefix: str,
        site: str,
        unifi_url: str,
        api_url: str,
        unifi_insecure: bool,
        unifi_api_key: Secret,
        deadline: float,
        exact: bool = False,
    ) -> int:
        """Count live static-DNS names matching a run prefix through the API."""
        actual_api_url = (api_url if api_url else unifi_url).rstrip("/")
        container = (
            dagger.dag.container()
            .from_(PYTHON_IMAGE)
            .with_file(
                "/verification/execution.py",
                dagger.dag.current_module().source().file("src/main/execution.py"),
            )
            .with_new_file("/verification/query.py", UNIFI_PREFIX_QUERY)
            .with_secret_variable("UNIFI_API_KEY", unifi_api_key)
        )
        container = live_exec(
            container,
            [
                "python",
                "/verification/query.py",
                actual_api_url,
                site,
                prefix,
                str(unifi_insecure).lower(),
                "exact" if exact else "prefix",
            ],
        )
        try:
            output = await _before_deadline(container.stdout(), deadline)
            return int(output.strip())
        except Exception as error:
            raise RuntimeError(_safe_exec_error("UniFi DNS prefix query", error)) from None

    @function(cache="never")  # type: ignore[call-overload]
    async def test_unifi_dns_baseline(
        self,
        source: Annotated[Directory, Doc("Project source containing the baseline fixture")],
        run_id: Annotated[
            str,
            Doc("Unique 6-32 character lowercase run identifier for sandbox isolation"),
        ],
        unifi_url: Annotated[str, Doc("UniFi controller URL")],
        unifi_api_key: Annotated[Secret, Doc("UniFi API key")],
        api_url: Annotated[str, Doc("UniFi API URL; defaults to unifi_url")] = "",
        site: Annotated[str, Doc("UniFi site for disposable DNS records")] = "default",
        unifi_insecure: Annotated[bool, Doc("Skip UniFi TLS verification")] = False,
        a_record_count: Annotated[int, Doc("Number of disposable A records")] = 64,
        cname_record_count: Annotated[int, Doc("Number of disposable CNAME records")] = 64,
        test_timeout: Annotated[str, Doc("Shared lifecycle timeout, such as 10m")] = "10m",
        terraform_version: Annotated[
            str, Doc("Reviewed Terraform image version")
        ] = DEFAULT_TERRAFORM_VERSION,
        cache_buster: Annotated[
            str, Doc("Optional bounded non-secret run label; not freshness")
        ] = "",
    ) -> str:
        """Run the isolated UniFi v1.1 DNS create/read/update/destroy baseline.

        The API key is mounted as a Dagger secret and Terraform state remains
        inside the lifecycle containers. Cleanup and provider-level absence
        checks are mandatory. Use only after authorizing live UniFi DNS changes.

        Example:
            dagger --engine "$DAGGER_ENGINE" api call -m . test-unifi-dns-baseline \\
                --source=. \\
                --run-id=20260828-a1b2c3 \\
                --unifi-url=https://192.168.60.1 \\
                --unifi-api-key=env://UNIFI_API_KEY
        """
        validate_run_label(cache_buster)
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{4,30}[a-z0-9]", run_id):
            raise ValueError(
                "run_id must be 6-32 lowercase letters, digits, or hyphens "
                "and may not start or end with a hyphen"
            )
        if not 1 <= a_record_count <= 200:
            raise ValueError("a_record_count must be from 1 through 200")
        if not 1 <= cname_record_count <= 200:
            raise ValueError("cname_record_count must be from 1 through 200")

        timeout_seconds = _parse_duration(test_timeout)
        cleanup_reserve = min(120.0, max(30.0, timeout_seconds * 0.25))
        if timeout_seconds <= cleanup_reserve:
            cleanup_reserve = max(1.0, timeout_seconds / 2)
        lifecycle_deadline = time.monotonic() + timeout_seconds
        operation_deadline = lifecycle_deadline - cleanup_reserve

        sandbox_zone = f"unifi-poc-{run_id}.solomonhd.ai"
        validation_names = [
            f"a-001.{sandbox_zone}",
            f"cname-001.{sandbox_zone}",
        ]
        state_file: Optional[dagger.File] = None
        primary_failure: Optional[str] = None
        cleanup_failure: Optional[str] = None
        baseline_unknown = False
        created = False
        zero_drift = False
        updated = False
        read_validated = False
        absence_validated = False

        def configured_container(update_first_record: bool) -> dagger.Container:
            fixture = source.directory("terraform/fixtures/unifi-provider-baseline")
            container = (
                dagger.dag.container()
                .from_(terraform_image(terraform_version))
                .with_directory("/fixture", fixture)
                .with_workdir("/fixture")
                .with_env_variable("TF_IN_AUTOMATION", "true")
                .with_env_variable("TF_INPUT", "false")
                .with_env_variable("TF_VAR_run_id", run_id)
                .with_env_variable("TF_VAR_site", site)
                .with_env_variable("TF_VAR_a_record_count", str(a_record_count))
                .with_env_variable("TF_VAR_cname_record_count", str(cname_record_count))
                .with_env_variable("TF_VAR_update_first_record", str(update_first_record).lower())
            )
            if cache_buster:
                container = container.with_env_variable("CACHE_BUSTER", cache_buster)
            return self._with_unifi_provider_environment(
                container,
                unifi_url,
                api_url,
                unifi_insecure,
                unifi_api_key,
                None,
                None,
            )

        container = configured_container(update_first_record=False)
        try:
            container = live_exec(container, ["terraform", "init", "-input=false", "-no-color"])
            await _before_deadline(container.stdout(), operation_deadline)

            container = live_exec(
                container, ["terraform", "apply", "-auto-approve", "-input=false", "-no-color"]
            )
            await _before_deadline(container.stdout(), operation_deadline)
            state_file = container.file("/fixture/terraform.tfstate")
            await _before_deadline(state_file.sync(), operation_deadline)
            created = True

            container = live_exec(
                container,
                [
                    "terraform",
                    "plan",
                    "-detailed-exitcode",
                    "-input=false",
                    "-no-color",
                    "-out=/tmp/zero-drift.tfplan",
                ],
            )
            await _before_deadline(container.stdout(), operation_deadline)
            zero_drift = True

            for name in validation_names:
                exists = await self._unifi_dns_exists(
                    name,
                    site,
                    unifi_url,
                    api_url,
                    unifi_insecure,
                    unifi_api_key,
                    None,
                    None,
                    terraform_version,
                    operation_deadline,
                )
                if not exists:
                    raise RuntimeError(f"provider read did not find expected sandbox record {name}")
            read_validated = True

            container = container.with_env_variable("TF_VAR_update_first_record", "true")
            container = live_exec(
                container,
                [
                    "terraform",
                    "plan",
                    "-detailed-exitcode",
                    "-input=false",
                    "-no-color",
                    "-out=/tmp/update.tfplan",
                ],
                expect=dagger.ReturnType.ANY,
            )
            await _before_deadline(container.stdout(), operation_deadline)
            if await _before_deadline(container.exit_code(), operation_deadline) != 2:
                raise RuntimeError("Expected a nonempty baseline update plan")
            container = live_exec(
                container,
                ["terraform", "apply", "-auto-approve", "-input=false", "/tmp/update.tfplan"],
            )
            await _before_deadline(container.stdout(), operation_deadline)
            state_file = container.file("/fixture/terraform.tfstate")
            await _before_deadline(state_file.sync(), operation_deadline)
            updated = True
        except asyncio.CancelledError:
            baseline_unknown = True
            raise
        except Exception as error:
            baseline_unknown = isinstance(error, TimeoutError)
            primary_failure = _safe_exec_error("UniFi DNS baseline lifecycle", error)
            try:
                candidate_state = container.file("/fixture/terraform.tfstate")
                await _before_deadline(candidate_state.sync(), lifecycle_deadline)
                state_file = candidate_state
            except Exception:
                pass
        finally:
            if baseline_unknown:
                cleanup_failure = (
                    f"baseline {run_id} outcome and state custody unknown; confirm termination "
                    "and reconcile remote resources/state before cleanup or retry"
                )
            elif state_file is None:
                cleanup_failure = "no Terraform state was available for mandatory cleanup"
            else:
                try:
                    cleanup_container = configured_container(update_first_record=True).with_file(
                        "/fixture/terraform.tfstate", state_file
                    )
                    cleanup_container = live_exec(
                        cleanup_container, ["terraform", "init", "-input=false", "-no-color"]
                    )
                    await _before_deadline(cleanup_container.stdout(), lifecycle_deadline)
                    cleanup_container = live_exec(
                        cleanup_container,
                        [
                            "terraform",
                            "destroy",
                            "-auto-approve",
                            "-input=false",
                            "-no-color",
                        ],
                    )
                    await _before_deadline(cleanup_container.stdout(), lifecycle_deadline)
                except Exception as error:
                    cleanup_failure = _safe_exec_error("UniFi DNS baseline cleanup", error)

            if cleanup_failure is None:
                try:
                    remaining = await self._unifi_dns_prefix_count(
                        sandbox_zone,
                        site,
                        unifi_url,
                        api_url,
                        unifi_insecure,
                        unifi_api_key,
                        lifecycle_deadline,
                    )
                    if remaining:
                        cleanup_failure = (
                            f"API absence verification found {remaining} records in "
                            f"the sandbox namespace {sandbox_zone}"
                        )
                    else:
                        absence_validated = True
                except Exception as error:
                    cleanup_failure = _safe_exec_error(
                        "UniFi DNS baseline absence verification", error
                    )

        failures = [failure for failure in (primary_failure, cleanup_failure) if failure]
        if failures:
            raise RuntimeError("; ".join(failures))

        return "\n".join(
            [
                "UniFi DNS baseline lifecycle passed",
                f"Sandbox: {sandbox_zone}",
                f"Records: {a_record_count} A + {cname_record_count} CNAME",
                f"Create completed: {created}",
                f"Provider reads completed: {read_validated}",
                f"Second plan zero drift: {zero_drift}",
                f"Benign update completed: {updated}",
                f"Destroy and absence verification completed: {absence_validated}",
            ]
        )

    async def _cloudflare_resource_counts(
        self,
        account_id: str,
        zone_name: str,
        tunnel_name: str,
        hostname: str,
        cloudflare_token: Secret,
        deadline: float,
    ) -> tuple[int, int]:
        """Return freshly checked counts only after validating all HTTP envelopes."""
        try:
            container = (
                dagger.dag.container()
                .from_(PYTHON_IMAGE)
                .with_file(
                    "/verification/execution.py",
                    dagger.dag.current_module().source().file("src/main/execution.py"),
                )
                .with_new_file("/verification/query.py", CLOUDFLARE_QUERY)
                .with_secret_variable("CLOUDFLARE_API_TOKEN", cloudflare_token)
            )
            container = live_exec(
                container,
                ["python", "/verification/query.py", account_id, zone_name, tunnel_name, hostname],
            )
            counts = json.loads(await _before_deadline(container.stdout(), deadline))
            if (
                not isinstance(counts, list)
                or len(counts) != 2
                or any(type(value) is not int or value < 0 for value in counts)
            ):
                raise ValueError("Invalid bounded API count response")
            return counts[0], counts[1]
        except Exception as error:
            raise RuntimeError(_safe_exec_error("Cloudflare resource validation", error)) from None

    @function(cache="never")  # type: ignore[call-overload]
    async def test_integration(
        self,
        source: Annotated[
            Directory, Doc("Project source directory containing KCL and Terraform configs")
        ],
        cloudflare_zone: Annotated[str, Doc("DNS zone for test records (e.g., test.example.com)")],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API token")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare account ID")],
        unifi_url: Annotated[str, Doc("UniFi controller URL (e.g., https://unifi.local:8443)")],
        api_url: Annotated[str, Doc("UniFi API URL (often same as unifi_url)")],
        unifi_api_key: Annotated[
            Optional[Secret], Doc("UniFi API key (mutually exclusive with username/password)")
        ] = None,
        unifi_username: Annotated[
            Optional[Secret], Doc("UniFi username (use with password)")
        ] = None,
        unifi_password: Annotated[
            Optional[Secret], Doc("UniFi password (use with username)")
        ] = None,
        unifi_insecure: Annotated[
            bool,
            Doc("Skip TLS verification for UniFi controller (useful for self-signed certificates)"),
        ] = False,
        cleanup: Annotated[
            bool, Doc("Whether to cleanup resources after test (default: true)")
        ] = True,
        validate_connectivity: Annotated[
            bool, Doc("Whether to test actual HTTP connectivity")
        ] = False,
        test_timeout: Annotated[str, Doc("Timeout for test operations (e.g., 5m)")] = "5m",
        cache_buster: Annotated[
            str, Doc("Optional non-secret run label, at most 80 letters/digits/._-; not freshness")
        ] = "",
        wait_before_cleanup: Annotated[
            int, Doc("Seconds to wait between validation and cleanup for manual verification")
        ] = 0,
        test_mac_address: Annotated[
            str,
            Doc(
                "MAC address for test device (must exist in UniFi controller, e.g., 'aa:bb:cc:dd:ee:ff')"
            ),
        ] = "aa:bb:cc:dd:ee:ff",
        terraform_version: Annotated[
            str, Doc("Reviewed immutable Terraform release")
        ] = DEFAULT_TERRAFORM_VERSION,
        kcl_version: Annotated[str, Doc("Reviewed KCL release")] = DEFAULT_KCL_VERSION,
    ) -> str:
        """
        Run integration test creating ephemeral DNS resources with real APIs.

        Creates temporary Cloudflare tunnel and DNS records, UniFi DNS records,
        validates the setup, and attempts cleanup with a separate outcome ledger.
        This is an effectful disposable lifecycle, not an offline verification
        or a production deployment shortcut. Explicit authorization is required.
        Cancellation/disconnect can leave unknown effects; reconcile before retry.

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
            cache_buster: Optional bounded non-secret label; live freshness is automatic
            wait_before_cleanup: Seconds to wait between validation and cleanup.
                Allows manual verification of created resources before they are destroyed.
            test_mac_address: MAC address for the test device. This MAC must exist in your
                UniFi controller. Use a real device MAC from your network (default: "aa:bb:cc:dd:ee:ff")
            terraform_version: Reviewed digest-pinned Terraform (default: "1.13.5")
            kcl_version: Checksum-verified official KCL (default: "0.12.4")

        Returns:
            Detailed test report with created resources, validation results, and cleanup status.

        Example usage:
            # Only after sandbox mutation authorization; use the pinned receipt engine URI.
            dagger --engine "$DAGGER_ENGINE" api call -m . test-integration \\
                --source=. \\
                --cloudflare-zone=test.example.com \\
                --cloudflare-token=env://CF_TOKEN \\
                --cloudflare-account-id=xxx \\
                --unifi-api-key=env://UNIFI_API_KEY \\
                --unifi-url=https://unifi.local:8443 \\
                --api-url=https://unifi.local:8443 \\
                --test-mac-address=de:ad:be:ef:12:34
        """
        validate_run_label(cache_buster)
        # The transitional label is metadata; live execs enforce freshness.
        effective_cache_buster = cache_buster

        # Validate UniFi authentication
        using_api_key = unifi_api_key is not None
        using_password = unifi_username is not None and unifi_password is not None

        if not using_api_key and not using_password:
            raise ValueError(
                "Must provide either unifi_api_key OR both unifi_username and unifi_password"
            )

        if using_api_key and using_password:
            raise ValueError(
                "Cannot use both API key and username/password. Choose one authentication method."
            )

        if not cleanup:
            raise ValueError("cleanup=false is disabled for strict integration tests")

        timeout_seconds = _parse_duration(test_timeout)
        cleanup_reserve = min(60.0, max(10.0, timeout_seconds * 0.2))
        if timeout_seconds <= cleanup_reserve:
            cleanup_reserve = max(1.0, timeout_seconds / 2)
        operation_deadline = time.monotonic() + (timeout_seconds - cleanup_reserve)
        primary_failure: Optional[str] = None
        cleanup_ledger: list[dict[str, object]] = []
        effect_unknown = False

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
            f"Operation Timeout: {test_timeout}",
            f"Cleanup Reserve: {cleanup_reserve:g}s",
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
            test_id,
            cloudflare_zone,
            cloudflare_account_id,
            test_mac_address,
            unifi_domain=cloudflare_zone,
        )
        cloudflare_json = test_configs["cloudflare"]
        unifi_json = test_configs["unifi"]
        cloudflare_dir = dagger.dag.directory().with_new_file("cloudflare.json", cloudflare_json)
        unifi_dir = dagger.dag.directory().with_new_file("unifi.json", unifi_json)

        # Track cleanup status
        cleanup_status = {"cloudflare": "pending", "unifi": "pending", "state_files": "pending"}
        validation_results = {}

        # Initialize state directory variables for cleanup phase
        cloudflare_state_dir = None
        unifi_state_dir = None

        try:
            # Phase 1: Generate JSON configs for Terraform modules
            report_lines.append("PHASE 1: Generating Terraform JSON configurations...")

            report_lines.append(f"  ✓ Generated JSON configs for test ID: {test_id}")
            report_lines.append(f"  ✓ Test hostname: {test_hostname}")

            # Phase 2: Create Cloudflare resources
            report_lines.append("")
            report_lines.append("PHASE 2: Creating Cloudflare resources...")

            # Create directory with Cloudflare config for Terraform
            cloudflare_dir = dagger.dag.directory().with_new_file(
                "cloudflare.json", cloudflare_json
            )

            # Create Terraform container following deploy_cloudflare() pattern
            cf_ctr = dagger.dag.container().from_(terraform_image(terraform_version))

            # Mount Cloudflare config at /workspace
            cf_ctr = cf_ctr.with_directory("/workspace", cloudflare_dir)

            # Mount the Cloudflare Tunnel Terraform module
            try:
                tf_module = source.directory("terraform/modules/cloudflare-tunnel")
                cf_ctr = cf_ctr.with_directory("/module", tf_module)
            except Exception:
                # If module not in source, try project root
                try:
                    tf_module = (
                        dagger.dag.current_module()
                        .source()
                        .directory("terraform/modules/cloudflare-tunnel")
                    )
                    cf_ctr = cf_ctr.with_directory("/module", tf_module)
                except Exception:
                    raise RuntimeError(
                        "Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel"
                    )

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
                cf_ctr = live_exec(cf_ctr, ["terraform", "init"])
                init_result = await _before_deadline(cf_ctr.stdout(), operation_deadline)
                report_lines.append("  ✓ Terraform init completed")
            except dagger.ExecError as e:
                error_msg = _safe_exec_error("Cloudflare Terraform init", e)
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["cloudflare_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Execute terraform apply
            try:
                # Save container reference after execution
                cf_ctr = live_exec(
                    cf_ctr, ["terraform", "apply", "-auto-approve"], expect=dagger.ReturnType.ANY
                )
                apply_result = await _before_deadline(cf_ctr.stdout(), operation_deadline)
                cf_exit_code = await _before_deadline(cf_ctr.exit_code(), operation_deadline)
                report_lines.append(f"  ✓ Created tunnel: {tunnel_name}")
                report_lines.append(f"  ✓ Created DNS record: {test_hostname}")
                validation_results["cloudflare_tunnel"] = "created"
                validation_results["cloudflare_dns"] = "created"
                cleanup_ledger.append(
                    {
                        "provider": "cloudflare",
                        "resources": [tunnel_name, test_hostname],
                        "state_captured": False,
                    }
                )
            except dagger.ExecError as e:
                error_msg = _safe_exec_error("Cloudflare Terraform apply", e)
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["cloudflare_error"] = error_msg
                cleanup_ledger.append(
                    {
                        "provider": "cloudflare",
                        "resources": [tunnel_name, test_hostname],
                        "state_captured": False,
                    }
                )
                try:
                    cf_state_file = cf_ctr.file("/module/terraform.tfstate")
                    await _before_deadline(cf_state_file.sync(), operation_deadline)
                    cloudflare_state_dir = dagger.dag.directory().with_file(
                        "terraform.tfstate", cf_state_file
                    )
                    cleanup_ledger[-1]["state_captured"] = True
                except Exception:
                    pass
                raise RuntimeError(error_msg) from e

            # Export Cloudflare state for cleanup phase
            try:
                # Now cf_ctr contains the executed container with the state file
                cf_state_file = cf_ctr.file("/module/terraform.tfstate")
                await _before_deadline(cf_state_file.sync(), operation_deadline)
                cloudflare_state_dir = dagger.dag.directory().with_file(
                    "terraform.tfstate", cf_state_file
                )
                cleanup_ledger[-1]["state_captured"] = True
                report_lines.append("  ✓ Cloudflare state exported")
            except Exception:
                report_lines.append("  ⚠ Cloudflare state capture failed")
                cloudflare_state_dir = None

            if cf_exit_code != 0:
                validation_results["cloudflare_tunnel"] = "apply_failed"
                validation_results["cloudflare_dns"] = "apply_failed"
                raise PhaseFailure("Cloudflare apply", cf_exit_code)

            # Phase 3: Create UniFi resources
            report_lines.append("")
            report_lines.append("PHASE 3: Creating UniFi resources...")

            # Note: UniFi will fail if the test MAC address doesn't exist in the
            # UniFi controller. Use --test-mac-address to specify a real device MAC.

            # Create directory with UniFi config for Terraform
            unifi_dir = dagger.dag.directory().with_new_file("unifi.json", unifi_json)

            # Create Terraform container following deploy_unifi() pattern
            unifi_ctr = dagger.dag.container().from_(terraform_image(terraform_version))

            # Mount UniFi config at /workspace
            unifi_ctr = unifi_ctr.with_directory("/workspace", unifi_dir)

            # Mount the UniFi DNS Terraform module
            try:
                tf_module = source.directory("terraform/modules/unifi-dns")
                unifi_ctr = unifi_ctr.with_directory("/module", tf_module)
            except Exception:
                # If module not in source, try project root
                try:
                    tf_module = (
                        dagger.dag.current_module()
                        .source()
                        .directory("terraform/modules/unifi-dns")
                    )
                    unifi_ctr = unifi_ctr.with_directory("/module", tf_module)
                except Exception:
                    raise RuntimeError(
                        "UniFi DNS Terraform module not found at terraform/modules/unifi-dns"
                    )

            # Set environment variables
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
            unifi_ctr = unifi_ctr.with_env_variable(
                "TF_VAR_api_url", api_url if api_url else unifi_url
            )
            unifi_ctr = unifi_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
            unifi_ctr = unifi_ctr.with_env_variable(
                "TF_VAR_unifi_insecure", str(unifi_insecure).lower()
            )

            # Pass authentication credentials as secrets
            unifi_ctr = self._with_unifi_provider_environment(
                unifi_ctr,
                unifi_url,
                api_url,
                unifi_insecure,
                unifi_api_key,
                unifi_username,
                unifi_password,
            )

            # Set working directory to module
            unifi_ctr = unifi_ctr.with_workdir("/module")

            # Execute terraform init
            try:
                unifi_ctr = live_exec(unifi_ctr, ["terraform", "init"])
                init_result = await _before_deadline(unifi_ctr.stdout(), operation_deadline)
                report_lines.append("  ✓ Terraform init completed")
            except dagger.ExecError as e:
                error_msg = _safe_exec_error("UniFi Terraform init", e)
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["unifi_error"] = error_msg
                raise RuntimeError(error_msg) from e

            # Execute terraform apply
            try:
                # Save container reference after execution
                unifi_ctr = live_exec(
                    unifi_ctr, ["terraform", "apply", "-auto-approve"], expect=dagger.ReturnType.ANY
                )
                apply_result = await _before_deadline(unifi_ctr.stdout(), operation_deadline)
                unifi_exit_code = await _before_deadline(unifi_ctr.exit_code(), operation_deadline)
                report_lines.append(f"  ✓ Created UniFi DNS record: {unifi_hostname}")
                validation_results["unifi_dns"] = "created"
                cleanup_ledger.append(
                    {
                        "provider": "unifi",
                        "resources": [unifi_hostname],
                        "state_captured": False,
                    }
                )
            except dagger.ExecError as e:
                error_msg = _safe_exec_error("UniFi Terraform apply", e)
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["unifi_error"] = error_msg
                cleanup_ledger.append(
                    {
                        "provider": "unifi",
                        "resources": [unifi_hostname],
                        "state_captured": False,
                    }
                )
                try:
                    unifi_state_file = unifi_ctr.file("/module/terraform.tfstate")
                    await _before_deadline(unifi_state_file.sync(), operation_deadline)
                    unifi_state_dir = dagger.dag.directory().with_file(
                        "terraform.tfstate", unifi_state_file
                    )
                    cleanup_ledger[-1]["state_captured"] = True
                except Exception:
                    pass
                raise RuntimeError(error_msg) from e

            # Export UniFi state for cleanup phase
            try:
                # Now unifi_ctr contains the executed container with the state file
                unifi_state_file = unifi_ctr.file("/module/terraform.tfstate")
                await _before_deadline(unifi_state_file.sync(), operation_deadline)
                unifi_state_dir = dagger.dag.directory().with_file(
                    "terraform.tfstate", unifi_state_file
                )
                cleanup_ledger[-1]["state_captured"] = True
                report_lines.append("  ✓ UniFi state exported")
            except Exception:
                report_lines.append("  ⚠ UniFi state capture failed")
                unifi_state_dir = None

            if unifi_exit_code != 0:
                validation_results["unifi_dns"] = "apply_failed"
                raise PhaseFailure("UniFi apply", unifi_exit_code)

            # Phase 4: Credential Retrieval via get_tunnel_secrets
            report_lines.append("")
            report_lines.append("PHASE 4: Retrieving tunnel secrets...")

            try:
                # Create a directory with the Cloudflare state for credential retrieval
                cf_state_for_secrets = dagger.dag.directory().with_file(
                    "terraform.tfstate", cf_state_file, permissions=0o600
                )
                # Inspect each artifact inside its runtime; only booleans/counts leave it.
                for format in ("json", "human"):
                    artifact = await _before_deadline(
                        self.get_tunnel_secrets(
                            source=source,
                            cloudflare_token=cloudflare_token,
                            cloudflare_account_id=cloudflare_account_id,
                            zone_name=cloudflare_zone,
                            terraform_version=terraform_version,
                            state_dir=cf_state_for_secrets,
                            output_format=format,
                            protected_disclosure=True,
                        ),
                        operation_deadline,
                    )
                    summary = await _before_deadline(
                        verify_tunnel_artifact(
                            terraform_runtime(dagger.dag, terraform_image(terraform_version)),
                            artifact,
                            format,
                        ),
                        operation_deadline,
                    )
                    report_lines.append(
                        f"  ✓ Verified protected {format} credentials for {summary['count']} tunnel(s)"
                    )
                    validation_results[
                        "secrets_retrieval" if format == "json" else "secrets_human_format"
                    ] = "success"
            except Exception as e:
                error_msg = _safe_exec_error("Secrets retrieval", e)
                report_lines.append(f"  ✗ {error_msg}")
                validation_results["secrets_retrieval"] = f"failed: {error_msg}"

            # Phase 5: Resource Validation
            report_lines.append("")
            report_lines.append("PHASE 5: Validating resources...")

            try:
                tunnel_count, dns_count = await self._cloudflare_resource_counts(
                    cloudflare_account_id,
                    cloudflare_zone,
                    tunnel_name,
                    test_hostname,
                    cloudflare_token,
                    operation_deadline,
                )
                validation_results["cloudflare_tunnel"] = (
                    "validated" if tunnel_count == 1 else "not_found"
                )
                validation_results["cloudflare_dns"] = (
                    "validated" if dns_count == 1 else "not_found"
                )
            except Exception as e:
                report_lines.append(f"  ✗ {_safe_exec_error('Cloudflare verification', e)}")
                validation_results["cloudflare_tunnel"] = "error"
                validation_results["cloudflare_dns"] = "error"

            # UniFi validation uses the provider's DNS data source, which queries the
            # controller rather than treating apply success as proof of existence.
            try:
                unifi_exists = await self._unifi_dns_exists(
                    unifi_hostname,
                    "default",
                    unifi_url,
                    api_url,
                    unifi_insecure,
                    unifi_api_key,
                    unifi_username,
                    unifi_password,
                    terraform_version,
                    operation_deadline,
                )
                if unifi_exists:
                    report_lines.append(f"  ✓ UniFi DNS validated: {unifi_hostname}")
                    validation_results["unifi_validation"] = "validated"
                else:
                    report_lines.append(f"  ✗ UniFi DNS not found: {unifi_hostname}")
                    validation_results["unifi_validation"] = "not_found"
            except Exception as e:
                report_lines.append(f"  ✗ {_safe_exec_error('UniFi DNS validation', e)}")
                validation_results["unifi_validation"] = "error"

            # Optional connectivity check (future enhancement)
            if validate_connectivity:
                report_lines.append(
                    "  ○ HTTP connectivity check skipped (would test actual connectivity)"
                )
                validation_results["connectivity"] = "skipped"

            # Validation summary based on actual API responses
            cf_success = (
                validation_results.get("cloudflare_tunnel") == "validated"
                and validation_results.get("cloudflare_dns") == "validated"
            )
            unifi_success = validation_results.get("unifi_validation") == "validated"

            report_lines.append("")
            report_lines.append("-" * 60)
            if cf_success and unifi_success:
                report_lines.append("VALIDATION SUMMARY: ✓ ALL RESOURCES VALIDATED")
            else:
                report_lines.append("VALIDATION SUMMARY: ✗ SOME RESOURCES NOT FOUND")
            report_lines.append("-" * 60)

            # Phase 5.5: Wait before cleanup (if enabled)
            if wait_before_cleanup > 0:
                report_lines.append("")
                report_lines.append(f"PHASE 5.5: Waiting {wait_before_cleanup}s before cleanup...")
                report_lines.append("  (Use this time to manually verify created resources)")
                await _before_deadline(asyncio.sleep(wait_before_cleanup), operation_deadline)
                report_lines.append(f"  ✓ Wait completed ({wait_before_cleanup}s)")

        except asyncio.CancelledError:
            effect_unknown = True
            raise
        except Exception as e:
            if isinstance(e, TimeoutError):
                effect_unknown = True
                primary_failure = (
                    f"integration {test_id} outcome unknown after deadline; reconcile process "
                    "termination, resources and state before cleanup or retry; no rollback established"
                )
            else:
                primary_failure = _safe_exec_error("Integration operation", e)
            report_lines.append("")
            report_lines.append(f"✗ ERROR DURING TEST: {primary_failure}")
            validation_results["error"] = "timeout" if isinstance(e, TimeoutError) else "failed"

        finally:
            cleanup_deadline = time.monotonic() + cleanup_reserve
            # Phase 6: Guaranteed Cleanup
            if cleanup and not effect_unknown:
                report_lines.append("")
                report_lines.append(
                    "PHASE 5: Cleanup (attempt and verify; unknown effects hold)..."
                )

                # UniFi was created after Cloudflare, so destroy its recorded state
                # first. The later UniFi cleanup block remains as a state-less safety
                # pass, while this pass guarantees reverse creation order.
                if any(entry["provider"] == "unifi" for entry in cleanup_ledger):
                    report_lines.append("  Cleaning up UniFi resources (reverse order)...")
                    try:
                        unifi_first_ctr = dagger.dag.container().from_(
                            terraform_image(terraform_version)
                        )
                        unifi_first_ctr = unifi_first_ctr.with_directory("/workspace", unifi_dir)
                        try:
                            tf_module = source.directory("terraform/modules/unifi-dns")
                        except Exception:
                            tf_module = (
                                dagger.dag.current_module()
                                .source()
                                .directory("terraform/modules/unifi-dns")
                            )
                        unifi_first_ctr = unifi_first_ctr.with_directory("/module", tf_module)
                        if unifi_state_dir is None:
                            raise RuntimeError("UniFi state unavailable for reverse cleanup")
                        unifi_first_ctr = unifi_first_ctr.with_file(
                            "/module/terraform.tfstate",
                            unifi_state_dir.file("terraform.tfstate"),
                        )
                        unifi_first_ctr = unifi_first_ctr.with_env_variable(
                            "TF_VAR_unifi_url", unifi_url
                        )
                        unifi_first_ctr = unifi_first_ctr.with_env_variable(
                            "TF_VAR_api_url", api_url if api_url else unifi_url
                        )
                        unifi_first_ctr = unifi_first_ctr.with_env_variable(
                            "TF_VAR_config_file", "/workspace/unifi.json"
                        )
                        unifi_first_ctr = unifi_first_ctr.with_env_variable(
                            "TF_VAR_unifi_insecure", str(unifi_insecure).lower()
                        )
                        unifi_first_ctr = self._with_unifi_provider_environment(
                            unifi_first_ctr,
                            unifi_url,
                            api_url,
                            unifi_insecure,
                            unifi_api_key,
                            unifi_username,
                            unifi_password,
                        ).with_workdir("/module")
                        unifi_first_ctr = live_exec(
                            unifi_first_ctr, ["terraform", "init", "-input=false"]
                        )
                        await _before_deadline(unifi_first_ctr.stdout(), cleanup_deadline)
                        unifi_first_ctr = live_exec(
                            unifi_first_ctr,
                            [
                                "terraform",
                                "destroy",
                                "-auto-approve",
                                "-refresh=false",
                                "-input=false",
                            ],
                        )
                        await _before_deadline(unifi_first_ctr.stdout(), cleanup_deadline)
                        cleanup_status["unifi"] = "success"
                        unifi_state_dir = None
                        report_lines.append(f"    ✓ Deleted UniFi DNS record: {unifi_hostname}")
                    except Exception as error:
                        cleanup_status["unifi"] = "failed"
                        report_lines.append(
                            f"    ✗ {_safe_exec_error('UniFi reverse-order cleanup', error)}"
                        )

                # Cleanup Cloudflare resources after the later-created UniFi record.
                # NOTE: Implements retry logic for Cloudflare provider issue #5255
                # where tunnel deletion fails on first attempt due to "active connections"
                report_lines.append("  Cleaning up Cloudflare resources...")
                last_error = None
                cf_cleanup_success = False

                try:
                    # Create Cloudflare cleanup container
                    cf_cleanup_ctr = dagger.dag.container().from_(
                        terraform_image(terraform_version)
                    )

                    # Mount Cloudflare config at /workspace
                    cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/workspace", cloudflare_dir)

                    # Mount the Cloudflare Tunnel Terraform module
                    try:
                        tf_module = source.directory("terraform/modules/cloudflare-tunnel")
                        cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
                    except Exception:
                        # If module not in source, try project root
                        try:
                            tf_module = (
                                dagger.dag.current_module()
                                .source()
                                .directory("terraform/modules/cloudflare-tunnel")
                            )
                            cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
                        except Exception:
                            raise RuntimeError(
                                "Cloudflare Tunnel Terraform module not found at terraform/modules/cloudflare-tunnel"
                            )

                    # Mount preserved state file if available
                    if cloudflare_state_dir:
                        try:
                            # Extract state file from directory and mount it without overwriting module files
                            cf_state_file = cloudflare_state_dir.file("terraform.tfstate")
                            cf_cleanup_ctr = cf_cleanup_ctr.with_file(
                                "/module/terraform.tfstate", cf_state_file
                            )
                            report_lines.append(
                                "    ✓ Cloudflare state file mounted for state-based destroy"
                            )
                        except Exception as e:
                            report_lines.append(
                                f"    ⚠ {_safe_exec_error('Cloudflare cleanup state mounting', e)}"
                            )
                            cloudflare_state_dir = None
                    else:
                        raise RuntimeError("Cloudflare state unavailable; reconcile before cleanup")
                    if cloudflare_state_dir is None:
                        raise RuntimeError(
                            "Cloudflare state custody failed; reconcile before cleanup"
                        )

                    # Set environment variables with overrides for CLI parameters
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable(
                        "TF_VAR_account_id_override", cloudflare_account_id
                    )
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable(
                        "TF_VAR_zone_name_override", cloudflare_zone
                    )
                    cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable(
                        "TF_VAR_config_file", "/workspace/cloudflare.json"
                    )

                    # Pass Cloudflare token as secret - use CLOUDFLARE_API_TOKEN env var
                    cf_cleanup_ctr = cf_cleanup_ctr.with_secret_variable(
                        "CLOUDFLARE_API_TOKEN", cloudflare_token
                    )

                    # Set working directory to module
                    cf_cleanup_ctr = cf_cleanup_ctr.with_workdir("/module")

                    # Execute terraform init (no retry for init failures - fail fast)
                    try:
                        cf_cleanup_ctr = live_exec(cf_cleanup_ctr, ["terraform", "init"])
                        await _before_deadline(
                            cf_cleanup_ctr.stdout(),
                            cleanup_deadline,
                        )
                    except dagger.ExecError as e:
                        raise RuntimeError(_safe_exec_error("Cloudflare cleanup init", e)) from None

                    # Never replay a failed/uncertain effect from an older snapshot.
                    cf_cleanup_ctr = live_exec(
                        cf_cleanup_ctr,
                        ["terraform", "destroy", "-auto-approve", "-refresh=false"],
                    )
                    await _before_deadline(cf_cleanup_ctr.stdout(), cleanup_deadline)
                    cleanup_status["cloudflare"] = "success"
                    cf_cleanup_success = True

                except Exception as e:
                    cleanup_status["cloudflare"] = "failed"
                    report_lines.append(f"    ✗ {_safe_exec_error('Cloudflare cleanup', e)}")

                if not any(entry["provider"] == "unifi" for entry in cleanup_ledger):
                    cleanup_status["unifi"] = "success_not_created"

                # Cleanup local state files (state is container-local, so just document)
                report_lines.append("  Cleaning up local state files...")
                report_lines.append(
                    "    Terraform state is container-local; no host write-through or durable custody implied"
                )
                cleanup_status["state_files"] = "success"

                report_lines.append("  Verifying externally visible resources are absent...")
                try:
                    tunnel_count, dns_count = await self._cloudflare_resource_counts(
                        cloudflare_account_id,
                        cloudflare_zone,
                        tunnel_name,
                        test_hostname,
                        cloudflare_token,
                        cleanup_deadline,
                    )
                    if tunnel_count or dns_count:
                        cleanup_status["cloudflare"] = "residual_resources"
                        report_lines.append(
                            f"    ✗ Cloudflare residuals: tunnel={tunnel_name}, dns={test_hostname}"
                        )
                    else:
                        report_lines.append("    ✓ Cloudflare test resources are absent")
                except Exception as error:
                    cleanup_status["cloudflare"] = "residual_check_failed"
                    report_lines.append(
                        f"    ✗ {_safe_exec_error('Cloudflare residual check', error)}"
                    )

                try:
                    unifi_exists = await self._unifi_dns_exists(
                        unifi_hostname,
                        "default",
                        unifi_url,
                        api_url,
                        unifi_insecure,
                        unifi_api_key,
                        unifi_username,
                        unifi_password,
                        terraform_version,
                        cleanup_deadline,
                    )
                    if unifi_exists:
                        cleanup_status["unifi"] = "residual_resources"
                        report_lines.append(f"    ✗ UniFi residual DNS record: {unifi_hostname}")
                    else:
                        report_lines.append("    ✓ UniFi test DNS record is absent")
                except Exception as error:
                    cleanup_status["unifi"] = "residual_check_failed"
                    report_lines.append(f"    ✗ {_safe_exec_error('UniFi residual check', error)}")

                # Cleanup summary with warnings
                report_lines.append("")
                report_lines.append("-" * 60)
                report_lines.append("CLEANUP SUMMARY")
                report_lines.append("-" * 60)
                report_lines.append(f"  Cloudflare: {cleanup_status['cloudflare']}")
                report_lines.append(f"  UniFi: {cleanup_status['unifi']}")
                report_lines.append(f"  State Files: {cleanup_status['state_files']}")

                # Display warning if any cleanup step failed
                if not all(str(status).startswith("success") for status in cleanup_status.values()):
                    report_lines.append("")
                    report_lines.append("⚠ WARNING: Some cleanup steps failed!")
                    report_lines.append("  Manual cleanup may be required:")
                    if cleanup_status["cloudflare"] != "success":
                        report_lines.append(
                            f"    - Check Cloudflare dashboard for remaining resources: {tunnel_name}, {test_hostname}"
                        )
                    if cleanup_status["unifi"] != "success":
                        report_lines.append(
                            f"    - Check UniFi controller for remaining DNS record: {unifi_hostname}"
                        )
            else:
                report_lines.append("")
                report_lines.append("PHASE 5: Cleanup SKIPPED (cleanup=false)")
                report_lines.append("  WARNING: Resources may still exist!")
                cleanup_status = {
                    "cloudflare": (
                        "unknown_reconcile_before_cleanup" if effect_unknown else "skipped"
                    ),
                    "unifi": "unknown_reconcile_before_cleanup" if effect_unknown else "skipped",
                    "state_files": "unknown_custody" if effect_unknown else "skipped",
                }

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

        failure_reasons = _integration_failure_reasons(
            primary_failure,
            validation_results,
            cleanup_ledger,
            cleanup_status,
        )

        if failure_reasons:
            raise RuntimeError(
                f"Integration test {test_id} failed after cleanup: " + "; ".join(failure_reasons)
            )

        return "\n".join(report_lines)

    async def _detect_deployment_module(
        self,
        tf_ctr: dagger.Container,
        cache_buster: str = "",
    ) -> tuple[str, list[str]]:
        """
        Detect which Terraform module created the state by inspecting available outputs.

        This helper function queries `terraform output -json` to determine whether
        the state was created by the cloudflare-tunnel module (unprefixed outputs)
        or the glue module (prefixed outputs with 'cloudflare_' prefix).

        Args:
            tf_ctr: Initialized Terraform container with module mounted
            cache_buster: Optional cache buster for cache control

        Returns:
            Tuple of (module_type, available_outputs) where:
            - module_type is either "cloudflare-tunnel" or "glue"
            - available_outputs is a list of output names found in state
        """
        validate_run_label(cache_buster)
        try:
            # Return only names, never all credential-bearing values for detection.
            tf_ctr = live_exec(
                tf_ctr,
                ["terraform", "output", "-json"],
                redirect_stdout="/root/terraform-outputs.json",
            )
            tf_ctr = live_exec(
                tf_ctr,
                [
                    "python",
                    "-c",
                    "import json; value=json.load(open('/root/terraform-outputs.json')); "
                    "assert isinstance(value,dict); print(json.dumps(sorted(value)))",
                ],
            )
            available_outputs = json.loads(await tf_ctr.stdout())
            if not isinstance(available_outputs, list) or not all(
                isinstance(key, str) for key in available_outputs
            ):
                raise ValueError("Invalid state output identity response")

            # Detect module type based on output naming pattern
            # Glue module uses 'cloudflare_' prefix on outputs
            if {
                "cloudflare_tunnel_ids",
                "cloudflare_tunnel_tokens",
                "cloudflare_credentials_json",
            }.issubset(available_outputs):
                return "glue", available_outputs
            elif {"tunnel_ids", "tunnel_tokens", "credentials_json"}.issubset(available_outputs):
                return "cloudflare-tunnel", available_outputs
            else:
                raise ValueError("State output identity does not match a supported root")

        except Exception as error:
            raise RuntimeError(_safe_exec_error("State root detection", error)) from None

    @function(cache="never")  # type: ignore[call-overload]
    async def get_tunnel_secrets(
        self,
        source: Annotated[
            dagger.Directory, Doc("Source directory (for accessing terraform modules)")
        ],
        cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token for authentication")],
        cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
        zone_name: Annotated[str, Doc("DNS zone name (e.g., example.com)")],
        terraform_version: Annotated[
            str, Doc("Reviewed immutable Terraform release")
        ] = DEFAULT_TERRAFORM_VERSION,
        backend_type: Annotated[
            str, Doc("Terraform backend type (local, s3, azurerm, gcs, remote, etc.)")
        ] = "local",
        backend_config_file: Annotated[
            Optional[Secret],
            Doc("Secret backend configuration (required for remote backends)"),
        ] = None,
        backend_config_format: Annotated[str, Doc("Explicit backend syntax: yaml or hcl")] = "",
        state_dir: Annotated[
            Optional[dagger.Directory],
            Doc("Protected existing state input only; no host write-back; excludes remote backend"),
        ] = None,
        output_format: Annotated[
            str, Doc("Protected artifact material: json, human, or shell")
        ] = "json",
        protected_disclosure: Annotated[
            bool, Doc("Acknowledge credential disclosure into protected caller storage/output")
        ] = False,
        cache_buster: Annotated[
            str, Doc("Optional non-secret run label, at most 80 letters/digits/._-; not freshness")
        ] = "",
    ) -> dagger.Directory:
        """
        Return an explicitly acknowledged protected credential Directory, never raw stdout.

        Every artifact includes credentials.json; human additionally includes
        credentials.txt and shell includes tunnel-secrets.sh. All files are mode
        0600. Create an owner-only destination before authorized export; do not
        select File.contents(), log, or publish this artifact. Acknowledgment is
        not encryption and does not authorize disclosure to another party.

        Use the same remote backend Secret and explicit yaml/hcl format as the
        deployment, or an explicit protected existing local state_dir snapshot.
        The standalone and glue roots both expose the selected output aliases.
        No ephemeral invocation recovery or host state write-through is implied.
        Source/account/zone arguments are retained for existing caller identity;
        the selected state, not source files, supplies credential values.
        """
        if protected_disclosure is not True:
            raise ValueError(
                "Tunnel credentials require explicit protected-disclosure acknowledgement"
            )
        validate_run_label(cache_buster)
        if output_format not in {"json", "human", "shell"}:
            raise ValueError("Protected credential format must be json, human, or shell")
        is_valid, error_msg = self._validate_backend_config(backend_type, backend_config_file)
        if not is_valid:
            raise ValueError(error_msg)
        is_valid, error_msg = self._validate_state_storage_config(backend_type, state_dir)
        if not is_valid:
            raise ValueError(error_msg)
        if backend_type == "local" and state_dir is None:
            raise ValueError(
                "Credential retrieval requires an explicit protected existing local state snapshot"
            )
        if backend_type != "local" and backend_config_format not in {"yaml", "hcl"}:
            raise ValueError("backend-config-format must explicitly select yaml or hcl")
        operation_id = str(uuid4())
        try:
            tf_ctr = terraform_runtime(dagger.dag, terraform_image(terraform_version))
            tf_ctr = tf_ctr.with_env_variable("OPERATION_ID", operation_id)
            tf_ctr = tf_ctr.with_workdir("/workspace")
            if backend_type != "local":
                tf_ctr = tf_ctr.with_new_file(
                    "/workspace/backend.tf", self._generate_backend_block(backend_type)
                )
                if backend_config_file is not None:
                    tf_ctr = await _with_backend_secret(
                        tf_ctr, backend_config_file, backend_config_format
                    )
                tf_ctr = live_exec(
                    tf_ctr,
                    ["terraform", "init", "-input=false", f"-backend-config={BACKEND_SECRET_PATH}"],
                )
                await tf_ctr.sync()
            else:
                if state_dir is not None:
                    tf_ctr = tf_ctr.with_file(
                        "/workspace/terraform.tfstate",
                        state_dir.file("terraform.tfstate"),
                        permissions=0o600,
                    )
            return await protected_tunnel_artifact(tf_ctr, output_format)
        except Exception as e:
            raise RuntimeError(
                _safe_exec_error("Tunnel secret retrieval", e, operation_id)
            ) from None

    @function(cache="never")  # type: ignore[call-overload]
    async def test_cloudflare_dns_canary(
        self,
        cloudflare_api_token: Secret,
        wasabi_access_key: Secret,
        wasabi_secret_key: Secret,
        bucket: str,
        revision: str,
        run_id: str,
        attempt: str,
        repository: str,
        ref: str,
        event_name: str,
        acceptance_sha: str = "",
        acceptance_branch: str = "",
        policy_reviewed: str = "false",
        operation: str = "normal",
    ) -> str:
        """Qualify the sandbox, then create/update/verify/destroy two DNS records.

        Runtime Secrets never become Python application strings. Unknown effects
        retain the durable claim for separately authorized reconciliation.
        """
        try:
            from .canary_entrypoint import config_for, invoke
        except ImportError:
            from canary_entrypoint import (  # type: ignore[no-redef,import-not-found]
                config_for,
                invoke,
            )
        config = config_for(
            operation=operation,
            bucket=bucket,
            revision=revision,
            run_id=run_id,
            attempt=attempt,
            repository=repository,
            ref=ref,
            event_name=event_name,
            acceptance_sha=acceptance_sha,
            acceptance_branch=acceptance_branch,
            policy_reviewed=policy_reviewed,
        )
        return await invoke(config, cloudflare_api_token, wasabi_access_key, wasabi_secret_key)

    @function(cache="never")  # type: ignore[call-overload]
    async def inspect_cloudflare_dns_canary(
        self,
        run_prefix: str,
        cloudflare_api_token: Secret,
        wasabi_access_key: Secret,
        wasabi_secret_key: Secret,
    ) -> str:
        """Read-only projected metadata for one retained run; never cleanup or takeover."""
        try:
            from .canary_entrypoint import observe
        except ImportError:
            from canary_entrypoint import observe  # type: ignore[no-redef,import-not-found]
        return await observe(run_prefix, cloudflare_api_token, wasabi_access_key, wasabi_secret_key)

    @function(cache="never")  # type: ignore[call-overload]
    async def reconcile_cloudflare_dns_canary(
        self,
        run_prefix: str,
        expected_claim_version_id: str,
        expected_state_version_id: str,
        cloudflare_api_token: Secret,
        wasabi_access_key: Secret,
        wasabi_secret_key: Secret,
        prior_writer_terminated: bool = False,
        exclusive_writer: bool = False,
    ) -> str:
        """Explicitly reconcile/destroy one terminated run; never replay or age-takeover."""
        try:
            from .canary_entrypoint import reconcile
        except ImportError:
            from canary_entrypoint import reconcile  # type: ignore[no-redef,import-not-found]
        config = {
            "run_prefix": run_prefix,
            "expected_claim_version_id": expected_claim_version_id,
            "expected_state_version_id": expected_state_version_id,
            "prior_writer_terminated": prior_writer_terminated,
            "exclusive_writer": exclusive_writer,
        }
        return await reconcile(config, cloudflare_api_token, wasabi_access_key, wasabi_secret_key)

    @function(cache="never")  # type: ignore[call-overload]
    async def inventory_cloudflare_dns_canaries(
        self,
        cloudflare_api_token: Secret,
        wasabi_access_key: Secret,
        wasabi_secret_key: Secret,
    ) -> str:
        """Report-only exact namespace inventory; no ownership transfer or deletion."""
        try:
            from .canary_entrypoint import reporting
        except ImportError:
            from canary_entrypoint import reporting  # type: ignore[no-redef,import-not-found]
        return await reporting(
            {"operation": "janitor"}, cloudflare_api_token, wasabi_access_key, wasabi_secret_key
        )

    @function(cache="never")  # type: ignore[call-overload]
    async def measure_cloudflare_canary_phases(
        self,
        run_prefix: str,
        revision: str,
        cloudflare_api_token: Secret,
        wasabi_access_key: Secret,
        wasabi_secret_key: Secret,
    ) -> str:
        """Read protected ledger intervals, never raw state or isolated DNS latency."""
        try:
            from .canary_entrypoint import reporting
        except ImportError:
            from canary_entrypoint import reporting  # type: ignore[no-redef,import-not-found]
        return await reporting(
            {"operation": "metrics", "run_prefix": run_prefix, "revision": revision},
            cloudflare_api_token,
            wasabi_access_key,
            wasabi_secret_key,
        )
