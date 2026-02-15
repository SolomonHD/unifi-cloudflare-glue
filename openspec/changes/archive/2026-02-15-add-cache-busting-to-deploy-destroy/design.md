## Context

The Dagger module provides infrastructure deployment functions (`plan`, `deploy`, `destroy`) for managing UniFi DNS and Cloudflare Tunnel configurations. The `plan` function already implements cache busting support using the dual-parameter approach (`no_cache` boolean flag and `cache_buster` custom string), but the deployment functions (`deploy`, `destroy`, `deploy_unifi`, `deploy_cloudflare`) lack this capability entirely.

Dagger's aggressive caching can cause issues during:
- Integration testing against live APIs
- Debugging intermittent issues that require fresh execution
- Scenarios where external state has changed between runs

The existing `plan` function (lines 983-1383 in `src/main/main.py`) serves as the reference implementation for the cache busting pattern.

## Goals / Non-Goals

**Goals:**
- Add consistent cache busting support to all deployment-related functions
- Maintain backward compatibility (all new parameters have defaults)
- Follow the established pattern from the `plan` function
- Provide clear error messages for invalid parameter combinations
- Ensure cache buster is applied at the correct point in container lifecycle

**Non-Goals:**
- Modify the `plan` function (already has cache busting)
- Modify `test_integration()` function (already has cache busting)
- Change existing container setup or working directory logic (covered in Prompt 02)
- Add cache busting to helper/generator functions

## Decisions

### Decision 1: Replicate the `plan` function pattern exactly
**Rationale:** The `plan` function's implementation is proven and consistent with the module's existing patterns. Using the same validation logic, error messages, and environment variable approach ensures a uniform user experience.

**Alternative considered:** Creating a shared utility function for cache buster calculation. Rejected because the current pattern is simple (5 lines of code) and explicit duplication is clearer than indirection for this case.

### Decision 2: Apply cache buster after container setup but before execution
**Rationale:** The cache buster must be set after all file mounting and directory setup is complete to avoid interfering with those operations, but before terraform commands execute to ensure the cache key affects the operation.

**Pattern from `plan` function:**
```python
# After all setup operations
if effective_cache_buster:
    container = container.with_env_variable("CACHE_BUSTER", effective_cache_buster)
# Then execute terraform commands
```

### Decision 3: Use `Annotated[type, Doc()]` for parameter type hints
**Rationale:** Consistent with the existing codebase style and provides inline documentation visible in Dagger's CLI help output.

### Decision 4: Pass cache buster through the call chain
**Rationale:** The `deploy()` function orchestrates calls to `deploy_unifi()` and `deploy_cloudflare()`. Rather than having `deploy()` set the environment variable (which wouldn't work since it doesn't have direct container access), the effective cache buster value is passed down to the sub-functions that manage the containers.

**Flow:**
```
deploy(effective_cache_buster)
  ├─→ deploy_unifi(cache_buster=effective_cache_buster)
  │     └─→ Sets CACHE_BUSTER on UniFi container
  └─→ deploy_cloudflare(cache_buster=effective_cache_buster)
        └─→ Sets CACHE_BUSTER on Cloudflare container
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Parameter proliferation (4 functions × 2 parameters = 8 new params) | Parameters are optional with sensible defaults; only power users need to specify them |
| Inconsistent application between functions | Follow the same code pattern in all four functions; use copy-paste from `plan` function |
| Cache buster applied at wrong lifecycle point | Document in spec requirements that env var must be set after setup, before execution |
| Error message format inconsistency | Use exact error message from `plan` function: "✗ Failed: Cannot use both --no-cache and --cache-buster" |

## Migration Plan

This change is purely additive and backward compatible:

1. **Deployment:** No special steps required; existing calls without new parameters work unchanged
2. **Rollback:** Remove added parameters and cache buster logic if needed
3. **User communication:** Update function docstrings with usage examples showing new parameters

## Open Questions

None - the implementation pattern is well-established from the `plan` function reference.
