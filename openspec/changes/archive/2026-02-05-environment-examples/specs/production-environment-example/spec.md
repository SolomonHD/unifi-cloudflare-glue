## ADDED Requirements

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

### Requirement: Complete KCL configuration
The production environment SHALL include working KCL configuration demonstrating production deployment patterns.

#### Scenario: Production services defined
- **WHEN** user examines `kcl/main.k`
- **THEN** file includes example configurations appropriate for production

#### Scenario: Configuration uses production domains
- **WHEN** user examines KCL configuration
- **THEN** services reference production domain patterns (not test/dev domains)
