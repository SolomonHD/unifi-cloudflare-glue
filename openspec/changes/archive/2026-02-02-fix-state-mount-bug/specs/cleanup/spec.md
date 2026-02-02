## MODIFIED Requirements

### Requirement: Cloudflare Cleanup Container (State Mount Fix)

The cleanup phase SHALL create a properly configured Terraform container for Cloudflare resource destruction that correctly mounts the preserved state file without overwriting module files.

#### Scenario: Cloudflare cleanup container creation with correct state mounting
Given: The test_integration function is in the cleanup phase
And: The cloudflare_json configuration is available
And: The cloudflare_state_dir containing terraform.tfstate is available
When: Creating the Cloudflare cleanup container
Then: A Terraform container is created from hashicorp/terraform:{terraform_version}
And: The Cloudflare Tunnel Terraform module is mounted at /module
And: The cloudflare.json config is written to /workspace/cloudflare.json
And: The state file is extracted from cloudflare_state_dir using .file("terraform.tfstate")
And: The extracted state file is mounted at /module/terraform.tfstate using .with_file()
And: The module files at /module remain intact (not overwritten)
And: All required environment variables are set:
  - TF_VAR_cloudflare_account_id
  - TF_VAR_zone_name
  - TF_VAR_config_file
And: The Cloudflare token is set as a secret variable TF_VAR_cloudflare_token
And: The working directory is set to /module
And: The report includes "✓ Cloudflare state file mounted for state-based destroy"

#### Scenario: Cloudflare terraform destroy with correctly mounted state
Given: The Cloudflare cleanup container is configured with the state file at /module/terraform.tfstate
And: The module files exist at /module
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed
Then: Terraform reads the state file at /module/terraform.tfstate
And: Terraform finds the module configuration files at /module
And: Terraform identifies the resources to destroy from the state
And: The Cloudflare tunnel is destroyed
And: The Cloudflare DNS record is deleted
And: cleanup_status["cloudflare"] is set to "success"
And: The report includes "✓ Destroyed tunnel: {tunnel_name}"
And: The report includes "✓ Deleted DNS record: {test_hostname}"

#### Scenario: Cloudflare state file mounting failure handling
Given: The cloudflare_state_dir is available
And: The cleanup container is being configured
When: Extracting or mounting the state file raises an exception
Then: The exception is caught
And: The report includes "⚠ Failed to mount Cloudflare state file: {error_message}"
And: cloudflare_state_dir is set to None
And: The cleanup continues without the state file
And: Terraform destroy executes without prior state

#### Scenario: Cloudflare terraform destroy without state file
Given: The cloudflare_state_dir is None (state export failed or mount failed)
When: Creating the Cloudflare cleanup container
Then: The container is created without attempting to mount a state file
And: The report includes "⚠ No state file available for Cloudflare cleanup"
And: Terraform destroy executes without prior state
And: Manual cleanup instructions are provided

---

### Requirement: UniFi Cleanup Container (State Mount Fix)

The cleanup phase SHALL create a properly configured Terraform container for UniFi resource destruction that correctly mounts the preserved state file without overwriting module files.

#### Scenario: UniFi cleanup container creation with correct state mounting
Given: The test_integration function is in the cleanup phase
And: The unifi_json configuration is available
And: The unifi_state_dir containing terraform.tfstate is available
When: Creating the UniFi cleanup container
Then: A Terraform container is created from hashicorp/terraform:{terraform_version}
And: The UniFi DNS Terraform module is mounted at /module
And: The unifi.json config is written to /workspace/unifi.json
And: The state file is extracted from unifi_state_dir using .file("terraform.tfstate")
And: The extracted state file is mounted at /module/terraform.tfstate using .with_file()
And: The module files at /module remain intact (not overwritten)
And: All required environment variables are set:
  - TF_VAR_unifi_url
  - TF_VAR_api_url
  - TF_VAR_config_file
And: UniFi authentication is set as secrets (API key OR username/password)
And: The working directory is set to /module
And: The report includes "✓ UniFi state file mounted for state-based destroy"

#### Scenario: UniFi terraform destroy with correctly mounted state
Given: The UniFi cleanup container is configured with the state file at /module/terraform.tfstate
And: The module files exist at /module
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed
Then: Terraform reads the state file at /module/terraform.tfstate
And: Terraform finds the module configuration files at /module
And: Terraform identifies the resources to destroy from the state
And: The UniFi DNS records are deleted
And: cleanup_status["unifi"] is set to "success"
And: The report includes "✓ Deleted UniFi DNS record: {unifi_hostname}"

#### Scenario: UniFi state file mounting failure handling
Given: The unifi_state_dir is available
And: The cleanup container is being configured
When: Extracting or mounting the state file raises an exception
Then: The exception is caught
And: The report includes "⚠ Failed to mount UniFi state file: {error_message}"
And: unifi_state_dir is set to None
And: The cleanup continues without the state file
And: Terraform destroy executes without prior state

#### Scenario: UniFi terraform destroy without state file
Given: The unifi_state_dir is None (state export failed or mount failed)
When: Creating the UniFi cleanup container
Then: The container is created without attempting to mount a state file
And: The report includes "⚠ No state file available for UniFi cleanup"
And: Terraform destroy executes without prior state
And: Manual cleanup instructions are provided
