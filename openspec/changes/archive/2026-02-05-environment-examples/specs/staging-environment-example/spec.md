## ADDED Requirements

### Requirement: Staging environment directory structure
The example SHALL provide a complete staging environment directory under `examples/staging-environment/` with KCL configuration, backend config, Makefile, README, .gitignore, and environment variable template.

#### Scenario: Complete directory exists
- **WHEN** user navigates to `examples/staging-environment/`
- **THEN** directory contains `README.md`, `kcl/main.k`, `backend.yaml`, `.env.example`, `Makefile`, and `.gitignore`

#### Scenario: Ready for team use
- **WHEN** user copies the staging-environment directory to their project
- **THEN** configuration supports multiple team members with shared state

### Requirement: Remote state backend
The staging environment SHALL use remote state backend (S3) for team collaboration with state locking.

#### Scenario: Backend configuration provided
- **WHEN** user examines `backend.yaml`
- **THEN** file configures S3 backend with bucket and lockfile path

#### Scenario: State is persisted remotely
- **WHEN** team member runs deployment
- **THEN** Terraform state is stored in S3 and accessible to other team members

### Requirement: State locking for team collaboration
The staging environment SHALL implement state locking to prevent concurrent modifications by multiple team members.

#### Scenario: Lock file configured
- **WHEN** user examines `backend.yaml`
- **THEN** configuration includes lockfile path for coordinated access

#### Scenario: Safe concurrent operations
- **WHEN** multiple team members attempt simultaneous deployments
- **THEN** Terraform prevents concurrent state modifications through locking

### Requirement: Environment variable secrets
The staging environment SHALL use environment variables for secret management without requiring advanced tools like vals.

#### Scenario: Environment variables template
- **WHEN** user examines `.env.example`
- **THEN** file lists all required secrets and configuration values

#### Scenario: No vals dependency
- **WHEN** user deploys staging environment
- **THEN** deployment succeeds using environment variables only

### Requirement: Makefile automation
The staging environment SHALL provide a Makefile with common deployment tasks for consistent team workflows.

#### Scenario: Standard make targets
- **WHEN** user examines Makefile
- **THEN** targets include `deploy`, `destroy`, `plan`, and `clean`

#### Scenario: Makefile runs deployment
- **WHEN** user runs `make deploy`
- **THEN** deployment executes with proper backend configuration

### Requirement: Gitignore for sensitive files
The staging environment SHALL include .gitignore to prevent committing secrets and generated files.

#### Scenario: Gitignore protects secrets
- **WHEN** user examines `.gitignore`
- **THEN** file excludes `.env`, `backend.yaml` (if rendered), and Terraform state files

### Requirement: Minimal infrastructure costs
The staging environment SHALL minimize cloud costs using S3 storage only without expensive resources like DynamoDB.

#### Scenario: S3-only backend
- **WHEN** user examines backend configuration
- **THEN** only S3 bucket is required, no DynamoDB or other paid services

### Requirement: Complete KCL configuration
The staging environment SHALL include working KCL configuration demonstrating typical staging deployment patterns.

#### Scenario: Example services for staging
- **WHEN** user examines `kcl/main.k`
- **THEN** file includes service configurations appropriate for staging environment

#### Scenario: Configuration is team-ready
- **WHEN** user deploys from staging example
- **THEN** multiple team members can safely deploy and destroy
