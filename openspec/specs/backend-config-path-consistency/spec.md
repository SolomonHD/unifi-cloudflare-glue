## MODIFIED Requirements

### Requirement: Backend config file paths are consistent
All Dagger module functions that mount and reference backend configuration files SHALL use consistent file paths and extensions.

**Note**: This requirement was previously documented in the base spec but incorrectly implemented in `plan()` and `get_tunnel_secrets()` functions. This change fixes the implementation to match the spec.

#### Scenario: plan() function mounts backend config correctly
- **WHEN** the `plan()` function mounts a backend config file for the UniFi module (line 1106)
- **THEN** the file SHALL be mounted at `/root/.terraform/backend.tfbackend`
- **AND** when mounting for the Cloudflare module (line 1201), the file SHALL also be mounted at `/root/.terraform/backend.tfbackend`
- **AND** both mount paths SHALL match the path used in the terraform init command

#### Scenario: get_tunnel_secrets() function mounts backend config correctly
- **WHEN** the `get_tunnel_secrets()` function mounts a backend config file (line 2821)
- **THEN** the file SHALL be mounted at `/root/.terraform/backend.tfbackend`
- **AND** the mount path SHALL match the path used in the terraform init command (`-backend-config=/root/.terraform/backend.tfbackend`)

#### Scenario: All functions use consistent tfbackend extension
- **WHEN** any function mounts a backend config file
- **THEN** the mount path SHALL use the `.tfbackend` extension
- **AND** the init command reference SHALL use the same `.tfbackend` extension
- **AND** no function SHALL use the `.hcl` extension for mounted backend config files
