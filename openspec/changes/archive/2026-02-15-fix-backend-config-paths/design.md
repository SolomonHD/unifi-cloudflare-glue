## Context

The `unifi-cloudflare-glue` Dagger module provides functions for deploying hybrid DNS infrastructure using Terraform with various backend configurations (local, S3, GCS, AzureRM, etc.).

Currently, there is a file path inconsistency in the `plan()` and `get_tunnel_secrets()` functions:
- The `plan()` function mounts backend config files but was potentially using inconsistent paths between the mount location and the terraform init reference
- The `get_tunnel_secrets()` function similarly had a mismatch
- The `deploy_unifi()` and `deploy_cloudflare()` functions already have the correct implementation pattern

The `_process_backend_config()` helper function correctly returns `.tfbackend` as the extension, and the `deploy_*` functions correctly use this extension. The issue is ensuring `plan()` and `get_tunnel_secrets()` follow the same pattern.

## Goals / Non-Goals

**Goals:**
- Fix backend config file path inconsistencies in `plan()` function (lines 1106, 1201)
- Fix backend config file path inconsistency in `get_tunnel_secrets()` function (line 2821)
- Ensure all functions consistently use `/root/.terraform/backend.tfbackend` for mounting backend configs
- Ensure terraform init commands reference the same path used for mounting
- Use `.tfbackend` extension consistently (not `.hcl`)

**Non-Goals:**
- Changes to backend config processing logic (already correct in `_process_backend_config()`)
- Changes to Terraform module content
- Changes to function signatures or behavior
- Changes to `deploy_unifi()` or `deploy_cloudflare()` (already correct)

## Decisions

### Use `.tfbackend` extension consistently

**Decision**: All backend config mounts and references SHALL use the `.tfbackend` extension.

**Rationale**: 
- The `_process_backend_config()` function already returns `.tfbackend` as the extension
- This is the standard Terraform backend configuration file extension
- The `deploy_unifi()` and `deploy_cloudflare()` functions already use this pattern correctly

**Alternatives considered**:
- Keep using `.hcl` extension: Rejected because it conflicts with the existing working pattern in `deploy_*` functions

### Mount path: `/root/.terraform/backend.tfbackend`

**Decision**: All functions SHALL mount backend config files at `/root/.terraform/backend.tfbackend`.

**Rationale**:
- Consistent with the pattern already established in `deploy_unifi()` and `deploy_cloudflare()`
- The terraform init command uses `-backend-config=/root/.terraform/backend.tfbackend`
- Using a consistent path ensures predictability across all functions

**Alternatives considered**:
- Use different paths per function: Rejected because it creates unnecessary complexity and potential for errors

### Implementation approach

**Decision**: Direct file path string correction in the three identified locations.

**Rationale**:
- This is a straightforward bug fix with minimal scope
- No refactoring needed - just path alignment
- The pattern is already established in working functions

**Implementation details**:
1. Line 1106 in `plan()` (UniFi plan): Ensure path is `/root/.terraform/backend.tfbackend`
2. Line 1201 in `plan()` (Cloudflare plan): Ensure path is `/root/.terraform/backend.tfbackend`
3. Line 2821 in `get_tunnel_secrets()`: Ensure path is `/root/.terraform/backend.tfbackend`

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| [Risk] Changing paths could break existing deployments that rely on the current (incorrect) behavior | [Mitigation] The current behavior is already broken for remote backends - this fix corrects it. Local backends don't use these code paths. |
| [Risk] Path mismatch between mount and init command | [Mitigation] Both use the same constant path `/root/.terraform/backend.tfbackend` - verified by code review |
| [Risk] Regression in deploy functions | [Mitigation] No changes to deploy functions - they already have correct paths |

## Migration Plan

Not applicable - this is a bug fix that corrects incorrect behavior. No migration steps needed.

## Open Questions

None - the fix is straightforward and follows the established pattern in `deploy_unifi()` and `deploy_cloudflare()`.
