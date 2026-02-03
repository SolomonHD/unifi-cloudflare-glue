# Spec Delta: add-persistent-state-directory

## ADDED Requirements

### Requirement: Persistent Local State Directory Parameter

Deployment functions SHALL accept an optional `state_dir` parameter to enable persistent local Terraform state storage.

#### Scenario: User provides state directory for persistent storage
- **WHEN** user calls `deploy_cloudflare` with `--state-dir=./terraform-state`  
- **THEN** the function SHALL accept the directory and use it for state storage

#### Scenario: User omits state directory for ephemeral storage
- **WHEN** user calls `deploy_cloudflare` without `--state-dir`  
- **THEN** the function SHALL use container-local ephemeral state at `/module/terraform.tfstate`

### Requirement: Mutual Exclusion Validation

The system SHALL enforce mutual exclusion between persistent local state and remote backend configuration.

#### Scenario: User attempts to use both local state directory and remote backend
- **WHEN** user specifies both `--state-dir=./tf-state` and `--backend-type=s3`  
- **THEN** the function SHALL return an error message explaining mutual exclusion  
- **AND** the error message SHALL list all three valid state management modes

#### Scenario: User uses only remote backend
- **WHEN** user specifies `--backend-type=s3 --backend-config-file=./backend.hcl` without `--state-dir`  
- **THEN** validation SHALL pass and remote backend SHALL be used

#### Scenario: User uses only local state directory
- **WHEN** user specifies `--state-dir=./tf-state` without remote backend flags  
- **THEN** validation SHALL pass and persistent local state SHALL be used

#### Scenario: User provides neither (default ephemeral)
- **WHEN** user omits both `--state-dir` and remote backend flags  
- **THEN** validation SHALL pass and ephemeral state SHALL be used (default)

### Requirement: State Directory Mounting and Setup

When a state directory is provided, the system SHALL mount it and prepare it for Terraform operations.

#### Scenario: Mount state directory to container
- **WHEN** user provides `--state-dir=./terraform-state`  
- **THEN** the state directory SHALL be mounted at `/state` in the container  
- **AND** the mount SHALL be read-write to allow state persistence

#### Scenario: Copy module files to state directory
- **WHEN** Terraform module files exist at `/module` in the container  
- **AND** a state directory is mounted at `/state`  
- **THEN** all module files SHALL be copied from `/module/*` to `/state/`  
- **AND** the copy operation SHALL be logged in the report output

#### Scenario: Set working directory to state directory
- **WHEN** module files have been copied to `/state`  
- **THEN** the working directory SHALL be set to `/state`  
- **AND** this SHALL be reported in the deployment output

### Requirement: Error Message Clarity

Error messages for state configuration conflicts SHALL provide clear guidance on correct usage.

#### Scenario: Provide helpful error for conflicting state options
- **WHEN** user specifies both `--state-dir` and `--backend-type=s3`  
- **THEN** the error message SHALL explain the mutual exclusion constraint  
- **AND** the error message SHALL show the exact conflicting flags provided  
- **AND** the error message SHALL provide three example commands for each mode  
- **AND** the examples SHALL cover remote backend, persistent local, and ephemeral modes

### Requirement: Consistent Implementation Across Functions

All deployment and cleanup functions SHALL implement state directory support consistently.

#### Scenario: deploy-unifi supports state directory
- **WHEN** `deploy_unifi` function is called with `--state-dir=./tf-state`  
- **THEN** the state directory logic SHALL be applied identically to `deploy_cloudflare`

#### Scenario: deploy-cloudflare supports state directory
- **WHEN** `deploy_cloudflare` function is called with `--state-dir=./tf-state`  
- **THEN** state directory mounting, file copying, and working directory setup SHALL occur

#### Scenario: deploy orchestration function supports state directory
- **WHEN** `deploy` function is called with `--state-dir=./tf-state`  
- **THEN** the state directory SHALL be passed to both `deploy_unifi` and `deploy_cloudflare`  
- **AND** both phases SHALL use the same state directory

#### Scenario: destroy function supports state directory
- **WHEN** infrastructure was deployed with `--state-dir=./tf-state`  
- **AND** `destroy` function is called with the same `--state-dir=./tf-state`  
- **THEN** the function SHALL read state from the specified directory  
- **AND** cleanup operations SHALL use the existing state to identify resources

### Requirement: Working Directory Behavior

The working directory SHALL be set based on state storage mode.

#### Scenario: Working directory for ephemeral mode
- **WHEN** no `--state-dir` is provided (ephemeral mode)  
- **THEN** the working directory SHALL be set to `/module`  
- **AND** state SHALL be written to `/module/terraform.tfstate`

#### Scenario: Working directory for remote backend mode
- **WHEN** `--backend-type=s3` is provided (remote backend mode)  
- **THEN** the working directory SHALL be set to `/module`  
- **AND** state SHALL be written to the remote backend

#### Scenario: Working directory for persistent local mode
- **WHEN** `--state-dir=./tf-state` is provided  
- **THEN** the working directory SHALL be set to `/state`  
- **AND** state SHALL be written to `/state/terraform.tfstate`  
- **AND** module files SHALL exist at `/state/*.tf`

## MODIFIED Requirements

None - This is a new opt-in feature that preserves existing default behavior.

## REMOVED Requirements

None - This is an additive feature with no removals.
