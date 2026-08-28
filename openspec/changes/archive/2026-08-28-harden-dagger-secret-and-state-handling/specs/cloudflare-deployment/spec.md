## MODIFIED Requirements

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
Then the token is passed through Dagger's secret `CLOUDFLARE_API_TOKEN` environment variable
And the token is not supplied through `TF_VAR_*` or another Terraform input variable
And the token never appears in command line arguments, plans, reports, or logs

#### Scenario: Terraform Init Execution
Given the Terraform container is prepared
When the function executes
Then it runs `terraform init` before apply
And handles init failures with clear error messages

#### Scenario: Terraform Apply Execution
Given `terraform init` succeeds
When the function proceeds with deployment
Then it runs `terraform apply -auto-approve`
And captures sanitized stdout and stderr for status reporting

#### Scenario: Deployment Success
Given Terraform apply completes successfully
When the function processes the result
Then it returns a message starting with "✓ Success"
And includes summary of applied resources (tunnel names, DNS records)

#### Scenario: Deployment Failure
Given Terraform apply fails
When the function processes the error
Then it returns a failing result with non-secret Terraform error context
And provides context for troubleshooting

#### Scenario: Missing Configuration File
Given a source directory without `cloudflare.json`
When the function is called
Then it returns an error indicating the configuration file is missing
