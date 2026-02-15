## Why

The `deploy_unifi()`, `deploy_cloudflare()`, and `destroy()` Dagger functions have critical bugs where they lose container references after execution and use fragile working directory logic. This prevents proper access to files created during Terraform operations (like `terraform.tfstate`). The `plan()` function already implements the correct pattern for container reference preservation and working directory handling. This change aligns the deployment functions with the proven `plan()` implementation to ensure consistent, reliable behavior.

## What Changes

- **Fix container reference preservation** in `deploy_unifi()` after `terraform init` and `terraform apply` executions
- **Fix container reference preservation** in `deploy_cloudflare()` after `terraform init` and `terraform apply` executions
- **Fix container reference preservation** in `destroy()` for both Cloudflare and UniFi destroy phases
- **Replace fragile working directory logic** that uses string checks (`"/module" in str(ctr)`) with explicit boolean checks based on `using_persistent_state`
- **Add proper intermediate awaiting** using `_ = await ctr.stdout()` pattern where output isn't needed
- Align all deployment functions with the robust patterns from the `plan()` function (lines 1181-1212)

## Capabilities

### New Capabilities

- `container-reference-preservation`: Ensures Dagger container references are preserved after `with_exec()` calls, enabling access to files created during Terraform operations
- `working-directory-logic`: Explicit working directory setup based on `using_persistent_state` boolean instead of fragile string checks

### Modified Capabilities

*None - this is an internal implementation fix that doesn't change external behavior or API contracts*

## Impact

- **Code**: `src/main/main.py` - `deploy_unifi()` (~356), `deploy_cloudflare()` (~542), `destroy()` (~1385)
- **Behavior**: Files created during Terraform operations (e.g., `terraform.tfstate`) will now be accessible from the preserved container reference
- **Reliability**: Eliminates race conditions and undefined behavior from lost container references
- **Maintainability**: Consistent pattern across all deployment functions matching the proven `plan()` implementation
- **No Breaking Changes**: External API remains unchanged; this is an internal bug fix
