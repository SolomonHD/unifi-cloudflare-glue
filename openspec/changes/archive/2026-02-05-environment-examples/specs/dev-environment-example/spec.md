## ADDED Requirements

### Requirement: Development environment directory structure
The example SHALL provide a complete development environment directory under `examples/dev-environment/` with KCL configuration, deployment scripts, README, and environment variable template.

#### Scenario: Complete directory exists
- **WHEN** user navigates to `examples/dev-environment/`
- **THEN** directory contains `README.md`, `kcl/main.k`, `.env.example`, `deploy.sh`, and `destroy.sh`

#### Scenario: All files are standalone
- **WHEN** user copies the dev-environment directory to their project
- **THEN** all scripts and configurations work without requiring files from other directories

### Requirement: Ephemeral state management
The development environment SHALL use ephemeral state that lives only within the Dagger container, requiring no backend configuration or persistence.

#### Scenario: No backend config required
- **WHEN** user runs deployment from dev-environment
- **THEN** no backend configuration file is needed or referenced

#### Scenario: State lost after container exit
- **WHEN** Dagger container completes execution
- **THEN** Terraform state is not persisted to disk or remote storage

### Requirement: Environment variable secrets
The development environment SHALL use environment variables for all secrets without requiring external secret management tools.

#### Scenario: Environment variables file provided
- **WHEN** user examines `.env.example`
- **THEN** file lists all required environment variables with example values

#### Scenario: No vals or secret manager dependencies
- **WHEN** user deploys dev environment
- **THEN** deployment succeeds using only sourced environment variables

### Requirement: Fast iteration workflow
The development environment SHALL enable rapid iteration with minimal overhead for testing configurations.

#### Scenario: Simple deployment script
- **WHEN** user executes `./deploy.sh`
- **THEN** deployment completes without backend setup or complex initialization

#### Scenario: Quick cleanup
- **WHEN** user executes `./destroy.sh`
- **THEN** all resources are destroyed without state file cleanup required

### Requirement: Zero infrastructure costs
The development environment SHALL require no cloud resource costs beyond what's provisioned in UniFi/Cloudflare.

#### Scenario: No storage costs
- **WHEN** user deploys dev environment
- **THEN** no S3 buckets, DynamoDB tables, or other storage resources are created

### Requirement: Complete KCL configuration
The development environment SHALL include a working KCL configuration demonstrating basic service deployment.

#### Scenario: Example services defined
- **WHEN** user examines `kcl/main.k`
- **THEN** file includes example tunnel and service configurations

#### Scenario: Configuration is runnable
- **WHEN** user sources `.env` and runs `./deploy.sh`
- **THEN** KCL configuration is valid and generates proper JSON output
