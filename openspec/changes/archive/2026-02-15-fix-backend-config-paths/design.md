## Context

The `unifi-cloudflare-glue` Dagger module supports remote Terraform backends (S3, Azure, GCS, etc.) for team and enterprise use cases. When a backend config file is provided, it must be mounted into the container and referenced during `terraform init` using the `-backend-config` flag.

Currently, there is a path mismatch in three functions:
- `plan()` mounts the file at `/root/.terraform/backend.hcl` but references `/root/.terraform/backend.tfbackend`
- `get_tunnel_secrets()` mounts the file at `/root/.terraform/backend.hcl` but references `/root/.terraform/backend.tfbackend`

The functions `deploy_unifi()`, `deploy_cloudflare()`, and `destroy()` already use the correct path `/root/.terraform/backend.tfbackend` for both mounting and referencing.

The `_process_backend_config()` helper function already returns the extension `.tfbackend` for all backend config files, and the init commands are already using `-backend-config=/root/.terraform/backend.tfbackend`. The fix is to align the mount paths with the reference paths.

## Goals / Non-Goals

**Goals:**
- Fix the path mismatch in `plan()` function (lines 1106 and 1201)
- Fix the path mismatch in `get_tunnel_secrets()` function (line 2821)
- Ensure all backend config files use the `.tfbackend` extension consistently
- Enable remote backend deployments to work from consumer repositories

**Non-Goals:**
- Changes to backend config processing logic (already handled by `_process_backend_config()`)
- Changes to Terraform module content
- Changes to function signatures or behavior
- Adding new backend types

## Decisions

### Use `.tfbackend` extension consistently
The Terraform documentation recommends using `.tfbackend` for backend configuration files. The `_process_backend_config()` function already returns this extension, and the init commands reference it. We align all mount paths to use `.tfbackend`.

**Rationale:** Consistency with Terraform conventions and existing working code paths.

**Alternative considered:** Change the reference paths to `.hcl`. Rejected because `.tfbackend` is the Terraform convention and is already used in the working functions.

### Minimal changes: only fix the mount paths
The simplest fix is to change only the three lines that have the incorrect mount path. This minimizes risk and makes the change easy to review.

**Rationale:** Bug fixes should be minimal to reduce regression risk.

**Alternative considered:** Refactor backend config handling to a shared helper. Rejected as out of scope for a bug fix - this can be done later as a refactoring task.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Regression in other functions | The change only affects three specific lines; other functions already use the correct path |
| Breaking change for users who relied on the bug | None - the bug prevents remote backends from working, so no users could be relying on it |
| Extension mismatch with user-provided files | The `_process_backend_config()` function handles extension conversion; user can provide `.hcl` or `.yaml` files |

## Migration Plan

No migration needed. This is a bug fix that corrects broken behavior. Users who previously encountered the "Failed to read file" error will find that remote backend deployments now work correctly.

## Open Questions

None - the fix is straightforward and the correct paths are already established in the working functions.
