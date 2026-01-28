# terraform-root-module Specification

## Purpose
TBD - created by archiving change 010-example-homelab-media-stack. Update Purpose after archive.
## Requirements
### Requirement: Module Integration

The Terraform root module SHALL read KCL-generated JSON files and pass them to the appropriate provider modules.

#### Scenario: Consuming KCL output
Given KCL generates `unifi.json` and `cloudflare.json`
When Terraform applies the configuration
Then the root module must:
- Read unifi.json using `jsondecode(file(...))`
- Read cloudflare.json using `jsondecode(file(...))`
- Pass unifi data to `unifi-dns` module
- Pass cloudflare data to `cloudflare-tunnel` module

### Requirement: Provider Configuration

The Terraform root module SHALL configure both UniFi and Cloudflare providers with proper credentials.

#### Scenario: Multiple provider setup
Given both UniFi and Cloudflare providers are needed
When Terraform initializes
Then providers must be configured:
- UniFi provider with controller host, credentials
- Cloudflare provider with API token
- Provider versions pinned for reproducibility

### Requirement: Input Variables

The Terraform root module SHALL expose input variables for customizable deployment parameters.

#### Scenario: Configurable deployment
Given users have different environments
When they customize the deployment
Then variables must be available for:
- `unifi_controller_host`: UniFi controller hostname/IP
- `unifi_username`: UniFi username (sensitive)
- `unifi_password`: UniFi password (sensitive)
- `cloudflare_api_token`: Cloudflare API token (sensitive)
- `generated_files_path`: Path to KCL output directory

### Requirement: Output Values

The Terraform root module SHALL output information about created resources for verification.

#### Scenario: Deployment verification
Given users need to verify what was created
When Terraform apply completes
Then outputs must include:
- List of created UniFi DNS records
- Cloudflare tunnel information
- Configured tunnel names and hostnames

### Requirement: State Management

The Terraform root module SHALL include state management configuration examples.

#### Scenario: Production deployment preparation
Given users may use remote state
When they review the example
Then they must find:
- Commented example of remote state configuration
- Local state as default (for trying out)
- State file in .gitignore

### Requirement: Version Constraints

The Terraform root module SHALL specify version constraints for reproducible deployments.

#### Scenario: Reproducible deployments
Given provider versions change over time
When the example is used
Then version constraints must:
- Pin Terraform to ~> 1.5
- Pin UniFi provider to tested version
- Pin Cloudflare provider to tested version
- Document why versions were chosen

### Requirement: File Structure

The Terraform root module SHALL follow a standard file organization pattern.

#### Scenario: Organized Terraform code
Given the example should be easy to understand
When users explore the terraform directory
Then they must find:
- `main.tf`: Module instantiations and provider config
- `variables.tf`: All input variables
- `versions.tf`: Provider and Terraform version constraints
- `outputs.tf`: Output definitions
- `README.md`: Terraform-specific documentation
- `.terraform.lock.hcl`: Committed for reproducibility

