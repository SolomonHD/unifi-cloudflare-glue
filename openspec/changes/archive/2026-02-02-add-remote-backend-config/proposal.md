# Change: Add Remote Backend Configuration Support

## Why

The Dagger deployment functions currently use ephemeral local Terraform state that is lost when containers exit. While this works well for testing and CI/CD, it doesn't support production workflows requiring persistent state management via remote backends (S3, Azure Blob, GCS, Terraform Cloud, etc.). Users who need persistent state must bypass Dagger functions and lose the benefits of containerized, reproducible deployments.

## What Changes

- Add `backend_type` parameter to [`deploy_unifi`](../../../src/main/main.py:143), [`deploy_cloudflare`](../../../src/main/main.py:263), [`deploy`](../../../src/main/main.py:342), and [`destroy`](../../../src/main/main.py:486) functions
- Add `backend_config_file` parameter (File type) for mounting HCL backend configuration
- Implement validation ensuring `backend_config_file` required when `backend_type != "local"`
- Dynamically generate Terraform `backend.tf` file with empty backend block when using remote backends
- Use `terraform init -backend-config=FILE` pattern for configuration injection
- Add documentation in [`README.md`](../../../README.md) with examples for S3, Azure, GCS, and Terraform Cloud
- Create example backend configuration files in `examples/backend-configs/`
- Update [`CHANGELOG.md`](../../../CHANGELOG.md) with new feature

**Default behavior unchanged:** `backend_type="local"` maintains current ephemeral state behavior for backward compatibility.

## Impact

- **Affected specs:** `dagger-module`
- **Affected code:**
  - [`src/main/main.py`](../../../src/main/main.py): Add parameters and implementation to 4 deployment functions
  - [`README.md`](../../../README.md): Add "State Management" section with backend configuration examples
  - [`CHANGELOG.md`](../../../CHANGELOG.md): Document new feature under "Added" section
  - `examples/backend-configs/` (new): Example HCL files for common backends

**Files modified:** 3 existing + 1 new directory with examples
**Functions modified:** 4 (deploy_unifi, deploy_cloudflare, deploy, destroy)
**Breaking changes:** None (backward compatible, opt-in feature)
