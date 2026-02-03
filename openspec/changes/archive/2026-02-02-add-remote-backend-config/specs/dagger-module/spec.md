# Spec Delta: add-remote-backend-config

## ADDED Requirements

### Requirement: Remote Backend Configuration Parameters

The deployment functions SHALL accept optional remote backend configuration parameters to enable persistent state management via Terraform backends (S3, Azure Blob Storage, GCS, Terraform Cloud, etc.).

#### Scenario: User specifies S3 backend
- **WHEN** user calls [`deploy_cloudflare`](../../../../src/main/main.py:263) with `--backend-type=s3` and `--backend-config-file=./s3-backend.hcl`
- **THEN** the function SHALL generate a `backend "s3" {}` block in `backend.tf` and use `terraform init -backend-config=./s3-backend.hcl` to configure the backend

#### Scenario: User uses default local backend
- **WHEN** user calls [`deploy_cloudflare`](../../../../src/main/main.py:263) without `--backend-type` parameter
- **THEN** the function SHALL use ephemeral container-local state (current behavior maintained for backward compatibility)

#### Scenario: User specifies Azure backend
- **WHEN** user calls [`deploy_unifi`](../../../../src/main/main.py:143) with `--backend-type=azurerm` and `--backend-config-file=./azurerm-backend.hcl`
- **THEN** the function SHALL generate a `backend "azurerm" {}` block in `backend.tf` and use `terraform init -backend-config=./azurerm-backend.hcl` to configure the backend

#### Scenario: User specifies Terraform Cloud backend
- **WHEN** user calls [`deploy`](../../../../src/main/main.py:342) with `--backend-type=remote` and `--backend-config-file=./remote-backend.hcl`
- **THEN** the function SHALL generate a `backend "remote" {}` block in `backend.tf` for both UniFi and Cloudflare deployments

### Requirement: Backend Configuration Validation

The deployment functions SHALL validate backend configuration parameters and provide clear error messages when parameters are incompatible or missing.

#### Scenario: Missing backend config file
- **WHEN** user calls [`deploy_cloudflare`](../../../../src/main/main.py:263) with `--backend-type=s3` but without `--backend-config-file`
- **THEN** the function SHALL return error: "✗ Failed: Backend type 's3' requires --backend-config-file" with usage example

#### Scenario: Backend config file provided without backend type
- **WHEN** user calls [`deploy_unifi`](../../../../src/main/main.py:143) with `--backend-config-file=./s3-backend.hcl` but `--backend-type=local` (default)
- **THEN** the function SHALL return error: "✗ Failed: --backend-config-file specified but backend_type is 'local'" with resolution instructions

#### Scenario: Invalid backend type
- **WHEN** user provides any backend type supported by Terraform (s3, azurerm, gcs, remote, http, consul, etc.)
- **THEN** the function SHALL accept it without validation (Terraform CLI will validate backend-specific configuration)

### Requirement: Backend Configuration File Mounting

The deployment functions SHALL mount user-provided backend configuration files into Terraform containers and pass them to `terraform init` via the `-backend-config` flag.

#### Scenario: Mount backend config file Successfully
- **WHEN** user provides a valid HCL file via `--backend-config-file` parameter
- **THEN** the function SHALL mount the file at `/root/.terraform/backend.hcl` in the Terraform container and execute `terraform init -backend-config=/root/.terraform/backend.hcl`

#### Scenario: Backend config file contains credentials
- **WHEN** backend configuration file references environment variables for credentials (e.g., AWS_ACCESS_KEY_ID, ARM_CLIENT_ID)
- **THEN** the function SHALL NOT modify or inject credentials (user must set environment variables in their execution context)

### Requirement: Dynamic Backend Block Generation

The deployment functions SHALL dynamically generate a `backend.tf` file containing an empty backend configuration block when a remote backend type is specified.

#### Scenario: Generate S3 backend block
- **WHEN** user specifies `--backend-type=s3`
- **THEN** the function SHALL create `/module/backend.tf` with content:
```hcl
terraform {
  backend "s3" {}
}
```

#### Scenario: Local backend does not generate backend block
- **WHEN** user uses default `backend_type="local"` or explicitly sets `--backend-type=local`
- **THEN** the function SHALL NOT generate a `backend.tf` file (default Terraform local state behavior)

### Requirement: Destroy Function Backend Consistency

The `destroy` function SHALL use the same backend configuration as the corresponding `deploy` to ensure it can access the correct state file for resource destruction.

#### Scenario: Destroy with remote backend
- **WHEN** user calls [`destroy`](../../../../src/main/main.py:486) with matching backend configuration used during deployment
- **THEN** the function SHALL access the remote state and successfully destroy all resources

#### Scenario: Destroy with mismatched backend
- **WHEN** resources were deployed with S3 backend but user calls destroy without backend parameters
- **THEN** Terraform SHALL fail with "No state found" or similar error (expected behavior - user must provide matching backend config)

### Requirement: Documentation and Examples

The project documentation SHALL include comprehensive backend configuration examples for common remote backends.

#### Scenario: S3 backend documentation
- **WHEN** user reads [`README.md`](../../../../README.md) "State Management" section
- **THEN** they SHALL find complete examples for S3 backend with bucket, key, region, encrypt, and dynamodb_table configuration

#### Scenario: Example backend configuration files
- **WHEN** user explores `examples/backend-configs/` directory
- **THEN** they SHALL find ready-to-use HCL files for S3, Azure Blob Storage, GCS, and Terraform Cloud with descriptive comments

#### Scenario: Security best practices documented
- **WHEN** user reads backend configuration documentation
- **THEN** they SHALL find guidance on using environment variables for credentials and avoiding hardcoded secrets in backend config files

### Requirement: Backward Compatibility

The addition of remote backend support SHALL maintain full backward compatibility with existing usage patterns.

#### Scenario: Existing deployment without backend parameters
- **WHEN** user runs existing deployment command without new backend parameters
- **THEN** the function SHALL behave identically to previous versions (ephemeral local state)

#### Scenario: All four deployment functions support backend configuration
- **WHEN** user needs remote backend support
- **THEN** all four functions ([`deploy_unifi`](../../../../src/main/main.py:143), [`deploy_cloudflare`](../../../../src/main/main.py:263), [`deploy`](../../../../src/main/main.py:342), [`destroy`](../../../../src/main/main.py:486)) SHALL have consistent backend configuration parameters and behavior
