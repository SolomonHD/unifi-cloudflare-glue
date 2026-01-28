## ADDED Requirements

### Requirement: Terraform Module Structure

Each Terraform module SHALL follow a standard file structure with proper versioning and documentation.

#### Scenario: unifi-dns module structure
Given the `terraform/modules/unifi-dns/` directory exists
When the module scaffolding is complete
Then the following files SHALL exist:
  - `versions.tf` declaring Terraform >= 1.5.0 and unifi provider ~> 0.41
  - `main.tf` for resource definitions (may be empty initially)
  - `variables.tf` for input variables (may be empty initially)
  - `outputs.tf` for output values (may be empty initially)
  - `README.md` documenting module purpose and usage

#### Scenario: cloudflare-tunnel module structure
Given the `terraform/modules/cloudflare-tunnel/` directory exists
When the module scaffolding is complete
Then the following files SHALL exist:
  - `versions.tf` declaring Terraform >= 1.5.0 and cloudflare provider ~> 4.0
  - `main.tf` for resource definitions (may be empty initially)
  - `variables.tf` for input variables (may be empty initially)
  - `outputs.tf` for output values (may be empty initially)
  - `README.md` documenting module purpose and usage

### Requirement: Terraform Version Constraints

All Terraform modules SHALL declare appropriate version constraints for Terraform core and providers.

#### Scenario: unifi-dns versions.tf is valid
Given the `terraform/modules/unifi-dns/versions.tf` file exists
When validated with Terraform
Then it SHALL declare:
  - `required_version` of `>= 1.5.0`
  - `required_providers` containing `unifi` with `source = "paultyng/unifi"` and `version = "~> 0.41"`

#### Scenario: cloudflare-tunnel versions.tf is valid
Given the `terraform/modules/cloudflare-tunnel/versions.tf` file exists
When validated with Terraform
Then it SHALL declare:
  - `required_version` of `>= 1.5.0`
  - `required_providers` containing `cloudflare` with `source = "cloudflare/cloudflare"` and `version = "~> 4.0"`

### Requirement: Module Documentation

Each Terraform module SHALL have a README.md with standard sections.

#### Scenario: unifi-dns README exists
Given the `terraform/modules/unifi-dns/README.md` file exists
When the documentation is reviewed
Then it SHALL contain:
  - A heading with the module name
  - A brief description of the module's purpose
  - Placeholder sections for requirements, usage, inputs, and outputs

#### Scenario: cloudflare-tunnel README exists
Given the `terraform/modules/cloudflare-tunnel/README.md` file exists
When the documentation is reviewed
Then it SHALL contain:
  - A heading with the module name
  - A brief description of the module's purpose
  - Placeholder sections for requirements, usage, inputs, and outputs
