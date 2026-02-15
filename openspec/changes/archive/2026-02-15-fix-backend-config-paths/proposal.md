## Why

The `unifi-cloudflare-glue` Dagger module has inconsistent backend config file paths in `src/main/main.py`. When using remote Terraform backends (S3, etc.) from a consumer repository, Terraform init fails with:

```
Error: Failed to read file
The file "../root/.terraform/backend.tfbackend" could not be read.
```

This occurs because backend config files are being mounted at paths that don't match the paths referenced in the Terraform init commands, causing remote backend deployments to fail from consumer repositories.

## What Changes

- Fix path mismatch in `plan()` function (lines 1106 and 1201): Ensure backend config is mounted at `/root/.terraform/backend.tfbackend`
- Fix path mismatch in `get_tunnel_secrets()` function (line 2821): Ensure backend config is mounted at `/root/.terraform/backend.tfbackend`
- Ensure all backend config mounts use consistent `.tfbackend` extension (not `.hcl`)
- Verify `deploy_unifi()` and `deploy_cloudflare()` functions already have correct paths (no changes needed)

## Capabilities

### New Capabilities
<!-- No new capabilities - this is a bug fix -->

### Modified Capabilities
- `backend-config-path-consistency`: Fix file path inconsistencies in backend configuration handling across `plan()` and `get_tunnel_secrets()` functions to ensure remote backend deployments work correctly from consumer repositories.

## Impact

- **Affected Code**: `src/main/main.py` - `plan()` function (lines 1106, 1201) and `get_tunnel_secrets()` function (line 2821)
- **Behavior Change**: Remote backend deployments (S3, GCS, AzureRM) will now work correctly from consumer repositories
- **Backward Compatibility**: No breaking changes - this is a bug fix that corrects incorrect behavior
- **Terraform Backend Support**: Fixes initialization for all remote backend types (s3, azurerm, gcs, remote, etc.)
