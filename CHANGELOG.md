# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- **Improved KCL Error Handling in Configuration Generation:**
  - Refactored `generate_unifi_config()` and `generate_cloudflare_config()` to separate KCL execution from yq conversion
  - KCL execution now runs as a separate step with detailed error capture (stdout, stderr, exit code)
  - Added empty output validation to detect when KCL produces no output (empty generator file, no output statements, etc.)
  - yq conversion runs separately on a temporary file, preserving KCL output for debugging
  - When yq conversion fails, the actual KCL output is displayed (truncated to 1000 characters if large)
  - All error messages include actionable hints for local debugging (e.g., `kcl run generators/unifi.k`)
  - Container references are properly preserved after each operation step
  - Leverages existing `KCLGenerationError` exception class for consistent error handling
  - No breaking changes - function signatures and return types remain identical

### Fixed

- **Fixed yq YAML-to-JSON parsing bug in KCL generator files:**
  - Modified `generators/unifi.k` and `generators/cloudflare.k` to output single YAML document
  - Removed dual-document output (sample_config + result) that caused yq parsing failures
  - Changed internal `sample_config` to `_sample_config` (private) and output only `result`
  - Generators now produce single-document YAML compatible with `yq eval -o=json '.'`
  - Dagger functions `generate-unifi-config` and `generate-cloudflare-config` work correctly
  - Resolves "mapping values are not allowed in this context" YAML parsing error

- **Fixed yq YAML-to-JSON parsing bug in KCL configuration generation:**
  - Fixed `generate_unifi_config` function (line 142) and `generate_cloudflare_config` function (line 1678)
  - Changed yq command from `yq -o=json '.result'` to `yq eval -o=json '.'`
  - Resolves "mapping values are not allowed in this context" YAML parsing error
  - Both functions now successfully convert KCL YAML output to valid JSON
  - Generated JSON files are properly formatted and usable by Terraform modules

### Added

- **Architecture Diagrams:**
  - Created `docs/architecture.md` with comprehensive Mermaid diagrams
  - Five core diagrams illustrating system design:
    - System Architecture: Component layers (Configuration, Orchestration, Infrastructure, Network)
    - Data Flow: Configuration transformation pipeline from KCL to deployed infrastructure
    - Deployment Workflow: Sequence diagram showing interaction between User, Dagger, Terraform, UniFi, and Cloudflare
    - State Management Decision Tree: Visual guide for choosing ephemeral, local persistent, or remote backend state
    - DNS Resolution: Local vs external access paths with UniFi DNS and Cloudflare Tunnel
  - Embedded state management diagram in `docs/state-management.md`
  - Added architecture entry to `docs/README.md` index
  - Added architecture link to main `README.md` Documentation section
  - All diagrams use GitHub-native Mermaid format for version control and automatic rendering

- **Documentation Restructuring:**
  - Created `docs/` directory with specialized documentation files organized by topic
  - New documentation files:
    - `docs/getting-started.md` - Installation and first deployment guide
    - `docs/dagger-reference.md` - Complete Dagger function reference and CI/CD integration
    - `docs/terraform-modules.md` - Standalone Terraform module usage patterns
    - `docs/state-management.md` - State backend options (ephemeral, local, remote)
    - `docs/security.md` - Security best practices and credential handling
    - `docs/backend-configuration.md` - Placeholder for detailed backend guide (to be populated)
    - `docs/troubleshooting.md` - Placeholder for troubleshooting guide (to be populated)
    - `docs/README.md` - Documentation index with navigation
  - Rewrote `README.md` as a condensed entry point (~200 lines) with clear navigation to detailed docs
  - Backed up original `README.md` as `README.old.md` for reference
  - Updated `.gitignore` to include `terraform-state/` directory
  - All original content preserved with improved organization and cross-linking

- **Terraform Plan Function:**
  - Added `plan()` function for generating Terraform plans without applying changes
  - Supports plan → review → apply workflows for infrastructure changes
  - Generates three output formats per module:
    - Binary plan files (`*.tfplan`) - usable with `terraform apply`
    - JSON format (`*.json`) - for automation and policy-as-code tools
    - Human-readable text (`*.txt`) - for manual review
  - Creates `plan-summary.txt` with aggregated resource counts across both modules
  - Returns `dagger.Directory` containing all plan artifacts
  - Supports all existing state management options (ephemeral, persistent local, remote backends)
  - Includes cache control options (`--no-cache`, `--cache-buster`)
  - Usage:
    ```bash
    dagger call plan \
        --kcl-source=./kcl \
        --unifi-url=https://unifi.local:8443 \
        --cloudflare-token=env:CF_TOKEN \
        --cloudflare-account-id=xxx \
        --zone-name=example.com \
        --unifi-api-key=env:UNIFI_API_KEY \
        export --path=./plans
    ```

- **Persistent Local State Directory Support:**
  - Added `state_dir` parameter to `deploy`, `deploy-unifi`, `deploy-cloudflare`, and `destroy` functions
  - Enables persistent Terraform state storage on local filesystem without remote backend setup
  - Mounts user-provided directory at `/state` in the container
  - Copies Terraform module files to state directory for co-location with state
  - Sets working directory to `/state` when using persistent local state
  - Mutual exclusion with remote backend configuration (`--state-dir` and `--backend-type` cannot be used together)
  - Clear error messages when conflicting state storage options are provided
  - Perfect for solo development workflows - state persists between runs
  - Usage:
    ```bash
    dagger call deploy \
        --state-dir=./terraform-state \
        --kcl-source=./kcl \
        --unifi-url=https://unifi.local:8443 \
        ... other parameters ...
    ```

