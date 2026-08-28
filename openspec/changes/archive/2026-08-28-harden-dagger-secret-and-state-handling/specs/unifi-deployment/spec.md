## MODIFIED Requirements

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
When the function runs Terraform with API-key authentication
Then the key is passed through Dagger's secret `UNIFI_API_KEY` provider environment variable
And when compatibility username/password authentication is selected the credentials use secret `UNIFI_USERNAME` and `UNIFI_PASSWORD` provider environment variables
And no credential is supplied through `TF_VAR_*` or another Terraform input variable
And secrets never appear in command line arguments, plans, reports, or logs

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
And includes summary of applied resources

#### Scenario: Deployment Failure
Given Terraform apply fails
When the function processes the error
Then it returns a failing result with non-secret Terraform error context
And provides context for troubleshooting

#### Scenario: Missing Configuration File
Given a source directory without `unifi.json`
When the function is called
Then it returns an error indicating the configuration file is missing
