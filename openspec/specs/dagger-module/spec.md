# Spec: Dagger Module

## Overview

This specification defines the requirements for the Dagger Python module in the unifi-cloudflare-glue project, including scaffolding, deployment functions, and integration testing capabilities.

## ADDED Requirements

### Requirement: Dagger Module Manifest

The Dagger module SHALL have a `dagger.json` manifest file at the repository root with correct configuration.

#### Scenario: dagger.json exists at repository root
Given: The repository root directory exists
When: Dagger module initialization is complete
Then: A `dagger.json` file exists at the repository root with:
  - `name`: "unifi-cloudflare-glue"
  - `engineVersion`: "v0.19.7" or higher
  - `sdk.source`: "python"

### Requirement: Python Project Configuration

The Dagger module SHALL have a `pyproject.toml` with the correct build system and dependencies.

#### Scenario: pyproject.toml with uv_build backend
Given: The Dagger module requires Python tooling
When: The project configuration is created
Then: A `pyproject.toml` file exists with:
  - `[build-system]` using `uv_build>=0.8.4,<0.9.0`
  - `[project].name`: "main" (required by Dagger)
  - `[project].requires-python`: ">=3.11"
  - `[tool.uv.sources]` with dagger-io pointing to local SDK path
  - `[project].dependencies` includes "dagger-io"

### Requirement: Python Module Structure

The Dagger module SHALL have a standard Python package structure under `src/unifi_cloudflare_glue/`.

#### Scenario: src/unifi_cloudflare_glue directory exists
Given: The Dagger module requires Python source files
When: The module structure is created
Then: The directory `src/unifi_cloudflare_glue/` exists with:
  - `__init__.py` (empty or with minimal exports)
  - `main.py` containing the Dagger class definition

### Requirement: Dagger Class Skeleton

The Dagger module SHALL have a properly named class decorated with `@object_type` in `main.py`.

#### Scenario: UnifiCloudflareGlue class in main.py
Given: The Python module structure exists
When: The main.py file is created
Then: The file contains:
  ```python
  """Dagger module for unifi-cloudflare-glue"""
  
  import dagger
  from dagger import function, object_type
  
  @object_type
  class UnifiCloudflareGlue:
      """Dagger module for managing hybrid DNS infrastructure"""
      
      @function
      def hello(self) -> str:
          """Placeholder function for module verification"""
          return "Hello from unifi-cloudflare-glue!"
  ```

### Requirement: Gitignore Updates

The repository `.gitignore` SHALL be updated to exclude Dagger and Python artifacts.

#### Scenario: .gitignore includes Dagger artifacts
Given: The repository has an existing `.gitignore` file
When: The Dagger module scaffolding is complete
Then: The `.gitignore` file contains entries for:
  - `/sdk/` (Dagger auto-generated SDK)
  - `__pycache__/` (Python cache)
  - `*.py[cod]` (Python bytecode)
  - `*.egg-info/` (Python package metadata)
  - `.venv/` (Python virtual environment)
  - `/.env` (Environment files)

### Requirement: Module Verification

The Dagger module SHALL be loadable and display its functions when running `dagger functions`.

#### Scenario: dagger functions shows the module
Given: All scaffolding files are in place
When: The command `dagger functions` is executed from the repository root
Then: The output shows:
  - Class name: `UnifiCloudflareGlue`
  - Function: `hello`
  - No errors or warnings about missing files

### Requirement: Terraform Container Creation for UniFi

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

### Requirement: Environment Variable Configuration for UniFi

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

### Requirement: API Key Authentication for UniFi

The container SHALL support authentication via UniFi API key passed as a secret.

#### Scenario: API Key Secret Configured
Given `unifi_api_key` is provided as a Secret
And `unifi_username` and `unifi_password` are not provided
When configuring authentication
Then `TF_VAR_unifi_api_key` is set as a secret variable
And the secret value is not logged

### Requirement: Username Password Authentication for UniFi

The container SHALL support authentication via UniFi username and password passed as secrets.

