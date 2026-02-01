# OpenSpec Change Prompt

## Context

The `test_integration` function in `src/main/main.py` (line 737) creates ephemeral Cloudflare and UniFi resources for integration testing. Due to Dagger's caching behavior, the function result is cached based on input parameters. When users run the test multiple times with the same inputs, Dagger returns the cached result, causing the same test ID to be reported even though the actual test execution should generate new resources.

## Goal

Add two new optional parameters to the `test_integration` function to address caching issues and provide manual verification capabilities.

## Scope

**In scope:**
- Add `cache_buster` parameter (optional string, default empty string) to force re-execution
- Add `wait_before_cleanup` parameter (optional integer, default 0) to pause before resource destruction
- Update function signature at line 737
- Integrate `cache_buster` into container execution to bust Dagger's cache
- Implement sleep/delay logic for `wait_before_cleanup` between resource creation and cleanup

**Out of scope:**
- Changing existing function behavior when new parameters are not provided
- Modifying other functions
- Changing the test logic or resource creation process
- Breaking changes to existing parameter interface

## Desired Behavior

### 1. Cache Buster Parameter

- **Name:** `cache_buster`
- **Type:** `str`
- **Default:** `""` (empty string)
- **Documentation:** "Optional cache buster string. Change this value to force Dagger to re-execute the test instead of returning cached results."

When `cache_buster` is provided with a non-empty value:
- The value should be passed into the container execution (e.g., as an environment variable)
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

## Constraints & Assumptions

- Both parameters must be fully optional with defaults to maintain backward compatibility
- The `cache_buster` should use Dagger's cache invalidation mechanism (e.g., `with_env_variable` with the value)
- The wait implementation should use an async-compatible sleep
- The test report output should indicate when cache_buster and wait are being used
- Existing tests should continue to work without specifying these parameters

## Acceptance Criteria

- [ ] `cache_buster` parameter added to `test_integration` signature with type `str`, default `""`, and proper `Annotated` + `Doc` annotation
- [ ] `wait_before_cleanup` parameter added to `test_integration` signature with type `int`, default `0`, and proper `Annotated` + `Doc` annotation
- [ ] `cache_buster` value is incorporated into container execution to invalidate Dagger cache when changed
- [ ] When `wait_before_cleanup > 0`, function pauses for specified seconds between validation and cleanup phases
- [ ] Test report includes cache_buster value when non-empty
- [ ] Test report includes wait duration when greater than 0
- [ ] Function maintains backward compatibility (existing calls without new parameters work unchanged)
- [ ] Example usage documented in docstring showing both new parameters

## Reference

- Target function: `test_integration` at line 737 in `src/main/main.py`
- Dagger caching documentation: Cache is keyed by function inputs and container state
