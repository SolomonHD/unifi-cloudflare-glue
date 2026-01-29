## ADDED Requirements

### Requirement: Real Cloudflare Resource Creation in Integration Tests

The integration test SHALL create actual Cloudflare resources via Terraform execution rather than simulating success messages.

#### Scenario: Terraform container setup
Given a running integration test with generated Cloudflare config JSON
When Phase 2 (Cloudflare resource creation) begins
Then the system SHALL create a container from `hashicorp/terraform:{terraform_version}` image
And mount the Cloudflare Tunnel Terraform module at `/module`
And write the Cloudflare config JSON to `/workspace/cloudflare.json`

#### Scenario: Environment variable configuration
Given a Terraform container for Cloudflare deployment
When the container is configured
Then the system SHALL set `TF_VAR_cloudflare_account_id` to the provided account ID
And set `TF_VAR_zone_name` to the provided zone name
And set `TF_VAR_config_file` to `/workspace/cloudflare.json`
And pass the Cloudflare token as a secret via `TF_VAR_cloudflare_token`

#### Scenario: Terraform init execution
Given a configured Terraform container
When Phase 2 proceeds to initialization
Then the system SHALL execute `terraform init` in the container
And capture the command output
And report "✓ Terraform init completed" on success

#### Scenario: Terraform apply execution
Given a successfully initialized Terraform container
When Phase 2 proceeds to resource creation
Then the system SHALL execute `terraform apply -auto-approve`
And capture the command output
And report "✓ Created tunnel: {tunnel_name}" on success
And report "✓ Created DNS record: {test_hostname}" on success
And set `validation_results["cloudflare_tunnel"]` to "created"
And set `validation_results["cloudflare_dns"]` to "created"

#### Scenario: Terraform init failure handling
Given a Terraform container configuration
When `terraform init` fails with an error
Then the system SHALL catch the `dagger.ExecError` exception
And append "✗ Terraform init failed: {error_message}" to the report
And re-raise the exception to trigger the cleanup phase

#### Scenario: Terraform apply failure handling
Given a successfully initialized Terraform container
When `terraform apply` fails with an error
Then the system SHALL catch the `dagger.ExecError` exception
And append "✗ Terraform apply failed: {error_message}" to the report
And store error details in `validation_results["cloudflare_error"]`
And re-raise the exception to trigger the cleanup phase

#### Scenario: Container working directory
Given a Terraform container with mounted module
When executing Terraform commands
Then the working directory SHALL be set to `/module`
To ensure Terraform finds the correct module configuration

#### Scenario: Reference pattern alignment
Given the existing `deploy_cloudflare()` function implementation
When implementing Phase 2 resource creation
Then the implementation SHALL follow the same patterns as `deploy_cloudflare()` (lines 222-298)
Including container creation, mounting, environment setup, and error handling
