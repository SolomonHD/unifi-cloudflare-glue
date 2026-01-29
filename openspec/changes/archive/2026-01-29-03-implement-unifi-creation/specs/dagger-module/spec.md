# Specification: Dagger Module - Real UniFi Resource Creation

## ADDED Requirements

### Requirement: Terraform Container Creation

The `test_integration` function SHALL create a Terraform container for UniFi deployment with the correct image and mounted directories.

#### Scenario: Container with Correct Image
Given the `terraform_version` parameter is set to "1.10.0"
When creating the Terraform container
Then the container uses image `hashicorp/terraform:1.10.0`

#### Scenario: Module Directory Mounted
Given the UniFi DNS module exists at `terraform/modules/unifi-dns`
When the container is configured
Then the module is mounted at `/module` in the container

#### Scenario: Config Directory Mounted
Given the UniFi JSON configuration is generated
When the container is configured
Then the config is mounted at `/workspace/unifi.json` in the container

---

### Requirement: Environment Variable Configuration

The Terraform container SHALL have all required environment variables set for the UniFi DNS module.

#### Scenario: UniFi URL Variable Set
Given the `unifi_url` parameter is "https://unifi.local:8443"
When configuring the container
Then `TF_VAR_unifi_url` is set to "https://unifi.local:8443"

#### Scenario: API URL Variable with Default
Given `api_url` is not provided
And `unifi_url` is "https://unifi.local:8443"
When configuring the container
Then `TF_VAR_api_url` is set to "https://unifi.local:8443"

#### Scenario: API URL Variable with Custom Value
Given `api_url` is "https://api.unifi.local:8443"
And `unifi_url` is "https://unifi.local:8443"
When configuring the container
Then `TF_VAR_api_url` is set to "https://api.unifi.local:8443"

#### Scenario: Config File Variable Set
Given the UniFi config is mounted at `/workspace/unifi.json`
When configuring the container
Then `TF_VAR_config_file` is set to "/workspace/unifi.json"

---

### Requirement: API Key Authentication

The container SHALL support authentication via UniFi API key passed as a secret.

#### Scenario: API Key Secret Configured
Given `unifi_api_key` is provided as a Secret
And `unifi_username` and `unifi_password` are not provided
When configuring authentication
Then `TF_VAR_unifi_api_key` is set as a secret variable
And the secret value is not logged

---

### Requirement: Username Password Authentication

The container SHALL support authentication via UniFi username and password passed as secrets.

#### Scenario: Username Password Secrets Configured
Given `unifi_username` and `unifi_password` are provided as Secrets
And `unifi_api_key` is not provided
When configuring authentication
Then `TF_VAR_unifi_username` is set as a secret variable
And `TF_VAR_unifi_password` is set as a secret variable
And the secret values are not logged

---

### Requirement: Terraform Init Execution

The function SHALL execute `terraform init` and handle success and failure cases.

#### Scenario: Successful Terraform Init
Given the container is properly configured
When `terraform init` is executed
Then the command completes successfully
And stdout is captured
And `report_lines` contains "✓ Terraform init completed"

#### Scenario: Failed Terraform Init
Given the container is configured but module is invalid
When `terraform init` is executed
And the command fails with `dagger.ExecError`
Then `report_lines` contains an error message
And `validation_results["unifi_error"]` is set
And an exception is raised to trigger cleanup

---

### Requirement: Terraform Apply Execution

The function SHALL execute `terraform apply -auto-approve` and handle success and failure cases.

#### Scenario: Successful Terraform Apply
Given `terraform init` completed successfully
When `terraform apply -auto-approve` is executed
Then the command completes successfully
And stdout is captured
And `report_lines` contains "✓ Created UniFi DNS records"
And `validation_results["unifi_dns"]` is set to "created"

#### Scenario: Failed Terraform Apply
Given `terraform init` completed successfully
When `terraform apply -auto-approve` is executed
And the command fails with `dagger.ExecError`
Then `report_lines` contains an error message with stderr
And `validation_results["unifi_error"]` is set to error details
And an exception is raised to trigger cleanup

---

### Requirement: Error Handling and Cleanup Triggering

Any failure during Phase 3 SHALL trigger the cleanup phase via exception raising.

#### Scenario: Error Triggers Cleanup
Given an error occurs during Phase 3 execution
When the error is caught
Then the error is logged to `report_lines`
And `validation_results` is updated with error details
And an exception is raised
And the `finally` block cleanup phase is triggered

---

### Requirement: Expected Failure Documentation

The code SHALL document that UniFi deployment may fail due to test MAC not existing in controller.

#### Scenario: Comment Documents Expected Failure
Given the code is implemented
When viewing Phase 3 section
Then a comment explains that test MAC `aa:bb:cc:dd:ee:ff` won't exist in real controllers
And this is documented as expected behavior

---

## MODIFIED Requirements

### Requirement: Phase 3 Implementation

Phase 3 of `test_integration` SHALL be modified to execute real Terraform commands instead of simulated messages.

#### Scenario: Replace Simulated Message
Given the current Phase 3 implementation
When the code is modified
Then the simulated success message is removed
And real Terraform container creation is added
And real Terraform init and apply are executed
And `validation_results` is properly updated

#### Scenario: Working Directory Set
Given the Terraform container is created
When configuring for execution
Then the working directory is set to `/module`

---

## Technical References

### Source Code Locations

| Element | File | Lines | Description |
|---------|------|-------|-------------|
| `test_integration` | `src/main/main.py` | 789-1130 | Main integration test function |
| Phase 3 (current) | `src/main/main.py` | 1019-1026 | Simulated UniFi creation to replace |
| `deploy_unifi()` | `src/main/main.py` | 113-220 | Reference implementation |
| UniFi DNS module | `terraform/modules/unifi-dns/` | - | Terraform module for UniFi DNS |

### Module Variables

| Variable | Source | Type | Required |
|----------|--------|------|----------|
| `unifi_url` | Function parameter | Environment | Yes |
| `api_url` | Function parameter (defaults to unifi_url) | Environment | No |
| `config_file` | Hardcoded `/workspace/unifi.json` | Environment | Yes |
| `unifi_api_key` | Secret parameter (optional) | Secret | Conditional |
| `unifi_username` | Secret parameter (optional) | Secret | Conditional |
| `unifi_password` | Secret parameter (optional) | Secret | Conditional |

### Dagger Patterns

```python
# Container creation
ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

# Directory mounting
ctr = ctr.with_directory("/module", tf_module)
ctr = ctr.with_directory("/workspace", config_dir)

# Environment variables
ctr = ctr.with_env_variable("TF_VAR_name", value)

# Secret variables
ctr = ctr.with_secret_variable("TF_VAR_secret", secret)

# Working directory
ctr = ctr.with_workdir("/module")

# Command execution with error handling
try:
    output = await ctr.with_exec(["terraform", "init"]).stdout()
except dagger.ExecError as e:
    # Handle error and raise
```
