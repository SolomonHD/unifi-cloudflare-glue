## Context

The `unifi-cloudflare-glue` Dagger module embeds Terraform modules within its source tree at `terraform/modules/unifi-dns/` and `terraform/modules/cloudflare-tunnel/`. These modules need to be accessible when the Dagger module is called from external projects.

### Current Bug

Multiple functions use `dagger.dag.directory()` which resolves relative to the **calling project's** working directory instead of the module's own source. When an external project (e.g., `portainer-docker-compose`) calls the module, the path resolution fails because it looks for `portainer-docker-compose/terraform/modules/...` instead of `unifi-cloudflare-glue/terraform/modules/...`.

### Dagger API Behavior

- `dagger.dag.directory()` - Returns a directory relative to the caller's context (working directory of the calling project)
- `dagger.dag.current_module().source()` - Returns the module's own source directory, regardless of where it's called from

## Goals / Non-Goals

**Goals:**
- Fix all instances where embedded Terraform modules are incorrectly loaded using `dagger.dag.directory()`
- Ensure Terraform modules are always loaded from the module's own source directory
- Maintain backwards compatibility with existing function signatures and behavior
- Preserve existing error handling patterns

**Non-Goals:**
- Changing the Terraform module contents or logic
- Adding new features or functionality
- Refactoring unrelated code paths
- Changing how `source` parameters are used for KCL/config files

## Decisions

### Decision: Use `current_module().source()` Pattern

**Choice:** Replace `dagger.dag.directory().directory("terraform/modules/...")` with `dagger.dag.current_module().source().directory("terraform/modules/...")`

**Rationale:**
- This is the idiomatic Dagger pattern for accessing module-embedded resources
- It works correctly regardless of where the module is called from
- It's the minimal change that fixes the bug without side effects

**Alternatives Considered:**
- **Parameter-based path injection**: Would require changing function signatures and pushing complexity to callers. Rejected because it breaks backwards compatibility and adds unnecessary complexity.
- **Environment variable for module path**: Would require runtime configuration and be brittle. Rejected because it's non-standard and harder to maintain.

### Decision: Preserve Existing Error Handling

**Choice:** Keep existing try/except blocks around the module loading code

**Rationale:**
- The bug is about path resolution, not error handling
- Existing error handling should still work after the fix
- Changing error handling is out of scope for this bug fix

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Missed instances | Comprehensive code review of all functions listed in proposal; grep for pattern |
| Breaking existing callers | No API changes; only internal path resolution changes |
| Module path assumptions | Verify `terraform/modules/` structure exists in repository |
| Test coverage gap | Manual verification required as specified in testing notes |

## Migration Plan

This is a bug fix with no migration required:

1. **No action needed for callers**: The fix is internal to the module
2. **No breaking changes**: Function signatures remain unchanged
3. **No configuration changes**: Path resolution is automatic

**Rollout:**
1. Implement the fix in `src/main/main.py`
2. Update CHANGELOG.md with bug fix entry
3. Bump patch version in VERSION file
4. Tag and release new version
5. Test by calling from external project to verify fix

## Open Questions

None - the implementation approach is straightforward and well-understood.
