## ADDED Requirements

### Requirement: Diagnostics commands section documents Dagger verification

The troubleshooting guide SHALL provide copy-paste ready commands for verifying Dagger installation and module functionality.

#### Scenario: User verifies Dagger installation
- **WHEN** user needs to verify Dagger is working correctly
- **THEN** documentation provides `dagger version` and `dagger call hello` commands with expected output examples

#### Scenario: User verifies module installation
- **WHEN** user needs to verify unifi-cloudflare-glue module is installed
- **THEN** documentation provides `dagger call -m unifi-cloudflare-glue --help` command with expected output

### Requirement: Diagnostics commands section documents Terraform verification

The troubleshooting guide SHALL provide commands for verifying Terraform installation and provider configuration.

#### Scenario: User verifies Terraform installation
- **WHEN** user needs to verify Terraform is installed and working
- **THEN** documentation provides `terraform version` command with expected output

#### Scenario: User verifies Terraform provider configuration
- **WHEN** user needs to verify provider credentials are configured
- **THEN** documentation provides `terraform providers` command to inspect provider configuration

### Requirement: Diagnostics commands section documents KCL verification

The troubleshooting guide SHALL provide commands for verifying KCL installation and validating configuration files.

#### Scenario: User verifies KCL installation
- **WHEN** user needs to verify KCL is installed
- **THEN** documentation provides `kcl version` command with expected output

#### Scenario: User validates KCL configuration
- **WHEN** user needs to validate KCL syntax without generating output
- **THEN** documentation provides `kcl run main.k` command with expected validation behavior

### Requirement: Diagnostics commands section documents network connectivity tests

The troubleshooting guide SHALL provide commands for testing network connectivity to UniFi Controller and Cloudflare API.

#### Scenario: User tests UniFi Controller connectivity
- **WHEN** user needs to verify network access to UniFi Controller
- **THEN** documentation provides `curl -k https://unifi.local:8443/status` command with expected responses

#### Scenario: User tests Cloudflare API connectivity
- **WHEN** user needs to verify Cloudflare API token is valid
- **THEN** documentation provides curl command to verify token with expected success response

### Requirement: Diagnostics commands section documents state backend verification

The troubleshooting guide SHALL provide commands for verifying access to Terraform state backends (S3, Azure, GCS).

#### Scenario: User verifies S3 backend access
- **WHEN** user needs to verify S3 backend is accessible
- **THEN** documentation provides `aws s3 ls s3://my-bucket/` command with expected output

#### Scenario: User verifies Azure backend access
- **WHEN** user needs to verify Azure storage backend is accessible
- **THEN** documentation provides `az storage blob list` command with expected output

#### Scenario: User verifies GCS backend access
- **WHEN** user needs to verify GCS backend is accessible
- **THEN** documentation provides `gsutil ls gs://my-bucket/` command with expected output

### Requirement: Each diagnostic command includes expected output

All diagnostic commands in the troubleshooting guide SHALL include example expected output to help users verify correct operation.

#### Scenario: User runs any diagnostic command
- **WHEN** user executes a diagnostic command from the documentation
- **THEN** the documentation shows example successful output so user can compare with their results