#### Scenario: Username Password Secrets Configured
Given `unifi_username` and `unifi_password` are provided as Secrets
And `unifi_api_key` is not provided
When configuring authentication
Then `TF_VAR_unifi_username` is set as a secret variable
And `TF_VAR_unifi_password` is set as a secret variable
And the secret values are not logged

### Requirement: Terraform Init Execution for UniFi

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

### Requirement: Terraform Apply Execution for UniFi

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

### Requirement: Error Handling and Cleanup Triggering

Any failure during Phase 3 SHALL trigger the cleanup phase via exception raising.

#### Scenario: Error Triggers Cleanup
Given an error occurs during Phase 3 execution
When the error is caught
Then the error is logged to `report_lines`
And `validation_results` is updated with error details
And an exception is raised
And the `finally` block cleanup phase is triggered

### Requirement: Expected Failure Documentation

The code SHALL document that UniFi deployment may fail due to test MAC not existing in controller.

#### Scenario: Comment Documents Expected Failure
Given the code is implemented
When viewing Phase 3 section
Then a comment explains that test MAC `aa:bb:cc:dd:ee:ff` won't exist in real controllers
And this is documented as expected behavior

### Requirement: Cloudflare Tunnel Validation via API

The `test_integration` function SHALL query the Cloudflare API to verify that the tunnel was created successfully.

#### Scenario: Successful Tunnel Query
Given a Cloudflare tunnel was created in Phase 2 with name `tunnel-{test_id}`
When the validation phase queries the Cloudflare API for tunnels with matching name
Then the API returns a response with exactly one tunnel result
And `validation_results["cloudflare_tunnel"]` is set to `"validated"`
And the report shows `✓ Cloudflare tunnel validated: {tunnel_name}`

#### Scenario: Tunnel Not Found
Given a Cloudflare tunnel was expected to exist
When the validation phase queries the Cloudflare API
Then the API returns zero results for the tunnel name
And `validation_results["cloudflare_tunnel"]` is set to `"not_found"`
And the report shows `✗ Cloudflare tunnel not found: {tunnel_name}`

#### Scenario: Tunnel Validation Error
Given a Cloudflare tunnel validation is attempted
When the API query fails (network error, auth failure, etc.)
Then the exception is caught gracefully
And `validation_results["cloudflare_tunnel"]` is set to `"error: {message}"`
And the report shows `✗ Cloudflare tunnel validation failed: {message}`

### Requirement: Cloudflare DNS Record Validation via API

The function SHALL query the Cloudflare API to verify that DNS records were created successfully.

#### Scenario: Successful DNS Record Query
Given a Cloudflare DNS record was created in Phase 2 with hostname `{test_id}.{cloudflare_zone}`
When the validation phase first queries the zone ID by zone name
And then queries DNS records for the hostname using the zone ID
Then the API returns a response with exactly one DNS record result
And `validation_results["cloudflare_dns"]` is set to `"validated"`
And the report shows `✓ Cloudflare DNS validated: {test_hostname}`

#### Scenario: DNS Record Not Found
Given a Cloudflare DNS record was expected to exist
When the validation phase queries the DNS records API
Then the API returns zero results for the hostname
And `validation_results["cloudflare_dns"]` is set to `"not_found"`
And the report shows `✗ Cloudflare DNS not found: {test_hostname}`

#### Scenario: Zone Not Found
Given the Cloudflare zone name is queried
When the zone lookup returns no matching zone
Then `validation_results["cloudflare_dns"]` is set to `"zone_not_found"`
And the report shows `✗ Could not find zone: {cloudflare_zone}`

#### Scenario: DNS Validation Error
Given a Cloudflare DNS validation is attempted
When the API query fails (network error, auth failure, etc.)
Then the exception is caught gracefully
And `validation_results["cloudflare_dns"]` is set to `"error: {message}"`
And the report shows `✗ Cloudflare DNS validation failed: {message}`

### Requirement: Validation Container Setup

The function SHALL create a container with the necessary tools for API validation.

#### Scenario: Create Validation Container
Given the validation phase needs to make API calls
When the phase creates a container from `alpine/curl:latest`
And installs `jq` package for JSON parsing
Then the container is ready for Cloudflare API calls

