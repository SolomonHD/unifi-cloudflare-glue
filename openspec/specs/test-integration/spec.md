# Spec: Test Integration Cache Buster and Wait Parameters

## ADDED Requirements

### Requirement: Cache Buster Parameter

The `test_integration` function SHALL support a `cache_buster` parameter to force Dagger cache invalidation.

#### Scenario: Force Cache Invalidation
Given the `test_integration` function is called with a non-empty `cache_buster` value
When the container is prepared for execution
Then the cache buster value is injected as an environment variable
And Dagger treats the execution as different from previous runs

#### Scenario: No Cache Invalidation When Empty
Given the `test_integration` function is called with `cache_buster=""` (default)
When the function executes
Then no cache buster environment variable is set
And Dagger may return cached results if other inputs are identical

#### Scenario: Cache Buster Parameter Definition
Given the function signature at line 737
Then the `cache_buster` parameter has:
  - Type: `str`
  - Default value: `""`
  - Annotation using `Annotated[str, Doc("...")]` with descriptive documentation

---

### Requirement: Wait Before Cleanup Parameter

The `test_integration` function SHALL support a `wait_before_cleanup` parameter to pause between resource creation and destruction.

#### Scenario: Pause Between Validation and Cleanup
Given the `test_integration` function is called with `wait_before_cleanup` > 0
When Phase 4 (validation) completes successfully
Then the function pauses for the specified number of seconds
Before proceeding to Phase 5 (cleanup)

#### Scenario: No Wait When Zero
Given the `test_integration` function is called with `wait_before_cleanup=0` (default)
When Phase 4 (validation) completes
Then the function immediately proceeds to Phase 5 (cleanup)
Without any delay

#### Scenario: Async-Compatible Wait Implementation
Given the wait logic is implemented
When the wait is executed
Then it uses async-compatible sleep (e.g., `asyncio.sleep()`)
To avoid blocking the event loop

#### Scenario: Wait Parameter Definition
Given the function signature at line 737
Then the `wait_before_cleanup` parameter has:
  - Type: `int`
  - Default value: `0`
  - Annotation using `Annotated[int, Doc("...")]` with descriptive documentation

---

### Requirement: Cache Buster Integration

The cache buster value SHALL be properly integrated into container execution to invalidate Dagger's cache.

#### Scenario: Environment Variable Injection
Given a non-empty `cache_buster` value is provided
When the container is configured for execution
Then the cache buster value is injected as an environment variable named `CACHE_BUSTER`
Using Dagger's `with_env_variable()` method

#### Scenario: Container Cache Invalidation
Given the `CACHE_BUSTER` environment variable is set with a unique value
When Dagger evaluates the container for caching
Then the container state is considered different from runs with different cache buster values
Causing fresh execution instead of cache hit

---

### Requirement: Test Report Enhancements

The test report SHALL include information about cache buster and wait duration when these features are used.

#### Scenario: Cache Buster in Report
Given the `test_integration` function executes with a non-empty `cache_buster`
When the test report is generated
Then the report includes the cache buster value in the initial test information section

#### Scenario: Wait Duration in Report
Given the `test_integration` function executes with `wait_before_cleanup` > 0
When the test report is generated
Then the report includes:
  - The configured wait duration
  - A message indicating when the wait is occurring
  - Confirmation when the wait completes

#### Scenario: Backward Compatible Report Format
Given the `test_integration` function executes without new parameters
When the test report is generated
Then the report format is identical to the original format
With no mention of cache buster or wait duration

---

### Requirement: Backward Compatibility

The function SHALL maintain backward compatibility with existing calls.

#### Scenario: Existing Calls Without New Parameters
Given existing code calls `test_integration` without `cache_buster` or `wait_before_cleanup`
When the function is invoked
Then the call succeeds without errors
And uses the default values for both parameters

#### Scenario: Existing Calls With Partial Parameters
Given existing code calls `test_integration` with some but not all new parameters
When the function is invoked
Then the call succeeds
And uses provided values for specified parameters
And default values for unspecified parameters
