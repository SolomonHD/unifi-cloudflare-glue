# project-structure Specification

## Purpose
TBD - created by archiving change project-scaffolding. Update Purpose after archive.
## Requirements
### Requirement: Project Directory Layout

The project SHALL follow a stack-separation directory layout that separates Terraform infrastructure code, KCL configuration schemas, and example configurations.

#### Scenario: Monorepo structure exists
Given the project root directory
When the scaffolding is complete
Then the following directory structure SHALL exist:
  - `terraform/modules/` containing reusable Terraform modules
  - `kcl/` containing KCL schemas and generators
  - `examples/` containing example configurations
  - Root `README.md` with project documentation
  - Root `.gitignore` with appropriate exclusions

### Requirement: Gitignore Configuration

The project SHALL exclude sensitive files, generated artifacts, and local state from version control.

#### Scenario: Terraform files are excluded
Given the root `.gitignore` file exists
When Terraform state and local files are present
Then the following patterns SHALL be excluded:
  - `*.tfstate` and `*.tfstate.*` files
  - `.terraform/` directory
  - `.terraform.lock.hcl` (optional, per project preference)
  - `*.tfplan` files
  - `crash.log` and `crash.*.log`

#### Scenario: KCL artifacts are excluded
Given the root `.gitignore` file exists
When KCL build artifacts are generated
Then KCL build directories and temporary files SHALL be excluded

#### Scenario: Credential files are excluded
Given the root `.gitignore` file exists
When local credential or environment files exist
Then the following SHALL be excluded:
  - `.env` files
  - `*.pem`, `*.key` files
  - Any files containing `secret`, `credential`, or `password` in their names

