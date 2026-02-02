## MODIFIED Requirements

### Requirement: Cloudflare Resource Creation

The Cloudflare resource creation phase SHALL export and preserve the Terraform state file after successful apply for use during cleanup.

#### Scenario: Cloudflare apply with state preservation
Given: The test_integration function is executing Phase 2 (Cloudflare resources)
And: The cf_ctr container is configured with Terraform
When: terraform apply -auto-approve completes successfully
Then: The function exports the state file using cf_file = await cf_ctr.file("/module/terraform.tfstate")
And: The exported file is wrapped in a Directory: cloudflare_state_dir = dagger.dag.directory().with_file("terraform.tfstate", cf_file)
And: The cloudflare_state_dir variable is available for the cleanup phase
And: The report includes "✓ Created tunnel: {tunnel_name}"
And: The report includes "✓ Created DNS record: {test_hostname}"

#### Scenario: Cloudflare state export failure handling
Given: The test_integration function is executing Phase 2 (Cloudflare resources)
And: terraform apply completed successfully
When: Attempting to export the state file from cf_ctr
And: The export operation raises an exception
Then: The exception is caught and logged
And: cloudflare_state_dir is set to None
And: The test continues with a warning: "⚠ Cloudflare state export failed, cleanup may require manual intervention"
And: The cleanup phase will receive None for the state directory

---

### Requirement: UniFi Resource Creation

The UniFi resource creation phase SHALL export and preserve the Terraform state file after successful apply for use during cleanup.

#### Scenario: UniFi apply with state preservation
Given: The test_integration function is executing Phase 3 (UniFi resources)
And: The unifi_ctr container is configured with Terraform
When: terraform apply -auto-approve completes successfully
Then: The function exports the state file using unifi_file = await unifi_ctr.file("/module/terraform.tfstate")
And: The exported file is wrapped in a Directory: unifi_state_dir = dagger.dag.directory().with_file("terraform.tfstate", unifi_file)
And: The unifi_state_dir variable is available for the cleanup phase
And: The report includes "✓ Created UniFi DNS record: {unifi_hostname}"

#### Scenario: UniFi state export failure handling
Given: The test_integration function is executing Phase 3 (UniFi resources)
And: terraform apply completed successfully
When: Attempting to export the state file from unifi_ctr
And: The export operation raises an exception
Then: The exception is caught and logged
And: unifi_state_dir is set to None
And: The test continues with a warning: "⚠ UniFi state export failed, cleanup may require manual intervention"
And: The cleanup phase will receive None for the state directory

---

### Requirement: Variable Scope for State Preservation

The test_integration function SHALL maintain state directory variables in scope through the finally block for cleanup access.

#### Scenario: State variables in try-finally scope
Given: The test_integration function has started execution
When: The function enters the try block
Then: cloudflare_state_dir and unifi_state_dir variables are initialized as None
And: These variables are updated after successful state exports
And: The variables remain in scope for the finally block cleanup phase

#### Scenario: State variables available for cleanup
Given: The test has completed (success or failure)
When: The finally block begins cleanup
Then: cloudflare_state_dir contains either a Directory with the state file or None
And: unifi_state_dir contains either a Directory with the state file or None
And: The cleanup phase uses these variables to mount state files