#### Scenario: API Token Retrieval
Given the validation phase needs to authenticate API calls
When `await cloudflare_token.plaintext()` is called
Then the Cloudflare API token is obtained for use in curl commands

### Requirement: UniFi Resource Validation

The function SHALL validate UniFi resources based on Terraform apply results.

#### Scenario: UniFi Validation via Terraform Success
Given UniFi DNS records were created in Phase 3
When the validation phase checks `validation_results["unifi_dns"]`
And the value equals `"created"`
Then `validation_results["unifi_validation"]` is set to `"validated"`
And the report shows `✓ UniFi DNS validated (Terraform apply succeeded)`

#### Scenario: UniFi Validation Skipped
Given UniFi DNS records may not have been created
When the validation phase checks `validation_results["unifi_dns"]`
And the value is not `"created"`
Then `validation_results["unifi_validation"]` is set to `"skipped"`
And the report shows `○ UniFi DNS validation skipped (creation may have failed)`

### Requirement: Validation Summary Report

The function SHALL generate a summary of validation results.

#### Scenario: All Cloudflare Resources Validated
Given both tunnel and DNS validations succeeded
When the validation summary is generated
Then the report shows `VALIDATION SUMMARY: ✓ CLOUDFLARE RESOURCES VALIDATED`

#### Scenario: Some Resources Not Found
Given at least one Cloudflare validation failed
When the validation summary is generated
Then the report shows `VALIDATION SUMMARY: ✗ SOME RESOURCES NOT FOUND`
And details of which validations passed/failed are included

### Requirement: Cloudflare API Call Structure

The function SHALL construct proper Cloudflare API requests.

#### Scenario: Tunnel API Call
Given the validation phase queries for a tunnel
When the curl command is constructed
Then it uses GET method to `https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel`
And it includes query parameter `?name={tunnel_name}`
And it includes Authorization header with Bearer token
And it includes Content-Type header with value application/json

#### Scenario: Zone API Call
Given the validation phase needs a zone ID
When the curl command is constructed
Then it uses GET method to `https://api.cloudflare.com/client/v4/zones`
And it includes query parameter `?name={cloudflare_zone}`
And it includes Authorization header with Bearer token

#### Scenario: DNS Record API Call
Given the validation phase queries for a DNS record
When the curl command is constructed
Then it uses GET method to `https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records`
And it includes query parameter `?name={test_hostname}`
And it includes Authorization header with Bearer token

### Requirement: JSON Response Parsing

The function SHALL parse Cloudflare API responses to determine resource existence.

#### Scenario: Parse Tunnel Count
Given the tunnel API returns a JSON response
When the response is parsed with `jq '.result | length'`
Then a count of "1" indicates the tunnel exists
And a count of "0" indicates the tunnel was not found

#### Scenario: Parse Zone ID
Given the zone API returns a JSON response
When the response is parsed with `jq -r '.result[0].id'`
Then the zone ID is extracted for use in DNS queries
And a value of "null" indicates the zone was not found

#### Scenario: Parse DNS Record Count
Given the DNS record API returns a JSON response
When the response is parsed with `jq '.result | length'`
Then a count of "1" indicates the DNS record exists
And a count of "0" indicates the DNS record was not found

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

### Requirement: Phase 4 Implementation

Phase 4 of `test_integration` SHALL be modified to perform real API validation instead of fake validation.

#### Scenario: Replace Fake Validation
Given the current Phase 4 implementation (lines 1083-1105)
When the code is modified
Then the fake validation (setting `cf_validation = True`) is removed
And real Cloudflare API queries are added
And `validation_results` is properly updated based on API responses
And validation summary reflects actual resource state

#### Scenario: Maintain Report Format
Given the validation is performed
When the report lines are generated
Then the Phase 4 header is preserved
And individual validation results are reported
And the validation summary header format is preserved

## Technical References

### Source Code Locations

