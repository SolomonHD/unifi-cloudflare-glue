## Why

The `unifi-cloudflare-glue` Dagger module has inconsistent backend config file paths in `src/main/main.py`. When using remote Terraform backends (S3, etc.) from a consumer repository, Terraform init fails with "Failed to read file" errors because the backend config file is mounted at `/root/.terraform/backend.hcl` but referenced at `/root/.terraform/backend.tfbackend` in the init command.

## What Changes

- **Fix path mismatch in `plan()` function (line 1106)**: Change mount path from `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- **Fix path mismatch in `plan()` function (line 1201)**: Change mount path from `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- **Fix path mismatch in `get_tunnel_secrets()` function (line 2821)**: Change mount path from `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`

All three changes ensure backend config files are mounted and referenced at consistent paths using the `.tfbackend` extension.

## Capabilities

### New Capabilities
<!-- This is a bug fix with no new capabilities -->

### Modified Capabilities
- `backend-config-path-consistency`: Fix file path mismatches to ensure remote backend configurations work correctly from consumer repositories. The module already supports remote backends; this fix corrects implementation details to match the documented behavior.

## Impact

- **Affected Functions**: `plan()`, `get_tunnel_secrets()`
- **Functions Already Working**: `deploy_unifi()`, `deploy_cloudflare()`, `deploy()`, `destroy()` (these already use correct paths)
- **User Impact**: Fixes remote backend deployments (S3, Azure, GCS) from consumer repositories
- **Breaking Changes**: None - this is a bug fix that corrects broken behavior
- **Dependencies**: No changes to dependencies or external APIs
