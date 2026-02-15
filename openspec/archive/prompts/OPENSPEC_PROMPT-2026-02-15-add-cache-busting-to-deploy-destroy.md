# OpenSpec Prompt: Add Cache Busting to Deploy and Destroy Functions

## Context

The `plan` function in `src/main/main.py` has full cache busting support with `no_cache` and `cache_buster` parameters that work correctly. However, the `deploy` and `destroy` functions (and their sub-functions `deploy_unifi` and `deploy_cloudflare`) completely lack these parameters, making it impossible to bypass Dagger's cache when needed.

The `plan` function serves as the correct reference implementation (lines 983-1383).

## Goal

Add `no_cache` and `cache_buster` parameters to all deployment-related functions and implement proper cache busting by setting the `CACHE_BUSTER` environment variable on containers.

## Scope (In)

### Functions to Modify

1. **`deploy()`** (line ~746)
   - Add `no_cache: bool = False` parameter
   - Add `cache_buster: str = ""` parameter
   - Add cache buster validation (lines 1091-1093 pattern)
   - Calculate `effective_cache_buster` value
   - Pass `effective_cache_buster` to `deploy_unifi()` and `deploy_cloudflare()` calls
   - Update docstring with parameter documentation

2. **`destroy()`** (line ~1385)
   - Add `no_cache: bool = False` parameter
   - Add `cache_buster: str = ""` parameter
   - Add cache buster validation (lines 1091-1093 pattern)
   - Calculate `effective_cache_buster` value
   - Set `CACHE_BUSTER` environment variable on Cloudflare and UniFi containers
   - Update docstring with parameter documentation

3. **`deploy_unifi()`** (line ~356)
   - Add `no_cache: bool = False` parameter
   - Add `cache_buster: str = ""` parameter
   - Add cache buster validation
   - Calculate `effective_cache_buster` value
   - Set `CACHE_BUSTER` environment variable on the Terraform container before execution
   - Update docstring with parameter documentation

4. **`deploy_cloudflare()`** (line ~542)
   - Add `no_cache: bool = False` parameter
   - Add `cache_buster: str = ""` parameter
   - Add cache buster validation
   - Calculate `effective_cache_buster` value
   - Set `CACHE_BUSTER` environment variable on the Terraform container before execution
   - Update docstring with parameter documentation

### Code Patterns to Replicate

From `plan` function (lines 1091-1098):
```python
# Validate cache control options
if no_cache and cache_buster:
    raise ValueError("✗ Failed: Cannot use both --no-cache and --cache-buster")

# Determine effective cache buster value
effective_cache_buster = cache_buster
if no_cache:
    effective_cache_buster = str(int(time.time()))
```

From `plan` function (lines 1178-1179):
```python
# Add cache buster if provided
if effective_cache_buster:
    unifi_ctr = unifi_ctr.with_env_variable("CACHE_BUSTER", effective_cache_buster)
```

## Scope (Out)

- Container reference preservation fixes (covered in Prompt 02)
- Working directory logic fixes (covered in Prompt 02)
- Changes to `test_integration()` function (already has cache busting)
- Changes to `get_tunnel_secrets()` function
- Changes to `generate_*_config()` functions

## Desired Behavior

1. Users can run `dagger call deploy --no-cache` to bypass Dagger cache
2. Users can run `dagger call destroy --cache-buster=custom-key` for custom cache invalidation
3. Error message if both `--no-cache` and `--cache-buster` are used together
4. Cache busting works for both UniFi and Cloudflare deployments
5. All examples in docstrings show the new parameters

## Constraints & Assumptions

- The `time` module is already imported at the top of the file
- Must maintain backward compatibility (parameters have defaults)
- Follow existing code style and patterns from `plan` function
- Use `Annotated[type, Doc("...")]` for parameter type hints
- The `CACHE_BUSTER` environment variable name is the standard used across the module

## Acceptance Criteria

- [ ] `deploy()` function has `no_cache` and `cache_buster` parameters
- [ ] `destroy()` function has `no_cache` and `cache_buster` parameters
- [ ] `deploy_unifi()` function has `no_cache` and `cache_buster` parameters
- [ ] `deploy_cloudflare()` function has `no_cache` and `cache_buster` parameters
- [ ] All functions validate that `no_cache` and `cache_buster` are not both set
- [ ] All functions calculate `effective_cache_buster` correctly
- [ ] All functions set `CACHE_BUSTER` environment variable when applicable
- [ ] All function docstrings document the new parameters
- [ ] Example usage in docstrings includes `--no-cache` flag
- [ ] Error messages match the format: "✗ Failed: Cannot use both --no-cache and --cache-buster"

## Expected Files/Areas Touched

- `src/main/main.py`:
  - `deploy()` function signature and implementation (line ~746-981)
  - `destroy()` function signature and implementation (line ~1385-1719)
  - `deploy_unifi()` function signature and implementation (line ~356-541)
  - `deploy_cloudflare()` function signature and implementation (line ~542-744)

## Dependencies

- None (this is the first prompt in the sequence)

## Notes

The pattern for setting the environment variable should be applied to the container AFTER all other setup but BEFORE the terraform init/apply execution. This ensures the cache buster affects the execution but doesn't interfere with file mounting or other setup steps.