| Element | File | Lines | Description |
|---------|------|-------|-------------|
| `test_integration` | `src/main/main.py` | 789-1271 | Main integration test function |
| Phase 3 | `src/main/main.py` | 1019-1081 | UniFi resource creation |
| Phase 4 | `src/main/main.py` | 1083-1191 | Resource validation |
| `deploy_unifi()` | `src/main/main.py` | 113-220 | Reference for UniFi operations |
| `deploy_cloudflare()` | `src/main/main.py` | 223-298 | Reference for Cloudflare operations |
| UniFi DNS module | `terraform/modules/unifi-dns/` | - | Terraform module for UniFi DNS |
| Cloudflare Tunnel module | `terraform/modules/cloudflare-tunnel/` | - | Terraform module for Cloudflare |

### Module Variables

| Variable | Source | Type | Required |
|----------|--------|------|----------|
| `unifi_url` | Function parameter | Environment | Yes |
| `api_url` | Function parameter (defaults to unifi_url) | Environment | No |
| `config_file` | Hardcoded `/workspace/unifi.json` | Environment | Yes |
| `unifi_api_key` | Secret parameter (optional) | Secret | Conditional |
| `unifi_username` | Secret parameter (optional) | Secret | Conditional |
| `unifi_password` | Secret parameter (optional) | Secret | Conditional |

### Cloudflare API Endpoints

| Endpoint | Method | Path | Purpose |
|----------|--------|------|---------|
| List Tunnels | GET | `/accounts/{account_id}/cfd_tunnel?name={tunnel_name}` | Query tunnel by name |
| List Zones | GET | `/zones?name={cloudflare_zone}` | Get zone ID from name |
| List DNS Records | GET | `/zones/{zone_id}/dns_records?name={test_hostname}` | Query DNS record |

### Required API Token Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| Zone:Read | Zone | List zones to get zone ID |
| DNS Records:Read | Zone | Query DNS records |
| Cloudflare Tunnel:Read | Account | Query tunnel status |

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

# Validation container creation
validate_ctr = dagger.dag.container().from_("alpine/curl:latest")
validate_ctr = validate_ctr.with_exec(["apk", "add", "--no-cache", "jq"])

# API token retrieval
cf_token_plain = await cloudflare_token.plaintext()

# API call with curl
result = await validate_ctr.with_exec([
    "sh", "-c",
    f'curl -s -X GET "{api_url}" -H "Authorization: Bearer {token}"'
]).stdout()

# JSON parsing with jq
count = await validate_ctr.with_exec([
    "sh", "-c",
    f'echo \'{result}\' | jq \'.result | length\''
]).stdout()
```

## Constraints

1. **Module Location**: Dagger module must be at repository root for git-related functions to work properly
2. **Class Name**: Must match PascalCase conversion of module name: `unifi-cloudflare-glue` → `UnifiCloudflareGlue`
3. **Build System**: Must use `uv_build` (not hatchling/setuptools)
4. **Project Name**: Must be "main" in pyproject.toml (Dagger requirement)

---

## MODIFIED Requirements

### Requirement: Test Configuration Domain Parameter

The Dagger module SHALL support configurable UniFi domain in test configuration generation to ensure test DNS records use the correct FQDN matching the Cloudflare zone.

#### Scenario: Default domain behavior
Given: The `_generate_test_configs()` method is called with only the required parameters
When: The `unifi_domain` parameter is not provided (empty string)
Then: The UniFi configuration SHALL use the `cloudflare_zone` value for both device domain and default_domain

#### Scenario: Explicit domain override
Given: The `_generate_test_configs()` method is called with an explicit `unifi_domain` parameter
When: The `unifi_domain` parameter is provided with a non-empty value
Then: The UniFi configuration SHALL use the provided `unifi_domain` value for both device domain and default_domain

#### Scenario: Test integration passes correct domain
Given: The `test_integration()` function is executing
When: It calls `_generate_test_configs()` to create test configurations
Then: It SHALL pass the `cloudflare_zone` value as the `unifi_domain` parameter

#### Scenario: Backward compatibility
Given: Existing code calls `_generate_test_configs()` without the new parameter
When: The method is invoked with the legacy signature
Then: The method SHALL accept the call and default the domain to the cloudflare_zone value
