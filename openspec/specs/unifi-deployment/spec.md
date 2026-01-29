# Spec: UniFi Deployment Function

## ADDED Requirements

### Requirement: deploy_unifi Function

The Dagger module SHALL provide a `deploy_unifi` function that deploys UniFi DNS configuration using Terraform with secure credential handling.

#### Scenario: Deploy UniFi with API Key
Given a valid source directory containing `unifi.json`
And a UniFi Controller URL
And a UniFi API key provided as a `dagger.Secret`
When the `deploy_unifi` function is called with API key authentication
Then it runs Terraform apply for the UniFi DNS module
And returns a success message with applied resources

#### Scenario: Deploy UniFi with Username/Password
Given a valid source directory containing `unifi.json`
And a UniFi Controller URL
And UniFi username and password provided as `dagger.Secret` values
When the `deploy_unifi` function is called with username/password authentication
Then it runs Terraform apply for the UniFi DNS module
And returns a success message with applied resources

#### Scenario: Authentication Method Validation
Given a call to `deploy_unifi` with neither API key nor username/password
When the function validates parameters
Then it returns an error: "✗ Failed: Must provide either unifi_api_key OR both unifi_username and unifi_password"

#### Scenario: Conflicting Authentication Methods
Given a call to `deploy_unifi` with both API key AND username/password provided
When the function validates parameters
Then it returns an error: "✗ Failed: Cannot use both API key and username/password. Choose one authentication method."

#### Scenario: Terraform Container Environment
Given any valid input to `deploy_unifi`
When the function executes Terraform
Then it uses the official `hashicorp/terraform` container image
And mounts the source directory containing `unifi.json`
And mounts the Terraform module from `terraform/modules/unifi-dns/`
And sets the working directory to the module path

#### Scenario: Secret Injection via Environment Variables
Given secret values for UniFi authentication
When the function runs Terraform
Then secrets are passed via `TF_VAR_*` environment variables
And secrets never appear in command line arguments
And secrets are never logged in output

#### Scenario: Terraform Init Execution
Given the Terraform container is prepared
When the function executes
Then it runs `terraform init` before apply
And handles init failures with clear error messages

#### Scenario: Terraform Apply Execution
Given `terraform init` succeeds
When the function proceeds with deployment
Then it runs `terraform apply -auto-approve`
And captures stdout and stderr for status reporting

#### Scenario: Deployment Success
Given Terraform apply completes successfully
When the function processes the result
Then it returns a message starting with "✓ Success"
And includes summary of applied resources

#### Scenario: Deployment Failure
Given Terraform apply fails
When the function processes the error
Then it returns a message starting with "✗ Failed"
And includes Terraform error output
And provides context for troubleshooting

#### Scenario: Missing Configuration File
Given a source directory without `unifi.json`
When the function is called
Then it returns an error indicating the configuration file is missing

---

### Requirement: UniFi Function Parameters

The `deploy_unifi` function SHALL accept all required parameters with proper types and documentation.

#### Scenario: Required Parameters
Given the function signature
Then it accepts these required parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `dagger.Directory` | Source directory containing unifi.json |
| `unifi_url` | `str` | UniFi Controller URL |

#### Scenario: Optional API URL
Given the function signature
Then it accepts an optional `api_url` parameter of type `str`
And if not provided, it defaults to the value of `unifi_url`

#### Scenario: API Key Authentication Parameters
Given the function signature
Then it accepts an optional `unifi_api_key` parameter of type `dagger.Secret`
For API key authentication (preferred method)

#### Scenario: Username/Password Authentication Parameters
Given the function signature
Then it accepts optional parameters:
- `unifi_username` of type `dagger.Secret`
- `unifi_password` of type `dagger.Secret`
For username/password authentication

#### Scenario: Parameter Documentation
Given any parameter of the function
When viewed via `dagger functions` or IDE
Then it displays descriptive documentation via `Annotated[type, Doc("...")]`

---

### Requirement: UniFi Error Handling

The `deploy_unifi` function SHALL handle errors gracefully with informative messages.

#### Scenario: Terraform Configuration Error
Given invalid Terraform configuration
When the function runs Terraform
Then it captures the error
And returns a message with "✗ Failed" prefix
And includes the Terraform error details

#### Scenario: Authentication Failure
Given invalid credentials
When the function runs Terraform
Then it captures the authentication error
And returns a clear message indicating authentication failed
And suggests checking credentials without exposing secret values

#### Scenario: Provider API Error
Given valid credentials but UniFi API unavailable
When the function runs Terraform
Then it captures the API error
And returns a message with connection details
And suggests checking UniFi Controller availability