- **Remote Backend Configuration Support:**
  - Added `backend_type` parameter to `deploy`, `deploy-unifi`, `deploy-cloudflare`, and `destroy` functions
  - Added `backend_config_file` parameter for mounting HCL backend configuration files
  - Supports all Terraform backends: S3, Azure Blob Storage, GCS, Terraform Cloud, and more
  - Automatic backend validation with clear error messages
  - Dynamic `backend.tf` generation for remote backends
  - Example configuration files in `examples/backend-configs/` for common backends
  - Full backward compatibility - default behavior (local ephemeral state) unchanged
  - Usage:
    ```bash
    dagger call deploy \
        --backend-type=s3 \
        --backend-config-file=./s3-backend.hcl \
        ... other parameters ...
    ```

- **`--no-cache` Flag for Integration Tests:**
  - Added `no_cache` parameter to `test_integration` function
  - Automatically generates epoch timestamp (`int(time.time())`) when enabled
  - Provides user-friendly alternative to `--cache-buster=$(date +%s)`
  - Mutually exclusive with `--cache-buster` parameter (cannot use both)
  - Maintains backward compatibility with existing `--cache-buster` usage
  - Usage: `dagger call test-integration --no-cache ...`

- **Cloudflare Cleanup Retry Logic:**
  - Implements automatic retry for Cloudflare `terraform destroy` operations
  - Addresses Cloudflare provider issue #5255 where tunnel deletion fails on first attempt
  - Maximum 2 attempts with 5-second delay between attempts
  - New cleanup statuses: `success`, `success_after_retry`, `failed_needs_manual_cleanup`
  - Detailed manual cleanup instructions when retry fails
  - Displays tunnel name and DNS record name in failure messages
  - Includes step-by-step Cloudflare dashboard navigation instructions

### Added

- **Integration Test MAC Address Parameter:**
  - Added `test_mac_address` parameter to `test_integration` function
  - Allows specifying a real MAC address from your UniFi controller
  - Fixes `api.err.UnknownUser` error when using the default fake MAC (`aa:bb:cc:dd:ee:ff`)
  - Updated `_generate_test_configs` to accept custom MAC address
  - Test report now displays the MAC address being used
  - Example usage: `--test-mac-address=de:ad:be:ef:12:34`

- **UniFi TLS Insecure Mode Support:**
  - Added `unifi_insecure` parameter to all UniFi-related functions
  - Allows skipping TLS certificate verification for UniFi controllers with self-signed certificates
  - Updated functions: `deploy-unifi`, `deploy`, `destroy`, `test-integration`
  - Terraform module updated with `unifi_insecure` variable
  - Fixes error: `tls: failed to verify certificate: x509: certificate is valid for 127.0.0.1, not 192.168.10.1`
  - Usage: Add `--unifi-insecure` flag when calling functions

### Changed

- **Cloudflare Provider v5 Migration - DNS Record Resource:**
  - Migrated `cloudflare_record` resource to `cloudflare_dns_record`
  - Updated attribute: `value` → `content` (for CNAME records)
  - Added required `ttl = 1` attribute (automatic TTL)
  - Updated all output references from `cloudflare_record.tunnel` to `cloudflare_dns_record.tunnel`
  - Files modified: `terraform/modules/cloudflare-tunnel/main.tf`, `outputs.tf`, `README.md`
  - **State migration required:** Use `terraform state mv cloudflare_record.tunnel cloudflare_dns_record.tunnel` when applying to existing infrastructure

- **Cloudflare Provider v5 Migration - Tunnel Resource:**
  - Migrated `cloudflare_tunnel` resource to `cloudflare_zero_trust_tunnel_cloudflared`
  - Updated attribute: `secret` → `tunnel_secret` (base64-encoded tunnel secret)
  - Updated all references in `cloudflare_tunnel_config` and `cloudflare_dns_record` resources
  - Updated all output values to reference new resource type
  - Files modified: `terraform/modules/cloudflare-tunnel/main.tf`, `outputs.tf`
  - **State migration required:** Use `terraform state mv` commands when applying to existing infrastructure

- **Dagger Engine Upgrade:**
  - Updated `engineVersion` in `dagger.json` from `v0.19.7` to `v0.19.8`
  - Incorporates latest bug fixes and performance improvements
  - Maintains full backward compatibility with existing functions

### Added

- **Container version control parameters:**
  - Added `terraform_version` parameter to `deploy_unifi`, `deploy_cloudflare`, `deploy`, `destroy`, and `test_integration` functions
  - Added `kcl_version` parameter to `deploy`, `destroy`, and `test_integration` functions (was already present in config generators)
  - All version parameters default to `"latest"` for backward compatibility
  - Allows pinning to specific versions for reproducibility and compliance (e.g., `--terraform-version=1.10.0`)

- **`test_integration` function enhancements:**
  - Added `cache_buster` parameter (string, default: `""`) to force Dagger cache invalidation and trigger fresh test execution
  - Added `wait_before_cleanup` parameter (integer, default: `0`) to pause between resource validation and cleanup for manual verification
  - Cache buster value is injected as `CACHE_BUSTER` environment variable in test containers
  - Wait duration is reported in test output when enabled

## [0.1.0] - 2026-01-29

### Added

- Initial release of unifi-cloudflare-glue
- KCL schemas for UniFi and Cloudflare configuration
- Dagger module with containerized KCL generation
- Terraform modules for UniFi DNS and Cloudflare Tunnel management
- Integration testing framework with `test_integration` function
- Example homelab-media-stack configuration
