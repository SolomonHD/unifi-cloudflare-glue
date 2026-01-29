# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed

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
