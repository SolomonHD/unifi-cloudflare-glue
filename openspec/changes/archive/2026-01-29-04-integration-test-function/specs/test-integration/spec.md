# Spec: Integration Test Function

## ADDED Requirements

### Requirement: test_integration Function

The Dagger module SHALL provide a `test_integration` function that creates ephemeral DNS resources with real Cloudflare and UniFi APIs, validates the setup, and guarantees cleanup regardless of test outcome.

#### Scenario: Full Integration Test Execution
Given a valid KCL source directory
And valid Cloudflare credentials (token, account ID, zone)
And valid UniFi credentials (API key or username/password)
When the `test_integration` function is called
Then it executes the following phases:
  1. Setup: Generate random test ID and KCL config
  2. Generation: Generate UniFi and Cloudflare JSON configs
  3. Deployment: Apply Terraform for both modules (local state only)
  4. Validation: Verify resources were created successfully
  5. Cleanup: Destroy resources (guaranteed to run via defer)
And returns a comprehensive test report

#### Scenario: Random Test ID Generation
Given the test_integration function is called
When the setup phase begins
Then it generates a random test ID (e.g., `test-a7x9k`)
And uses this ID for all resource naming (tunnels, hostnames)

#### Scenario: Local State Isolation
Given the test_integration function executes
When Terraform runs for both modules
Then it uses local state files only
And does NOT use or affect any remote state backends

#### Scenario: Guaranteed Cleanup via Defer
Given the test_integration function is called with cleanup=true (default)
When any phase fails (setup, generation, deployment, validation)
Then the cleanup phase still executes via Dagger's defer mechanism
And attempts to destroy all created resources

#### Scenario: Test Report Generation
Given all phases complete (success or failure)
When the function returns
Then it returns a string report containing:
  - Test ID used
  - Phase-by-phase results with durations
  - List of created resources
  - Validation results
  - Cleanup status

---

### Requirement: Cache Buster Parameter

The `test_integration` function SHALL support a `cache_buster` parameter to force Dagger cache invalidation.

#### Scenario: Force Cache Invalidation
Given the `test_integration` function is called with a non-empty `cache_buster` value
When the container is prepared for execution
Then the cache buster value is injected as an environment variable named `CACHE_BUSTER`
And Dagger treats the execution as different from previous runs

#### Scenario: No Cache Invalidation When Empty
Given the `test_integration` function is called with `cache_buster=""` (default)
When the function executes
Then no cache buster environment variable is set
And Dagger may return cached results if other inputs are identical

#### Scenario: Cache Buster Parameter Definition
Given the function signature
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
Given the function signature
Then the `wait_before_cleanup` parameter has:
  - Type: `int`
  - Default value: `0`
  - Annotation using `Annotated[int, Doc("...")]` with descriptive documentation

---

### Requirement: Required Parameters

The `test_integration` function SHALL accept all required parameters for both Cloudflare and UniFi access.

#### Scenario: Source Directory Parameter
Given the function signature
Then it accepts a required `source` parameter of type `dagger.Directory`
Containing the KCL module with schemas and generators

#### Scenario: Cloudflare Parameters
Given the function signature
Then it accepts these required Cloudflare parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `cloudflare_zone` | `str` | DNS zone for test records (e.g., test.example.com) |
| `cloudflare_token` | `dagger.Secret` | Cloudflare API token |
| `cloudflare_account_id` | `str` | Cloudflare account ID |

#### Scenario: UniFi Connection Parameters
Given the function signature
Then it accepts these required UniFi parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `unifi_url` | `str` | UniFi Controller URL |
| `api_url` | `str` | UniFi API URL (often same as unifi_url) |

---

### Requirement: UniFi Authentication (Mutually Exclusive)

The `test_integration` function SHALL support two authentication methods for UniFi, but only one may be used at a time.

#### Scenario: API Key Authentication
Given the function signature
Then it accepts an optional `unifi_api_key` parameter of type `dagger.Secret`
When this parameter is provided
Then username and password parameters must NOT be provided

#### Scenario: Username/Password Authentication
Given the function signature
Then it accepts optional parameters:
- `unifi_username` of type `dagger.Secret`
- `unifi_password` of type `dagger.Secret`
When both parameters are provided
Then the API key parameter must NOT be provided

#### Scenario: Authentication Validation - Neither Provided
Given a call with neither API key nor username/password
When the function validates parameters
Then it returns an error: "✗ Failed: Must provide either unifi_api_key OR both unifi_username and unifi_password"

