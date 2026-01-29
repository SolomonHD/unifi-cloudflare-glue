# Spec: Cloudflare Deployment Function

## ADDED Requirements

### Requirement: deploy_cloudflare Function

The Dagger module SHALL provide a `deploy_cloudflare` function that deploys Cloudflare Tunnel configuration using Terraform with secure credential handling.

#### Scenario: Deploy Cloudflare with API Token
Given a valid source directory containing `cloudflare.json`
And a Cloudflare API token provided as a `dagger.Secret`
And a Cloudflare Account ID
And a DNS zone name
When the `deploy_cloudflare` function is called
Then it runs Terraform apply for the Cloudflare Tunnel module
And returns a success message with applied resources

#### Scenario: Terraform Container Environment
Given any valid input to `deploy_cloudflare`
When the function executes Terraform
Then it uses the official `hashicorp/terraform` container image
And mounts the source directory containing `cloudflare.json`
And mounts the Terraform module from `terraform/modules/cloudflare-tunnel/`
And sets the working directory to the module path

#### Scenario: Secret Injection via Environment Variables
Given a secret Cloudflare API token
When the function runs Terraform
Then the token is passed via `TF_VAR_cloudflare_token` environment variable
And the token never appears in command line arguments
And the token is never logged in output

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
And includes summary of applied resources (tunnel names, DNS records)

#### Scenario: Deployment Failure
Given Terraform apply fails
When the function processes the error
Then it returns a message starting with "✗ Failed"
And includes Terraform error output
And provides context for troubleshooting

#### Scenario: Missing Configuration File
Given a source directory without `cloudflare.json`
When the function is called
Then it returns an error indicating the configuration file is missing

---

### Requirement: Cloudflare Function Parameters

The `deploy_cloudflare` function SHALL accept all required parameters with proper types and documentation.

#### Scenario: Required Parameters
Given the function signature
Then it accepts these required parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `dagger.Directory` | Source directory containing cloudflare.json |
| `cloudflare_token` | `dagger.Secret` | Cloudflare API Token |
| `cloudflare_account_id` | `str` | Cloudflare Account ID |
| `zone_name` | `str` | DNS zone name (e.g., example.com) |

#### Scenario: Secret Parameter
Given the `cloudflare_token` parameter
Then it MUST be of type `dagger.Secret`
And it is a required parameter (no default)

#### Scenario: Parameter Documentation
Given any parameter of the function
When viewed via `dagger functions` or IDE
Then it displays descriptive documentation via `Annotated[type, Doc("...")]`

---

### Requirement: Cloudflare Error Handling

The `deploy_cloudflare` function SHALL handle errors gracefully with informative messages.

#### Scenario: Terraform Configuration Error
Given invalid Terraform configuration
When the function runs Terraform
Then it captures the error
And returns a message with "✗ Failed" prefix
And includes the Terraform error details

#### Scenario: Authentication Failure
Given an invalid Cloudflare API token
When the function runs Terraform
Then it captures the authentication error
And returns a clear message indicating authentication failed
And suggests checking the token without exposing the secret value

#### Scenario: Invalid Account ID
Given an invalid Cloudflare Account ID
When the function runs Terraform
Then it captures the error
And returns a message indicating the account ID is invalid
And suggests verifying the Account ID in Cloudflare dashboard

#### Scenario: Zone Not Found
Given a zone name that doesn't exist or isn't accessible
When the function runs Terraform
Then it captures the error
And returns a message indicating the zone was not found
And suggests checking zone name and token permissions

#### Scenario: Provider API Error
Given valid credentials but Cloudflare API unavailable
When the function runs Terraform
Then it captures the API error
And returns a message with connection details
And suggests checking network connectivity
