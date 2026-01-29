# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

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
