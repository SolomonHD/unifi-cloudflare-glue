# Proposal: Test Integration Cache Buster and Wait Parameters

## Summary

Add two optional parameters to the `test_integration` function to address Dagger caching issues and provide manual verification capabilities during integration testing.

## Motivation

The `test_integration` function creates ephemeral Cloudflare and UniFi resources for integration testing. Due to Dagger's caching behavior, the function result is cached based on input parameters. When users run the test multiple times with the same inputs, Dagger returns the cached result instead of executing fresh tests. This can cause the same test ID to be reported even though users expect new resources to be created.

Additionally, users need a way to pause between resource creation and cleanup to manually verify the created resources before they are destroyed.

## Proposed Changes

### 1. Cache Buster Parameter

Add `cache_buster` parameter:
- **Type:** `str`
- **Default:** `""` (empty string)
- **Purpose:** Force Dagger to re-execute the test instead of returning cached results

When `cache_buster` is provided with a non-empty value, it will be incorporated into the container execution (e.g., as an environment variable) to invalidate Dagger's cache and trigger fresh execution.

### 2. Wait Before Cleanup Parameter

Add `wait_before_cleanup` parameter:
- **Type:** `int`
- **Default:** `0`
- **Purpose:** Pause after creating resources before destroying them

When `wait_before_cleanup` is greater than 0, the function will pause for the specified number of seconds between the validation phase (Phase 4) and the cleanup phase (Phase 5). This allows users to manually inspect and verify the created resources.

## Implementation Target

- **File:** `src/main/main.py`
- **Function:** `test_integration` (line 737)
- **Approach:** Add optional parameters with defaults to maintain backward compatibility

## Backward Compatibility

Both parameters are fully optional with sensible defaults:
- `cache_buster=""` - No cache busting when empty
- `wait_before_cleanup=0` - No wait when zero

Existing calls to `test_integration` without these parameters will continue to work unchanged.

## Acceptance Criteria

- [ ] `cache_buster` parameter added with proper type annotations and documentation
- [ ] `wait_before_cleanup` parameter added with proper type annotations and documentation
- [ ] Cache buster value incorporated into container execution to invalidate Dagger cache
- [ ] Wait logic implemented between validation and cleanup phases
- [ ] Test report includes cache_buster and wait duration when used
- [ ] Backward compatibility maintained
- [ ] Example usage documented in function docstring
