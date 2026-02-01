# Spec Delta: Terraform State Persistence for Integration Tests

## ADDED Requirements

### Requirement: Cloudflare State Export

The test_integration function SHALL export Cloudflare Terraform state after successful resource creation.

#### Scenario: Export state after Cloudflare apply
Given: Phase 2 (Cloudflare resource creation) executes successfully
When: The `terraform apply -auto-approve` command completes without error
Then: The function reads `/module/terraform.tfstate` from the Cloudflare container
And: The state content is stored in the `cloudflare_state` variable
And: A log message indicates state export success

#### Scenario: State export with error handling
Given: Phase 2 (Cloudflare resource creation) executes successfully
When: State export is attempted
And: An error occurs reading the state file
Then: The error is caught and logged as a warning
And: The `cloudflare_state` variable is set to an empty string
And: Test execution continues without failing

#### Scenario: State export using Dagger API
Given: The Cloudflare container exists after apply
When: State export is performed
Then: The function uses `container.file("/module/terraform.tfstate").contents()`
And: The state is read as a string (async operation with await)

---

### Requirement: UniFi State Export

The test_integration function SHALL export UniFi Terraform state after successful resource creation.

#### Scenario: Export state after UniFi apply
Given: Phase 3 (UniFi resource creation) executes successfully
When: The `terraform apply -auto-approve` command completes without error
Then: The function reads `/module/terraform.tfstate` from the UniFi container
And: The state content is stored in the `unifi_state` variable
And: A log message indicates state export success

#### Scenario: State export with error handling
Given: Phase 3 (UniFi resource creation) executes successfully
When: State export is attempted
And: An error occurs reading the state file
Then: The error is caught and logged as a warning
And: The `unifi_state` variable is set to an empty string
And: Test execution continues without failing

---

### Requirement: Cloudflare State Import

The test_integration function SHALL import Cloudflare Terraform state before cleanup destruction.

#### Scenario: Import state before Cloudflare destroy
Given: Phase 5 (cleanup) is executing
And: The `cloudflare_state` variable is not empty
When: Creating the Cloudflare cleanup container
Then: The state file is written to `/module/terraform.tfstate` using `container.with_new_file()`
And: `terraform init` is executed to initialize providers
And: `terraform destroy -auto-approve` uses the imported state

#### Scenario: Skip state import when state is empty
Given: Phase 5 (cleanup) is executing
And: The `cloudflare_state` variable is empty (export failed or not attempted)
When: Creating the Cloudflare cleanup container
Then: No state file is written
And: `terraform init` is executed
And: `terraform destroy` uses configuration-based destruction (fallback)

#### Scenario: State import with error handling
Given: Phase 5 (cleanup) is executing
And: The `cloudflare_state` variable contains state data
When: State import is attempted
And: An error occurs writing the state file
Then: The error is caught and logged as a warning
And: Cleanup continues without state (config-based fallback)

---

### Requirement: UniFi State Import

The test_integration function SHALL import UniFi Terraform state before cleanup destruction.

#### Scenario: Import state before UniFi destroy
Given: Phase 5 (cleanup) is executing
And: The `unifi_state` variable is not empty
When: Creating the UniFi cleanup container
Then: The state file is written to `/module/terraform.tfstate` using `container.with_new_file()`
And: `terraform init` is executed to initialize providers
And: `terraform destroy -auto-approve` uses the imported state

#### Scenario: Skip state import when state is empty
Given: Phase 5 (cleanup) is executing
And: The `unifi_state` variable is empty (export failed or not attempted)
When: Creating the UniFi cleanup container
Then: No state file is written
And: `terraform init` is executed
And: `terraform destroy` uses configuration-based destruction (fallback)

---

### Requirement: State Persistence Status in Test Report

The test_integration function SHALL include state persistence status in the test report.

#### Scenario: Show state persistence in report header
Given: The test report is being generated
When: Displaying initial test information
Then: The report includes "State Persistence: enabled"
And: This appears after "Test MAC Address" line

#### Scenario: Show state export status in report
Given: State export is attempted for Cloudflare
When: Export completes successfully
Then: The report includes "  ✓ Cloudflare state exported (X bytes)"

#### Scenario: Show state export failure in report
Given: State export is attempted for Cloudflare
When: Export fails
Then: The report includes "  ⚠ Cloudflare state export failed: {error_message}"

#### Scenario: Show cleanup method in cleanup summary
Given: Cleanup phase completes
When: Generating cleanup summary
Then: The report indicates state-based or config-based cleanup:
  - "State-based cleanup: ✓" when state was used
  - "Config-based cleanup: ✓" when config was used (fallback)

---

### Requirement: Backward Compatibility

The state persistence feature SHALL be fully backward compatible.

#### Scenario: Existing calls without state persistence
Given: Existing code calls `test_integration`
When: The function executes
Then: State export is attempted automatically
And: If state export fails, cleanup falls back to config-based
And: No new parameters are required

#### Scenario: Graceful degradation
Given: State export fails for both providers
When: Cleanup phase executes
Then: Both cleanups use config-based destruction
And: The test report indicates config-based cleanup was used
And: All resources are still cleaned up (if destroy succeeds)

---

## MODIFIED Requirements

### Requirement: Cleanup Container Creation

The cleanup container creation SHALL support optional Terraform state file injection for state-based resource destruction.

**Original**: Create cleanup containers with config files only.

**Modified**: Create cleanup containers with config files AND optional state files.

#### Scenario: Cloudflare cleanup container with state
Given: The `cloudflare_state` variable contains state data
When: Creating the Cloudflare cleanup container
Then: The container is created with:
  - Cloudflare config at `/workspace/cloudflare.json`
  - Terraform module at `/module`
  - State file at `/module/terraform.tfstate` (if state exists)
  - Required environment variables
  - Required secret variables

#### Scenario: UniFi cleanup container with state
Given: The `unifi_state` variable contains state data
When: Creating the UniFi cleanup container
Then: The container is created with:
  - UniFi config at `/workspace/unifi.json`
  - Terraform module at `/module`
  - State file at `/module/terraform.tfstate` (if state exists)
  - Required environment variables
  - Required secret variables
