# example-configuration Specification

## Purpose
TBD - created by archiving change 010-example-homelab-media-stack. Update Purpose after archive.
## Requirements
### Requirement: Media Server Entity Definition

The KCL configuration SHALL define a media server entity with dual NICs as the foundation for all service configurations.

#### Scenario: Single device hosts all services
Given a user wants to configure a homelab media server
When they define the media server entity
Then it must include:
- friendly_hostname: "media-server"
- domain: "internal.lan"
- At least two endpoints (management and media NICs)

#### Scenario: Dual NIC configuration
Given a media server has multiple network interfaces
When endpoints are defined
Then they must include:
- Management NIC with MAC address placeholder
- Media NIC (10GbE) with MAC address placeholder
- Descriptive nic_name for each endpoint

### Requirement: UniFi-Only Services Configuration

The KCL configuration SHALL define internal automation services (*arr stack) that are only accessible within the internal network.

#### Scenario: Internal automation services
Given services that should only be accessible internally
When configuring Sonarr, Radarr, and Prowlarr
Then they must have:
- distribution: "unifi_only"
- internal_hostname in format "servicename.internal.lan"
- No public_hostname defined
- Standard ports (Sonarr: 8989, Radarr: 7878, Prowlarr: 9696)

### Requirement: Cloudflare-Only Services Configuration

The KCL configuration SHALL define external-facing services that are only accessible through Cloudflare Tunnel.

#### Scenario: External document and photo management
Given services that should only be accessible externally
When configuring Paperless-ngx and Immich
Then they must have:
- distribution: "cloudflare_only"
- public_hostname in format "service.<your-domain>.com"
- internal_hostname for local_service_url construction
- Standard ports (Paperless: 8000, Immich: 2283)

### Requirement: Dual-Exposure Services Configuration

The KCL configuration SHALL define services accessible both internally and externally through both UniFi DNS and Cloudflare Tunnel.

#### Scenario: Media streaming with internal and external access
Given services that need both internal and external access
When configuring Jellyfin and Jellyseerr
Then they must have:
- distribution: "both"
- internal_hostname for UniFi DNS (e.g., "jellyfin.internal.lan")
- public_hostname for Cloudflare (e.g., "media.<your-domain>.com")
- Correct ports (Jellyfin: 8096, Jellyseerr: 5055)

### Requirement: Placeholder Values

The KCL configuration SHALL use consistent placeholder values that users can easily identify and replace.

#### Scenario: User customization required
Given the example is intended for users to adapt
When placeholder values are needed
Then they must use consistent format:
- `<your-domain>` for Cloudflare zone
- `<your-account-id>` for Cloudflare account
- `<mac-management>` for management NIC MAC
- `<mac-media>` for media NIC MAC
- Comments explaining each placeholder

### Requirement: MAC Address Handling

The KCL configuration SHALL demonstrate MAC address normalization and proper usage patterns.

#### Scenario: MAC address normalization demonstration
Given MAC addresses can be provided in multiple formats
When the configuration includes MAC addresses
Then it must demonstrate:
- Acceptable formats (colon, hyphen, no separator)
- Normalization to lowercase colon format in output
- Consistent MAC address usage as dictionary keys

---

## ADDED Requirements (from change: environment-examples)

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

### Requirement: Production environment directory structure
The example SHALL provide a complete production environment directory under `examples/production-environment/` with KCL configuration, vals backend template, Makefile, README, SECRETS.md, .gitignore, and environment variable template.

#### Scenario: Complete directory exists
- **WHEN** user navigates to `examples/production-environment/`
- **THEN** directory contains `README.md`, `kcl/main.k`, `backend.yaml.tmpl`, `.env.example`, `Makefile`, `SECRETS.md`, and `.gitignore`

#### Scenario: Production-ready configuration
- **WHEN** user copies the production-environment directory
- **THEN** all security best practices are demonstrated

### Requirement: Remote state with locking
The production environment SHALL use remote state backend (S3) with DynamoDB locking or lockfile for safe concurrent operations.

#### Scenario: Backend template configured
- **WHEN** user examines `backend.yaml.tmpl`
- **THEN** file includes vals placeholders for S3 bucket, region, and locking mechanism

#### Scenario: State persisted with locking
- **WHEN** user deploys production environment
- **THEN** Terraform state uses both remote storage and locking

### Requirement: Vals secret injection
The production environment SHALL use vals for injecting secrets from 1Password or other secret managers into backend configuration.

#### Scenario: Vals template provided
- **WHEN** user examines `backend.yaml.tmpl`
- **THEN** file uses `ref+op://` or `ref+vault://` syntax for secret references

#### Scenario: Secrets never committed
- **WHEN** user runs Makefile targets
- **THEN** rendered `backend.yaml` with plaintext secrets is automatically cleaned up

### Requirement: 1Password integration documentation
The production environment SHALL document the 1Password secret structure required for vals integration.

#### Scenario: SECRETS.md exists
- **WHEN** user examines `SECRETS.md`
- **THEN** file documents required 1Password vault structure and item names

#### Scenario: Secret setup instructions
- **WHEN** user reads SECRETS.md
- **THEN** instructions explain how to create and structure secrets in 1Password

### Requirement: Makefile automation with secret cleanup
The production environment SHALL provide Makefile targets that automatically clean up rendered secrets after operations.

#### Scenario: Makefile targets available
- **WHEN** user examines Makefile
- **THEN** targets include `deploy`, `destroy`, `plan`, and `clean`

#### Scenario: Automatic cleanup after deploy
- **WHEN** user runs `make deploy`
- **THEN** rendered backend.yaml is removed automatically after deployment

#### Scenario: Manual cleanup target
- **WHEN** user runs `make clean`
- **THEN** all rendered secret files are removed

### Requirement: Gitignore for production secrets
The production environment SHALL include comprehensive .gitignore protecting all secret files and rendered configurations.

#### Scenario: Rendered secrets excluded
- **WHEN** user examines `.gitignore`
- **THEN** file excludes `backend.yaml` (rendered from .tmpl), `.env`, and state files

#### Scenario: Only templates committed
- **WHEN** user commits production example
- **THEN** only `backend.yaml.tmpl` is committed, not rendered `backend.yaml`

### Requirement: Full security best practices
The production environment SHALL demonstrate all security best practices including secret rotation, least privilege, and audit logging.

#### Scenario: Security guidance in README
- **WHEN** user reads production README
- **THEN** document includes security notes about secret rotation, access control, and monitoring

#### Scenario: No hardcoded secrets
- **WHEN** user examines all production files
- **THEN** no plaintext secrets exist in any committed file

### Requirement: Production-grade infrastructure costs
The production environment SHALL document expected infrastructure costs and demonstrate full production backend setup.

#### Scenario: Cost documentation
- **WHEN** user reads production README
- **THEN** costs for S3, DynamoDB (if used), and other resources are documented

#### Scenario: DynamoDB or lockfile locking
- **WHEN** user examines backend template
- **THEN** configuration shows either DynamoDB table name or lockfile path for locking

### Requirement: Production-grade KCL configuration
The production environment SHALL include working KCL configuration demonstrating production deployment patterns.

#### Scenario: Production services defined
- **WHEN** user examines `kcl/main.k`
- **THEN** file includes example configurations appropriate for production

#### Scenario: Configuration uses production domains
- **WHEN** user examines KCL configuration
- **THEN** services reference production domain patterns (not test/dev domains)

