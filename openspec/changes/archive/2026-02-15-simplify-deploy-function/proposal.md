## Why

The current `deploy()` function calls `deploy_unifi()` and `deploy_cloudflare()` sequentially with separate Terraform modules. When using persistent local state (`--state-dir`), both deployments share the same state file, causing the Cloudflare deployment to fail with provider configuration errors. This architectural issue prevents reliable deployment workflows and complicates the user experience.

## What Changes

- **BREAKING**: Remove `deploy_unifi()` function entirely (lines ~356-588)
- **BREAKING**: Remove `deploy_cloudflare()` function entirely (lines ~589-841)
- Modify `deploy()` to use the combined Terraform module at `terraform/modules/glue/`
- Add `--unifi-only` boolean flag for UniFi-only deployments
- Add `--cloudflare-only` boolean flag for Cloudflare-only deployments
- Add validation: error if both `--unifi-only` and `--cloudflare-only` are set
- Update function signature to make credentials optional based on deployment scope
- Single Terraform init/apply cycle for atomic deployment

## Capabilities

### New Capabilities
- `deploy-function-consolidation`: Unified deployment using combined Terraform module with selective component deployment flags

### Modified Capabilities
- None (this is a pure refactoring with breaking API changes)

## Impact

### API Changes
- **Removed Functions**: `deploy_unifi()`, `deploy_cloudflare()`
- **Modified Function**: `deploy()` - new parameters `unifi_only` and `cloudflare_only`
- **New Behavior**: Credentials optional based on deployment scope (UniFi-only doesn't require Cloudflare creds, vice versa)

### Files Modified
- `src/main/main.py`: Update `deploy()`, remove `deploy_unifi()`, remove `deploy_cloudflare()`

### Dependencies
- Requires `terraform/modules/glue/` combined module (completed in Prompt 10)
- KCL configuration generation functions remain unchanged

### Backward Compatibility
This is a **breaking change**. Users currently calling `deploy_unifi()` or `deploy_cloudflare()` directly will need to migrate to the new `deploy()` with appropriate flags.

### Migration Path
```bash
# Old way (will be removed)
dagger call deploy-unifi --source=. ...
dagger call deploy-cloudflare --source=. ...

# New way
dagger call deploy --kcl-source=./kcl --unifi-only ...
dagger call deploy --kcl-source=./kcl --cloudflare-only ...
```