#### Scenario: Authentication Validation - Both Provided
Given a call with both API key AND username/password
When the function validates parameters
Then it returns an error: "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."

---

### Requirement: Optional Parameters

The `test_integration` function SHALL support optional parameters for test customization.

#### Scenario: Cleanup Flag
Given the function signature
Then it accepts an optional `cleanup` parameter of type `bool`
With default value: `true`
When set to `false`
Then resources are NOT destroyed after testing (for debugging)

#### Scenario: Validate Connectivity Flag
Given the function signature
Then it accepts an optional `validate_connectivity` parameter of type `bool`
With default value: `false`
When set to `true`
Then the test attempts HTTP connectivity checks to tunnel endpoints

#### Scenario: Test Timeout
Given the function signature
Then it accepts an optional `test_timeout` parameter of type `str`
With default value: `"5m"`
Used to limit the duration of individual test operations

---

### Requirement: Test Phases

The `test_integration` function SHALL execute distinct phases with clear separation.

#### Scenario: Phase 1 - Setup
Given the test begins
When Phase 1 executes
Then it:
  1. Generates random test ID (e.g., `test-a7x9k`)
  2. Creates temporary KCL config with random hostnames
  3. Prepares working directory

#### Scenario: Phase 2 - Generation
Given Phase 1 completes
When Phase 2 executes
Then it:
  1. Runs KCL to generate unifi.json
  2. Runs KCL to generate cloudflare.json
  3. Validates JSON output files exist

#### Scenario: Phase 3 - Deployment
Given Phase 2 completes
When Phase 3 executes
Then it:
  1. Runs Terraform apply for UniFi DNS module first
  2. Waits for UniFi deployment to complete
  3. Runs Terraform apply for Cloudflare Tunnel module
  4. Captures all Terraform output

#### Scenario: Phase 4 - Validation
Given Phase 3 completes
When Phase 4 executes
Then it:
  1. Verifies tunnel exists in Cloudflare
  2. Verifies DNS records exist in Cloudflare
  3. Verifies DNS records exist in UniFi
  4. Optionally tests HTTP connectivity if enabled

#### Scenario: Phase 5 - Cleanup
Given any prior phase completes or fails
When Phase 5 executes (via defer)
Then it:
  1. Destroys Cloudflare resources first (reverse order)
  2. Destroys UniFi resources second
  3. Removes local state files
  4. Reports cleanup status

---

### Requirement: Test Report Format

The test report SHALL include comprehensive information about the test execution.

#### Scenario: Successful Test Report
Given all phases succeed
When the report is generated
Then it includes:
  - "✓ Integration Test Passed" header
  - Test ID used
  - Duration of each phase
  - List of created resources (tunnels, hostnames)
  - Validation results summary
  - "✓ Cleanup completed successfully"

#### Scenario: Failed Test Report
Given any phase fails
When the report is generated
Then it includes:
  - "✗ Integration Test Failed" header
  - Test ID used
  - Which phase failed
  - Error details from failed phase
  - Results from any successful prior phases
  - Cleanup status (attempted and result)

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

---

### Requirement: Error Handling

The `test_integration` function SHALL handle errors gracefully at each phase.

#### Scenario: Setup Phase Failure
Given Phase 1 (setup) fails
When the error is caught
Then the function still proceeds to Phase 5 (cleanup via defer)
And the report indicates setup failed with error details

#### Scenario: Generation Phase Failure
Given Phase 1 succeeds but Phase 2 (generation) fails
When the error is caught
Then the function still proceeds to Phase 5 (cleanup via defer)
And the report indicates generation failed with KCL error output

#### Scenario: Deployment Phase Failure
Given Phase 2 succeeds but Phase 3 (deployment) fails
When the error is caught
Then the function still proceeds to Phase 5 (cleanup via defer)
And attempts to destroy any partially created resources

#### Scenario: Validation Phase Failure
Given Phase 3 succeeds but Phase 4 (validation) fails
When the error is caught
Then the function still proceeds to Phase 5 (cleanup via defer)
And the report indicates which validation checks failed

---

### Requirement: Security

The `test_integration` function SHALL handle credentials securely.

#### Scenario: Secret Parameter Types
Given any credential parameter
Then it uses `dagger.Secret` type
And never appears as plain string in function signature

#### Scenario: No Secret Logging
Given secret values are provided
When the function executes
Then secret values never appear in:
  - Terraform command line arguments
  - Log output
  - Test reports
  - Error messages

#### Scenario: Random Resource Naming
Given the test executes
When resources are created
Then all resource names include the random test ID
And prevent collisions between concurrent test runs
