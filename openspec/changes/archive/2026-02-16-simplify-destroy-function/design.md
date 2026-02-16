## Context

The `destroy()` function currently uses separate Terraform modules for UniFi DNS (`terraform/modules/unifi/`) and Cloudflare Tunnel (`terraform/modules/cloudflare/`) management. After the introduction of the combined `terraform/modules/glue/` module and simplification of `deploy()`/`plan()` functions, the `destroy()` function needs to be updated for consistency and to support selective destruction of components.

## Goals / Non-Goals

**Goals:**
- Update `destroy()` to use the combined `terraform/modules/glue/` module
- Add `--unifi-only` and `--cloudflare-only` flags for selective component destruction
- Maintain backward compatibility (default behavior destroys both components)
- Use Terraform `-target` option for selective destruction
- Generate only necessary KCL configuration files based on flags

**Non-Goals:**
- Changes to `deploy()` or `plan()` functions (handled separately)
- Introduction of new authentication mechanisms
- Changes to the combined Terraform module itself
- Support for destroying individual resources (only module-level targeting)

## Decisions

### Use Terraform `-target` for Selective Destruction

**Decision:** Use Terraform's `-target` option (`-target=module.unifi_dns` or `-target=module.cloudflare_tunnel`) for selective destruction rather than managing separate state files.

**Rationale:**
- Maintains a single state file for consistency
- Leverages Terraform's built-in targeting mechanism
- Simpler implementation than managing separate state files
- The combined module already has proper module boundaries

**Alternatives Considered:**
- Separate state files: More complex state management, harder to maintain consistency
- Separate Terraform working directories: Would require duplicating configuration logic

### Conditional KCL Config Generation

**Decision:** Generate only the KCL configuration files needed for the selected destroy mode.

**Rationale:**
- Avoids unnecessary KCL execution
- Reduces potential errors from missing provider credentials for unused components
- Aligns with the principle of minimal required configuration

**Implementation Approach:**
- `unifi-only`: Generate only `unifi.json`
- `cloudflare-only`: Generate only `cloudflare.json`
- Default: Generate both `unifi.json` and `cloudflare.json`

### Validation for Mutually Exclusive Flags

**Decision:** Explicitly validate that `--unifi-only` and `--cloudflare-only` cannot both be set.

**Rationale:**
- Prevents user confusion about intent
- Both flags being set is semantically equivalent to default behavior
- Clear error message guides users to correct usage

**Error Message:** "Cannot use both --unifi-only and --cloudflare-only"

### Credential Requirements Based on Mode

**Decision:** Only require credentials for the component(s) being destroyed.

**Rationale:**
- `unifi-only` mode should not require Cloudflare credentials
- `cloudflare-only` mode should not require UniFi credentials
- Default mode requires both sets of credentials

**Implementation:**
- Move credential validation after flag parsing
- Validate only required credentials for the selected mode

## Risks / Trade-offs

**Risk:** Partial destroys may leave the system in an inconsistent state if there are cross-module dependencies.
→ **Mitigation:** The combined module uses `depends_on` which Terraform respects during destroy operations. Targeted destroys still respect these dependencies.

**Risk:** Users may expect individual resource targeting rather than module-level targeting.
→ **Mitigation:** Document that selective destroy operates at the module level. Individual resource management is out of scope for this change.

**Risk:** State file corruption during partial destroys.
→ **Mitigation:** Terraform's `-target` option is well-tested and safe. The state file remains consistent even with targeted operations.

**Trade-off:** Using `-target` for selective destroy means the Terraform state still contains the other module's resources, they just won't be managed in that operation.
→ **Acceptance:** This is the intended behavior - selective destroy is for operational convenience, not complete removal from state.

## Migration Plan

No migration needed. This is a new feature that adds optional flags to the existing `destroy()` function. Default behavior remains unchanged.

## Open Questions

None. The approach is straightforward and builds on existing patterns from the `deploy()` and `plan()` simplification work.
