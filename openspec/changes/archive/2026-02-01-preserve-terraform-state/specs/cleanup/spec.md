## MODIFIED Requirements

### Requirement: Cloudflare Cleanup Container

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

### Requirement: UniFi Cleanup Container

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
