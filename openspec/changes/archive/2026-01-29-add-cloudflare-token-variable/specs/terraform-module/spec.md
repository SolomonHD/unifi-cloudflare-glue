## ADDED Requirements

### Requirement: cloudflare_token Variable Declaration

The Terraform module SHALL declare a cloudflare_token variable for Cloudflare API authentication.

#### Scenario: Variable is properly declared
Given: The cloudflare-tunnel module's `variables.tf` file
When: Inspecting the file contents
Then: The file must contain a `cloudflare_token` variable declaration

#### Scenario: Variable is marked sensitive
Given: The `cloudflare_token` variable declaration
When: Reviewing the variable configuration
Then: The variable must have `sensitive = true` to prevent value logging

#### Scenario: Variable has clear documentation
Given: The `cloudflare_token` variable declaration
When: Reading the description
Then: The description must specify required permissions:
  - Zone:Read
  - DNS:Edit
  - Cloudflare Tunnel:Edit

#### Scenario: Variable is required
Given: The `cloudflare_token` variable declaration
When: Attempting to use the module without providing the token
Then: Terraform must require the variable (no default value)

### Requirement: HCL Formatting Compliance

The variable declaration SHALL follow Terraform HCL formatting conventions.

#### Scenario: Variable follows Terraform conventions
Given: The added `cloudflare_token` variable
When: Running `terraform fmt`
Then: No formatting changes are required
