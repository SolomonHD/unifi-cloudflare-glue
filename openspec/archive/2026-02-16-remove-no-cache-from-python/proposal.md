## Why

The `no_cache` boolean parameter was added to Dagger functions to provide a user-friendly way to bypass Dagger's caching. However, due to Dagger's aggressive function-level caching behavior, this boolean parameter is ineffective. The parameter becomes part of the function's cache key, meaning when `no_cache=True` is passed, Dagger still caches the result because the input is static. The only effective way to bypass cache is using the explicit `--cache-buster` parameter with a unique timestamp value on each invocation.

Removing this ineffective parameter simplifies the API, reduces code complexity, and eliminates confusion for users who might expect `--no-cache` to work. The `--cache-buster=$(date +%s)` pattern remains the supported and documented approach for cache bypass.

## What Changes

**BREAKING**: Remove `no_cache` parameter from all Dagger module functions

### Function Signature Changes
- Remove `no_cache: Annotated[bool, Doc(...)] = False` parameter from:
  - `deploy()` function (line ~377)
  - `plan()` function (line ~866)
  - `destroy()` function (line ~1239)
  - `test_integration()` function (line ~1881)

### Code Logic Changes
- Remove mutual exclusion validation: `if no_cache and cache_buster:` checks
- Remove timestamp generation logic: `if no_cache: effective_cache_buster = str(int(time.time()))`
- Simplify to direct assignment: `effective_cache_buster = cache_buster`
- Remove cache buster suffix append for `no_cache` in return results

### Documentation Changes
- Update `cache_buster` parameter documentation to emphasize shell timestamp pattern
- Remove all `no_cache` references from Args sections in docstrings
- Update all docstring examples to use `--cache-buster=$(date +%s)` instead of `--no-cache`
- Remove validation error messages mentioning `--no-cache`

### Files Modified
- `src/main/main.py` - All changes contained to this single file

## Capabilities

### New Capabilities
<!-- None - this is a removal/cleanup change -->

### Modified Capabilities
<!-- This is an implementation-only change that doesn't modify spec-level requirements.
     The existing deploy-function-cache-busting, plan-generation-cache-busting, 
     destroy-function-cache-busting, and test-integration specs already document
     the correct --cache-buster approach. This change aligns implementation with spec. -->

## Impact

### User-Facing Changes
- **CLI Breaking Change**: Users must replace `--no-cache` with `--cache-buster=$(date +%s)` in all commands
- **Simpler Mental Model**: Only one cache control mechanism (`--cache-buster`) instead of two confusing options
- **Error Messages**: No more "Cannot use both --no-cache and --cache-buster" validation errors

### Code Impact
- ~20 lines of code removed (parameter definitions, validation, timestamp generation)
- ~15 documentation updates (docstring examples, parameter descriptions)
- Reduced cyclomatic complexity in all four affected functions
- No changes to actual cache-busting behavior (when `--cache-buster` is used)

### Migration Guide for Users
```bash
# Before (will no longer work)
dagger call deploy --kcl-source=./kcl --unifi-only --no-cache

# After (correct usage)
dagger call deploy --kcl-source=./kcl --unifi-only --cache-buster=$(date +%s)
```

### Dependencies
- No external dependency changes
- No Terraform module changes
- No KCL module changes
- Pure Dagger/Python module cleanup
