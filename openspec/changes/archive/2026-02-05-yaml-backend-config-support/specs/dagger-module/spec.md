## ADDED Requirements

### Requirement: YAML backend config file support
The Dagger module SHALL accept YAML-formatted backend configuration files via the `--backend-config-file` parameter while maintaining backward compatibility with HCL files.

#### Scenario: YAML backend config provided to deploy function
- **WHEN** user calls `deploy` function with `--backend-config-file=backend.yaml`
- **THEN** system automatically converts YAML to Terraform backend config format and successfully initializes Terraform

#### Scenario: YAML backend config provided to plan function
- **WHEN** user calls `plan` function with `--backend-config-file=backend.yaml`
- **THEN** system automatically converts YAML to Terraform backend config format and successfully generates plan

#### Scenario: YAML backend config provided to destroy function
- **WHEN** user calls `destroy` function with `--backend-config-file=backend.yaml`
- **THEN** system automatically converts YAML to Terraform backend config format and successfully destroys infrastructure

#### Scenario: YAML backend config provided to get_tunnel_secrets function
- **WHEN** user calls `get_tunnel_secrets` function with `--backend-config-file=backend.yaml`
- **THEN** system automatically converts YAML to Terraform backend config format and successfully retrieves tunnel secrets

#### Scenario: HCL backend config still works
- **WHEN** user calls any function with `--backend-config-file=backend.hcl`
- **THEN** system processes file as HCL without conversion, maintaining existing behavior

### Requirement: YAML documentation in docstrings
The Dagger module functions SHALL include YAML usage examples in their docstrings to guide users on YAML backend configuration.

#### Scenario: Function docstring includes YAML example
- **WHEN** user runs `dagger functions` or views function help
- **THEN** docstring displays clear examples of using YAML backend config files

#### Scenario: YAML example shows vals integration pattern
- **WHEN** user views function documentation
- **THEN** documentation demonstrates how to use vals with YAML backend configs for secret injection
