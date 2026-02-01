# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

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
