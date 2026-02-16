## Context

The Dagger module API has been simplified to use a unified Terraform module that combines UniFi DNS and Cloudflare Tunnel deployment. The previous separate functions (`deploy_unifi()`, `deploy_cloudflare()`) have been removed in favor of a single `deploy()` function with selective flags (`--unifi-only`, `--cloudflare-only`).

Current documentation still references the removed functions and does not explain the new unified approach or selective deployment flags. This creates confusion for users trying to follow outdated examples.

## Goals / Non-Goals

**Goals:**
- Update README.md Quick Start with unified deployment examples
- Update docs/dagger-reference.md with new function signatures and flags
- Update docs/deployment-patterns.md with simplified workflow documentation
- Remove all references to deleted `deploy_unifi()` and `deploy_cloudflare()` functions
- Document the `--unifi-only` and `--cloudflare-only` flags with usage examples

**Non-Goals:**
- Changes to example projects (handled separately)
- Changes to Terraform module documentation
- Adding new features or functionality
- Modifying the Dagger module implementation

## Decisions

### Decision: Update documentation in priority order
**Rationale**: Users typically encounter README.md first, then reference docs, then patterns. Updating in this order ensures the most-visible docs are corrected first.

**Priority order:**
1. README.md - First impression and quick start
2. docs/dagger-reference.md - Detailed function reference
3. docs/deployment-patterns.md - Advanced usage patterns

### Decision: Show unified deployment as primary example
**Rationale**: The unified approach is the recommended default. Selective deployment is an advanced use case.

**Approach**: 
- Primary examples show full `deploy` command with all parameters
- Secondary examples show `--unifi-only` and `--cloudflare-only` variations
- Clear note that flags are mutually exclusive

### Decision: Remove rather than deprecate old function references
**Rationale**: The old functions are already removed from code. Keeping references, even as "deprecated", adds confusion.

**Approach**: Full removal of:
- `deploy_unifi()` function documentation
- `deploy_cloudflare()` function documentation
- All examples using these functions

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Users with bookmarks to old anchors may get 404s | Not applicable (same file, different content) |
| Users following external blog posts may be confused | Add note in README about API simplification |
| Documentation temporarily inconsistent during transition | Update all three files in single PR/commit |

## Migration Plan

Not applicable - this is documentation-only with no migration required. Users already using the unified API will see clearer documentation. Users still looking for old functions will be directed to the new approach.

## Open Questions

None - the API changes are complete and the documentation scope is well-defined.
