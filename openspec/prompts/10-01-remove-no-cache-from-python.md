# OpenSpec Prompt: Remove no_cache Parameter from Python Functions

## Context

The `no_cache` boolean parameter was added to provide user-friendly cache bypassing, but Dagger's function-level caching makes it ineffective. The parameter needs to be removed from all function signatures in `src/main/main.py`.

## Goal

Remove the `no_cache` parameter from all Dagger functions and associated validation/conversion logic.

## Scope

### In Scope
- Remove `no_cache` parameter from function signatures:
  - `deploy()` - Line ~377
  - `plan()` - Line ~866
  - `destroy()` - Line ~1239
  - `test_integration()` - Line ~1881
- Remove mutual exclusion validation (e.g., "Cannot use both --no-cache and --cache-buster")
- Remove timestamp generation logic (`if no_cache: effective_cache_buster = str(int(time.time()))`)
- Simplify effective_cache_buster assignment to just use `cache_buster` directly
- Update parameter documentation strings in function signatures
- Update docstring examples to remove `--no-cache` usage
- Remove references to `no_cache` from Args sections in docstrings

### Out of Scope
- Markdown documentation files (handled in separate prompt)
- The `cache_buster` parameter itself (keep unchanged)
- How `cache_buster` is applied to containers (keep existing logic)

## Desired Behavior

### Function Signature Changes

**Before:**
```python
async def deploy(
    self,
    # ... other params ...
    no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False,
    cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = "",
) -> str:
```

**After:**
```python
async def deploy(
    self,
    # ... other params ...
    cache_buster: Annotated[str, Doc("Unique value to bypass Dagger cache (e.g., $(date +%s))")] = "",
) -> str:
```

### Logic Changes

**Before:**
```python
# Validate cache control options
if no_cache and cache_buster:
    return "✗ Failed: Cannot use both --no-cache and --cache-buster"

# Determine effective cache buster value
effective_cache_buster = cache_buster
if no_cache:
    import time as time_module
    effective_cache_buster = f"nocache-{int(time_module.time())}-{id(locals())}"
```

**After:**
```python
# Use cache_buster directly - no validation or conversion needed
effective_cache_buster = cache_buster
```

### Docstring Example Changes

**Before:**
```python
# Force fresh execution (bypass Dagger cache)
dagger call deploy \\
    --kcl-source=./kcl \\
    --unifi-url=https://unifi.local:8443 \\
    --unifi-api-key=env:UNIFI_API_KEY \\
    --unifi-only \\
    --no-cache
```

**After:**
```python
# Force fresh execution (bypass Dagger cache)
dagger call deploy \\
    --kcl-source=./kcl \\
    --unifi-url=https://unifi.local:8443 \\
    --unifi-api-key=env:UNIFI_API_KEY \\
    --unifi-only \\
    --cache-buster=$(date +%s)
```

## Constraints & Assumptions

- Only modify `src/main/main.py`
- Keep all other cache-busting logic intact (env var addition, kcl_source modification, etc.)
- Maintain backward compatibility for existing `--cache-buster` usage
- Update ALL occurrences in docstrings consistently

## Acceptance Criteria

1. No function signature contains `no_cache` parameter
2. No validation code checks `no_cache and cache_buster`
3. No code generates timestamps from `no_cache` flag
4. `effective_cache_buster = cache_buster` (simple assignment)
5. All docstring examples use `--cache-buster=$(date +%s)` pattern
6. All docstring Args sections document cache_buster only
7. Parameter descriptions updated to show shell command pattern

## Expected Changes

- ~20 deletions (parameter lines, validation lines, conversion lines)
- ~15 modifications (docstring examples, parameter descriptions)
- Net reduction in code complexity
