# Proposal: Add cache_buster and wait_before_cleanup to test_integration

## Summary

Add two new optional parameters to the `test_integration` function to address Dagger caching issues and provide manual verification capabilities.

## Motivation

The `test_integration` function creates ephemeral Cloudflare and UniFi resources for integration testing. Due to Dagger's caching behavior, the function result is cached based on input parameters. When users run the test multiple times with the same inputs, Dagger returns the cached result, causing the same test ID to be reported even though the actual test execution should generate new resources.

Additionally, users need the ability to pause between resource creation and cleanup to manually verify the created resources.

## Proposed Changes

### 1. Cache Buster Parameter

- **Name:** `cache_buster`
- **Type:** `str`
- **Default:** `""` (empty string)
- **Documentation:** "Optional cache buster string. Change this value to force Dagger to re-execute the test instead of returning cached results."

When `cache_buster` is provided with a non-empty value:
- The value should be passed into the container execution as an environment variable (`CACHE_BUSTER`)
- This forces Dagger to treat the execution as different from previous runs
- Users can change the cache_buster value to trigger fresh test execution

### 2. Wait Before Cleanup Parameter

- **Name:** `wait_before_cleanup`
- **Type:** `int`
- **Default:** `0`
- **Documentation:** "Seconds to wait after creating resources before destroying them. Useful for manual verification of created resources."

When `wait_before_cleanup` is greater than 0:
- After Phase 4 (validation) completes successfully
- Before Phase 5 (cleanup) begins
- The function should pause/wait for the specified number of seconds
- The wait duration should be logged in the test report

## Acceptance Criteria

- [ ] `cache_buster` parameter added to `test_integration` signature with type `str`, default `""`, and proper `Annotated` + `Doc` annotation
- [ ] `wait_before_cleanup` parameter added to `test_integration` signature with type `int`, default `0`, and proper `Annotated` + `Doc` annotation
- [ ] `cache_buster` value is incorporated into container execution to invalidate Dagger cache when changed
- [ ] When `wait_before_cleanup > 0`, function pauses for specified seconds between validation and cleanup phases
- [ ] Test report includes cache_buster value when non-empty
- [ ] Test report includes wait duration when greater than 0
- [ ] Function maintains backward compatibility (existing calls without new parameters work unchanged)
- [ ] Example usage documented in docstring showing both new parameters

## Implementation Details

### Cache Buster Implementation

```python
# Add to container to invalidate cache when value changes
if cache_buster:
    base_container = base_container.with_env_variable("CACHE_BUSTER", cache_buster)
```

### Wait Before Cleanup Implementation

```python
# After validation, before cleanup
if wait_before_cleanup > 0:
    report_lines.append(f"PHASE 4.5: Waiting {wait_before_cleanup}s before cleanup...")
    await asyncio.sleep(wait_before_cleanup)
```

## Scope

**In scope:**
- Add `cache_buster` parameter to `test_integration` function
- Add `wait_before_cleanup` parameter to `test_integration` function
- Update function signature at line 737
- Integrate `cache_buster` into container execution to bust Dagger's cache
- Implement sleep/delay logic for `wait_before_cleanup` between resource creation and cleanup

**Out of scope:**
- Changing existing function behavior when new parameters are not provided
- Modifying other functions
- Changing the test logic or resource creation process
- Breaking changes to existing parameter interface

## References

- Target function: `test_integration` at line 737 in `src/main/main.py`
- Dagger caching documentation: Cache is keyed by function inputs and container state
