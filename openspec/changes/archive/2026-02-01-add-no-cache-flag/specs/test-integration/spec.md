## ADDED Requirements

### Requirement: No-Cache Flag Parameter

The `test_integration` function SHALL support a `no_cache` boolean parameter that automatically generates an epoch timestamp for cache invalidation.

#### Scenario: No-Cache Flag Defaults to False
Given the `test_integration` function signature
Then the `no_cache` parameter has:
  - Type: `bool`
  - Default value: `False`
  - Annotation using `Annotated[bool, Doc("...")]` with descriptive documentation

#### Scenario: No-Cache Flag Generates Epoch Timestamp
Given the `test_integration` function is called with `no_cache=True`
When the function logic processes parameters
Then the current epoch time is generated using `int(time.time())`
And the value is converted to string and assigned to `cache_buster`
And the `CACHE_BUSTER` environment variable is set in the container

#### Scenario: No-Cache Flag Compatible with Report Output
Given the `test_integration` function executes with `no_cache=True`
When the test report is generated
Then the report includes the auto-generated cache buster value
And reports it as "Cache Buster: {timestamp}" in the initial test information section

---

### Requirement: Parameter Validation

The function SHALL validate that `no_cache` and `cache_buster` parameters are not used simultaneously.

#### Scenario: Both Flags Provided Returns Error
Given the `test_integration` function is called with both `no_cache=True` and a non-empty `cache_buster` value
When the function begins execution
Then the function returns an error message: "✗ Failed: Cannot use both --no-cache and --cache-buster"
And no resources are created

#### Scenario: Only No-Cache Flag Provided
Given the `test_integration` function is called with `no_cache=True` and `cache_buster=""` (default)
When the function validates parameters
Then validation passes
And the epoch timestamp is generated automatically

#### Scenario: Only Cache-Buster Flag Provided
Given the `test_integration` function is called with `no_cache=False` (default) and a non-empty `cache_buster` value
When the function validates parameters
Then validation passes
And the provided `cache_buster` value is used as-is

---

### Requirement: Time Module Import

The Python module SHALL import the `time` module for epoch timestamp generation.

#### Scenario: Time Module Available
Given the `src/main/main.py` file
Then the file contains `import time` at the top of the file with other imports
And the import is available for use in the `test_integration` function

---

## MODIFIED Requirements

### Requirement: Cache Buster Parameter Documentation

The existing `cache_buster` parameter documentation SHALL be updated to clarify its relationship with the new `no_cache` parameter.

#### Scenario: Updated Cache Buster Documentation
Given the `cache_buster` parameter in the function signature
Then the Doc annotation includes text indicating:
  - That this is an advanced option for custom cache keys
  - That `--no-cache` is the preferred simple option
  - That both options cannot be used together

---

### Requirement: Function Docstring Examples

The `test_integration` function docstring SHALL include usage examples for the new `--no-cache` flag.

#### Scenario: No-Cache Example in Docstring
Given the function docstring
Then it includes an example showing:
  ```bash
  # With --no-cache to force re-execution (auto-generates timestamp)
  dagger call test-integration \\
      --source=. \\
      --cloudflare-zone=test.example.com \\
      --cloudflare-token=env:CF_TOKEN \\
      --cloudflare-account-id=xxx \\
      --unifi-api-key=env:UNIFI_API_KEY \\
      --unifi-url=https://unifi.local:8443 \\
      --api-url=https://unifi.local:8443 \\
      --no-cache
  ```

#### Scenario: Updated Cache Buster Example
Given the function docstring
Then the existing cache buster example is updated to clarify it is for advanced use:
  ```bash
  # With custom cache buster (advanced use)
  dagger call test-integration \\
      --source=. \\
      --cloudflare-zone=test.example.com \\
      --cloudflare-token=env:CF_TOKEN \\
      --cloudflare-account-id=xxx \\
      --unifi-api-key=env:UNIFI_API_KEY \\
      --unifi-url=https://unifi.local:8443 \\
      --api-url=https://unifi.local:8443 \\
      --cache-buster=custom-key-123
  ```
