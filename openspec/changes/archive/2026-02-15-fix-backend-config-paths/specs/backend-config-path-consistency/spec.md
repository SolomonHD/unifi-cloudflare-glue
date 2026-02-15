## MODIFIED Requirements

### Requirement: Backend config file paths are consistent
All Dagger module functions that mount and reference backend configuration files SHALL use consistent file paths and extensions.

#### Scenario: plan() function with remote backend
- **WHEN** the `plan()` function is called with a remote backend type and backend config file
- **THEN** the backend config file SHALL be mounted at `/root/.terraform/backend.tfbackend`
- **AND** the terraform init command SHALL reference `/root/.terraform/backend.tfbackend`

#### Scenario: get_tunnel_secrets() function with remote backend
- **WHEN** the `get_tunnel_secrets()` function is called with a remote backend type and backend config file
- **THEN** the backend config file SHALL be mounted at `/root/.terraform/backend.tfbackend`
- **AND** the terraform init command SHALL reference `/root/.terraform/backend.tfbackend`

#### Scenario: deploy_unifi() function with remote backend
- **WHEN** the `deploy_unifi()` function is called with a remote backend type and backend config file
- **THEN** the backend config file SHALL be mounted at `/root/.terraform/backend.tfbackend`
- **AND** the terraform init command SHALL reference `/root/.terraform/backend.tfbackend`

#### Scenario: deploy_cloudflare() function with remote backend
- **WHEN** the `deploy_cloudflare()` function is called with a remote backend type and backend config file
- **THEN** the backend config file SHALL be mounted at `/root/.terraform/backend.tfbackend`
- **AND** the terraform init command SHALL reference `/root/.terraform/backend.tfbackend`

#### Scenario: Consumer repository uses remote S3 backend
- **WHEN** a consumer repository calls the module with `--backend-type=s3` and `--backend-config-file=./s3-backend.hcl`
- **THEN** terraform init SHALL successfully read the backend configuration
- **AND** the deployment SHALL proceed without file not found errors
