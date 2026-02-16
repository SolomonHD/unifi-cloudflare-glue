## Context

The Dagger module currently has two cache control mechanisms:

1. **`no_cache` (boolean)**: Auto-generates a timestamp when True - **This does NOT work**
2. **`cache_buster` (string)**: Uses the provided value directly - **This is the only working approach**

The `no_cache` parameter was intended to provide a simple flag for users to bypass caching without manually generating timestamps. However, Dagger's function-level caching caches the function result based on input parameters. When a user passes `--no-cache`, the parameter value `True` becomes part of the cache key. Since `True` is static, Dagger returns cached results from previous runs with `no_cache=True`.

The `cache_buster` parameter works because each unique string value creates a different cache key. Using shell substitution like `--cache-buster=$(date +%s)` generates a unique value on every invocation.

### Current Code Pattern (in all 4 functions)

```python
async def deploy(...,
    no_cache: Annotated[bool, Doc("Bypass Dagger cache")] = False,
    cache_buster: Annotated[str, Doc("Custom cache key")] = "",
) -> str:
    # Validate mutual exclusion
    if no_cache and cache_buster:
        return "✗ Failed: Cannot use both --no-cache and --cache-buster"
    
    # Determine effective cache buster
    effective_cache_buster = cache_buster
    if no_cache:
        import time as time_module
        effective_cache_buster = f"nocache-{int(time_module.time())}-{id(locals())}"
```

### Affected Functions

1. `deploy()` - ~3000 lines, main deployment function
2. `plan()` - Plan generation function  
3. `destroy()` - Resource destruction function
4. `test_integration()` - Integration testing function

## Goals / Non-Goals

**Goals:**
- Remove the ineffective `no_cache` parameter from all function signatures
- Remove associated validation and timestamp generation logic
- Update documentation to consistently promote `--cache-buster=$(date +%s)`
- Maintain all existing `cache_buster` functionality
- Reduce code complexity and API surface area

**Non-Goals:**
- Do NOT change the `cache_buster` parameter behavior
- Do NOT modify Terraform module logic
- Do NOT modify KCL module logic  
- Do NOT modify markdown documentation (handled in separate change)
- Do NOT add new features or capabilities

## Decisions

### Decision: Simple Assignment Instead of Conditional Logic

**Choice**: Change `effective_cache_buster = cache_buster if not no_cache else timestamp` to `effective_cache_buster = cache_buster`

**Rationale**: 
- Eliminates the conditional branch entirely
- No functional change when `cache_buster` is provided
- Cleaner, more maintainable code

**Alternative Considered**: Keep conditional but only use `cache_buster` - rejected as unnecessary complexity

### Decision: Update Parameter Documentation

**Choice**: Change `cache_buster` description from "Custom cache key (advanced use)" to "Unique value to bypass Dagger cache (use --cache-buster=$(date +%s))"

**Rationale**:
- Makes the correct usage pattern explicit
- Removes implication that this is only for "advanced" use
- Provides copy-pasteable example

### Decision: Remove Validation Error Message

**Choice**: Delete the "Cannot use both --no-cache and --cache-buster" validation entirely

**Rationale**:
- Only existed because of the mutual exclusion between two cache control options
- With only one option, no validation needed
- Simplifies error handling paths

### Decision: Preserve No-Op Cache Buster Behavior

**Choice**: Keep the `if effective_cache_buster:` guards around cache-busting logic

**Rationale**:
- Empty string `cache_buster=""` should remain a no-op (no cache busting)
- Prevents unnecessary file creation and env var pollution when not needed
- Maintains backward compatibility for existing usage without cache busting

## Risks / Trade-offs

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking change for users using `--no-cache` | Medium - Users with scripts using `--no-cache` will see errors | Document migration path clearly; `--cache-buster=$(date +%s)` is equivalent |
| Users confused why `--no-cache` disappeared | Low - Parameter was already non-functional | Update CHANGELOG with clear explanation; shell command pattern is intuitive |
| Accidental removal of cache_buster logic | Medium - Could break working cache bypass | Code review; tests verify cache_buster still works |
| Incomplete docstring updates | Low - Inconsistent documentation | Search for all "no_cache" references; review all Args sections |

### Breaking Change Notice

This is a **BREAKING CHANGE** for any users currently using `--no-cache`. However, since the parameter never actually worked, affected users were likely experiencing unexpected caching behavior. The migration is straightforward:

```bash
# Before (non-functional)
dagger call deploy --kcl-source=./kcl --no-cache

# After (working)
dagger call deploy --kcl-source=./kcl --cache-buster=$(date +%s)
```

## Migration Plan

### Implementation Steps

1. **Remove parameters**: Delete `no_cache` from function signatures (4 functions)
2. **Remove validation**: Delete `if no_cache and cache_buster:` checks (4 locations)
3. **Simplify assignment**: Change to `effective_cache_buster = cache_buster` (4 locations)
4. **Update docstrings**: Remove `no_cache` from Args sections (4 locations)
5. **Update examples**: Change `--no-cache` to `--cache-buster=$(date +%s)` in all docstring examples
6. **Update parameter docs**: Revise `cache_buster` descriptions to emphasize shell pattern
7. **Clean up**: Remove unused `time` import if no longer needed elsewhere

### Verification

- Run `dagger functions` to ensure module loads successfully
- Verify `--cache-buster=$(date +%s)` works in `deploy`, `plan`, `destroy`, and `test_integration`
- Confirm `--no-cache` no longer appears in help output

### Rollback

If issues discovered:
1. Revert the commit
2. The old code remains functional (just with non-working `--no-cache`)
3. Re-release with restored parameter

## Open Questions

None - the scope and approach are clear from the prompt requirements.
