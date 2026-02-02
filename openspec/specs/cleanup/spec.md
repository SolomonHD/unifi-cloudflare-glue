# Cleanup Specification

## Capability: Real Resource Cleanup

This capability implements actual resource destruction via `terraform destroy` in the integration test cleanup phase.

---

## ADDED Requirements

### Requirement: Cloudflare Cleanup Container

The cleanup phase SHALL create a properly configured Terraform container for Cloudflare resource destruction.

#### Scenario: Cloudflare cleanup container creation
Given: The test_integration function is in the cleanup phase
And: The cloudflare_json configuration is available
When: Creating the Cloudflare cleanup container
Then: A Terraform container is created from hashicorp/terraform:{terraform_version}
And: The Cloudflare Tunnel Terraform module is mounted at /module
And: The cloudflare.json config is written to /workspace/cloudflare.json
And: All required environment variables are set:
  - TF_VAR_cloudflare_account_id
  - TF_VAR_zone_name
  - TF_VAR_config_file
And: The Cloudflare token is set as a secret variable TF_VAR_cloudflare_token
And: The working directory is set to /module

#### Scenario: Cloudflare terraform destroy execution
Given: The Cloudflare cleanup container is configured
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed
Then: The Cloudflare tunnel is destroyed
And: The Cloudflare DNS record is deleted
And: cleanup_status["cloudflare"] is set to "success"
And: The report includes "✓ Destroyed tunnel: {tunnel_name}"
And: The report includes "✓ Deleted DNS record: {test_hostname}"

### Requirement: UniFi Cleanup Container

The cleanup phase SHALL create a properly configured Terraform container for UniFi resource destruction.

#### Scenario: UniFi cleanup container creation
Given: The test_integration function is in the cleanup phase
And: The unifi_json configuration is available
When: Creating the UniFi cleanup container
Then: A Terraform container is created from hashicorp/terraform:{terraform_version}
And: The UniFi DNS Terraform module is mounted at /module
And: The unifi.json config is written to /workspace/unifi.json
And: All required environment variables are set:
  - TF_VAR_unifi_url
  - TF_VAR_api_url
  - TF_VAR_config_file
And: UniFi authentication is set as secrets (API key OR username/password)
And: The working directory is set to /module

#### Scenario: UniFi terraform destroy execution
Given: The UniFi cleanup container is configured
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed
Then: The UniFi DNS records are deleted
And: cleanup_status["unifi"] is set to "success"
And: The report includes "✓ Deleted UniFi DNS records"

### Requirement: Cleanup Error Handling

Cleanup errors SHALL be caught and logged without preventing other cleanup operations or masking original test errors.

#### Scenario: Cloudflare cleanup failure handling
Given: The Cloudflare cleanup is being executed
When: An exception occurs during destroy
Then: The exception is caught
And: cleanup_status["cloudflare"] is set to "failed: {error_message}"
And: The report includes "✗ Failed to cleanup Cloudflare: {error_message}"
And: The report includes "(Resources may need manual cleanup)"
And: The error does not prevent UniFi cleanup from executing

#### Scenario: UniFi cleanup failure handling
Given: The UniFi cleanup is being executed
When: An exception occurs during destroy
Then: The exception is caught
And: cleanup_status["unifi"] is set to "failed: {error_message}"
And: The report includes "✗ Failed to cleanup UniFi: {error_message}"
And: The error does not mask any original test errors

#### Scenario: Resource already deleted handling
Given: The cleanup is being executed
When: Terraform destroy runs for resources that no longer exist
Then: The operation completes without error
And: cleanup_status is set to "success"
And: The report indicates successful cleanup

### Requirement: State File Cleanup Documentation

The cleanup phase SHALL document that Terraform state is container-local and automatically cleaned up.

#### Scenario: Container-local state documentation
Given: The cleanup phase is executing
When: State file cleanup is performed
Then: cleanup_status["state_files"] is set to "success"
And: The report includes "✓ Terraform state is container-local (automatically cleaned)"
And: The report notes that no manual state file cleanup is needed

### Requirement: Cleanup Summary Report

The cleanup phase SHALL generate a summary showing the status of all cleanup operations with appropriate warnings.

#### Scenario: Successful cleanup summary
Given: All cleanup operations completed successfully
When: The cleanup summary is generated
Then: The report includes a "CLEANUP SUMMARY" section
And: The summary shows:
  - Cloudflare: success
  - UniFi: success
  - State Files: success
And: No warning messages are displayed

#### Scenario: Failed cleanup summary
Given: One or more cleanup operations failed
When: The cleanup summary is generated
Then: The report includes a "CLEANUP SUMMARY" section
And: The summary shows the actual status for each component
And: A warning is displayed: "⚠ WARNING: Some resources may not have been cleaned up!"
And: The report includes: "Please verify manually in Cloudflare and UniFi dashboards."

#### Scenario: Cleanup skipped summary
Given: Cleanup is disabled (cleanup=false)
When: The cleanup phase is reached
Then: The report includes "PHASE 5: Cleanup SKIPPED (cleanup=false)"
And: The report includes "WARNING: Resources may still exist!"
And: cleanup_status shows all components as "skipped"

---

## Implementation Notes

### Container Separation
- Cloudflare and UniFi cleanup must use separate containers to avoid conflicts
- Each container has its own Terraform state (local backend)

### Execution Order
1. Cloudflare cleanup first (reverse order of creation)
2. UniFi cleanup second
3. State file documentation last

