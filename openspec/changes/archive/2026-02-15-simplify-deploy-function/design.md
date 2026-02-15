## Context

The current Dagger module has three deployment functions:
- `deploy_unifi()`: Deploys UniFi DNS configuration using `terraform/modules/unifi-dns/`
- `deploy_cloudflare()`: Deploys Cloudflare Tunnel using `terraform/modules/cloudflare-tunnel/`
- `deploy()`: Orchestrates both deployments by calling the above two functions sequentially

When using persistent local state (`--state-dir`), the sequential deployment causes issues because both deployments share the same state directory and `.terraform` directory. The second deployment (Cloudflare) fails because it finds the UniFi provider state from the first deployment.

The combined Terraform module at `terraform/modules/glue/` was created to solve this by wrapping both sub-modules in a single Terraform configuration with explicit dependencies.

## Goals / Non-Goals

**Goals:**
- Consolidate all deployment logic into a single `deploy()` function
- Support selective component deployment via flags (`--unifi-only`, `--cloudflare-only`)
- Use the combined Terraform module for atomic deployments
- Eliminate state sharing issues between separate deployments
- Simplify the public API by removing redundant functions

**Non-Goals:**
- Changes to `plan()` function (handled in Prompt 12)
- Changes to `destroy()` function (handled in Prompt 13)
- Changes to the combined Terraform module itself
- Changes to KCL configuration generation

## Decisions

### Decision: Remove deploy_unifi() and deploy_cloudflare() functions
**Rationale**: Having three functions (deploy, deploy_unifi, deploy_cloudflare) creates confusion and maintenance overhead. The selective deployment flags provide the same functionality with a cleaner API.

**Alternative considered**: Keep the functions as internal helpers. Rejected because it adds complexity and doesn't solve the state sharing issue.

### Decision: Make credentials optional based on deployment scope
**Rationale**: When using `--unifi-only`, Cloudflare credentials are not needed. Making them optional improves UX and security (principle of least privilege).

**Implementation approach**:
- Default mode: Both credential sets required
- `--unifi-only`: Only UniFi credentials required
- `--cloudflare-only`: Only Cloudflare credentials required

### Decision: Single Terraform init/apply cycle
**Rationale**: The combined module handles both components in one operation. This ensures atomic deployment and eliminates the state directory cleanup issues.

**Container reference management**: The container reference must be preserved after `terraform apply` to allow state file export if needed.

### Decision: Error if both flags are set
**Rationale**: `--unifi-only` and `--cloudflare-only` are mutually exclusive. Setting both is a user error that should fail fast with a clear message.

## Risks / Trade-offs

**Risk**: Breaking change for existing users of `deploy_unifi()` and `deploy_cloudflare()`
→ **Mitigation**: Clear migration documentation, major version bump, deprecation notice in CHANGELOG

**Risk**: Users may be confused by credential requirements changing based on flags
→ **Mitigation**: Clear error messages indicating which credentials are required for the selected deployment scope

**Risk**: Combined module may have different error handling characteristics
→ **Mitigation**: Thorough testing with integration tests, error message preservation from Terraform

## Migration Plan

### For Users

**Before (will be removed):**
```bash
dagger call deploy-unifi \
    --source=. \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY
```

**After:**
```bash
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only
```

### Implementation Steps

1. Update `deploy()` function signature to add `unifi_only` and `cloudflare_only` parameters
2. Add credential validation logic based on deployment scope
3. Add mutual exclusion validation for flags
4. Modify deployment logic to use combined module
5. Remove `deploy_unifi()` function entirely
6. Remove `deploy_cloudflare()` function entirely
7. Update docstrings and examples
8. Test all three deployment modes (full, unifi-only, cloudflare-only)

## Open Questions

None - the combined module interface is already defined and the approach is straightforward.