### Error Handling Strategy
- Try/except blocks around each cleanup operation
- Errors are logged but not re-raised
- Both cleanup operations are attempted even if one fails
- Original test errors are preserved in the finally block

### Reference Pattern
Follow the same pattern as the destroy() function (lines 431-623):
- Container creation with from_()
- Module mounting with with_directory()
- Config writing with with_new_file()
- Environment setup with with_env_variable() and with_secret_variable()
- Execution with with_exec(["terraform", "init"]) and with_exec(["terraform", "destroy", "-auto-approve"])

---

## MODIFIED Requirements

### Requirement: Cloudflare Cleanup Container (State Mount Fix)

The cleanup phase SHALL create a properly configured Terraform container for Cloudflare resource destruction that includes the preserved state file from the apply phase.

#### Scenario: Cloudflare cleanup container creation with state
Given: The test_integration function is in the cleanup phase
And: The cloudflare_json configuration is available
And: The cloudflare_state_dir containing terraform.tfstate is available
When: Creating the Cloudflare cleanup container
Then: A Terraform container is created from hashicorp/terraform:{terraform_version}
And: The Cloudflare Tunnel Terraform module is mounted at /module
And: The cloudflare.json config is written to /workspace/cloudflare.json
And: The preserved state file is mounted at /module/terraform.tfstate from cloudflare_state_dir
And: All required environment variables are set:
  - TF_VAR_cloudflare_account_id
  - TF_VAR_zone_name
  - TF_VAR_config_file
And: The Cloudflare token is set as a secret variable TF_VAR_cloudflare_token
And: The working directory is set to /module

#### Scenario: Cloudflare terraform destroy with state
Given: The Cloudflare cleanup container is configured with the preserved state file
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed
Then: Terraform reads the state file at /module/terraform.tfstate
And: Terraform identifies the resources to destroy from the state
And: The Cloudflare tunnel is destroyed
And: The Cloudflare DNS record is deleted
And: cleanup_status["cloudflare"] is set to "success"
And: The report includes "✓ Destroyed tunnel: {tunnel_name}"
And: The report includes "✓ Deleted DNS record: {test_hostname}"

#### Scenario: Cloudflare terraform destroy without state file
Given: The cloudflare_state_dir is None or empty (state export failed)
When: Creating the Cloudflare cleanup container
Then: The container is created without mounting a state file
And: Terraform destroy executes without prior state
And: The report includes a warning: "⚠ No state file available for Cloudflare cleanup"
And: Manual cleanup instructions are provided

---

### Requirement: UniFi Cleanup Container (State Mount Fix)

The cleanup phase SHALL create a properly configured Terraform container for UniFi resource destruction that includes the preserved state file from the apply phase.

#### Scenario: UniFi cleanup container creation with state
Given: The test_integration function is in the cleanup phase
And: The unifi_json configuration is available
And: The unifi_state_dir containing terraform.tfstate is available
When: Creating the UniFi cleanup container
Then: A Terraform container is created from hashicorp/terraform:{terraform_version}
And: The UniFi DNS Terraform module is mounted at /module
And: The unifi.json config is written to /workspace/unifi.json
And: The preserved state file is mounted at /module/terraform.tfstate from unifi_state_dir
And: All required environment variables are set:
  - TF_VAR_unifi_url
  - TF_VAR_api_url
  - TF_VAR_config_file
And: UniFi authentication is set as secrets (API key OR username/password)
And: The working directory is set to /module

#### Scenario: UniFi terraform destroy with state
Given: The UniFi cleanup container is configured with the preserved state file
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed
Then: Terraform reads the state file at /module/terraform.tfstate
And: Terraform identifies the resources to destroy from the state
And: The UniFi DNS records are deleted
And: cleanup_status["unifi"] is set to "success"
And: The report includes "✓ Deleted UniFi DNS record: {unifi_hostname}"

#### Scenario: UniFi terraform destroy without state file
Given: The unifi_state_dir is None or empty (state export failed)
When: Creating the UniFi cleanup container
Then: The container is created without mounting a state file
And: Terraform destroy executes without prior state
And: The report includes a warning: "⚠ No state file available for UniFi cleanup"
And: Manual cleanup instructions are provided

---

### Requirement: State File Preservation

The test_integration function SHALL export and preserve Terraform state files after successful apply operations for use during cleanup.

#### Scenario: Cloudflare state export after apply
Given: Cloudflare terraform apply completed successfully
And: The cf_ctr container has a state file at /module/terraform.tfstate
When: The apply phase completes
Then: The state file is exported using cf_ctr.file("/module/terraform.tfstate")
And: The exported file is stored in a Directory: dagger.dag.directory().with_file("terraform.tfstate", state_file)
And: The cloudflare_state_dir variable is set to this directory
And: State export failures are caught and logged but do not fail the test

#### Scenario: UniFi state export after apply
Given: UniFi terraform apply completed successfully
And: The unifi_ctr container has a state file at /module/terraform.tfstate
When: The apply phase completes
Then: The state file is exported using unifi_ctr.file("/module/terraform.tfstate")
And: The exported file is stored in a Directory: dagger.dag.directory().with_file("terraform.tfstate", state_file)
And: The unifi_state_dir variable is set to this directory
And: State export failures are caught and logged but do not fail the test

#### Scenario: State export failure handling
Given: Terraform apply succeeded but state file export fails
When: Attempting to export the state file from the container
Then: The exception is caught and logged
And: The corresponding state_dir variable is set to None
And: The test continues without the state file
And: The cleanup phase receives None for the state directory
And: Manual cleanup instructions are provided in the report
