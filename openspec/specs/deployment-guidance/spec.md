## ADDED Requirements

### Requirement: Deploy Cloudflare success message includes credential retrieval guidance
After successful Cloudflare tunnel deployment via [`deploy_cloudflare()`](../../../../src/main/main.py:422-571), the success message SHALL include clear, actionable instructions for retrieving tunnel credentials using both Terraform and Dagger commands.

#### Scenario: Successful deploy_cloudflare with local backend
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) completes successfully with local backend
- **THEN** success message includes:
  - Success indicator and backend type
  - Section header "Next Step: Retrieve Tunnel Credentials"
  - Terraform output command: `terraform output -json cloudflare_tunnel_tokens`
  - Dagger command with actual deployment parameters (account ID, zone name, source directory)
  - `cloudflared service install` command example
  - Link to example documentation

#### Scenario: Successful deploy_cloudflare with remote backend
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) completes successfully with remote backend (e.g., S3, GCS)
- **THEN** success message includes:
  - Backend type information
  - Credential retrieval guidance
  - Dagger command WITH backend-specific flags (`--backend-type`, `--backend-config-file`)

#### Scenario: Successful deploy_cloudflare with persistent local state
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) completes successfully with mounted state directory
- **THEN** success message includes:
  - State persistence indicator
  - Dagger command WITH `--state-dir` flag

#### Scenario: Failed deploy_cloudflare
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) fails
- **THEN** success message MUST NOT include credential retrieval guidance

### Requirement: Full deploy success message includes credential retrieval guidance
After successful full deployment via [`deploy()`](../../../../src/main/main.py:574-742) where both UniFi and Cloudflare phases succeed, the final summary SHALL include clear instructions for retrieving tunnel credentials.

#### Scenario: Both UniFi and Cloudflare deployments succeed
- **WHEN** [`deploy()`](../../../../src/main/main.py:574-742) completes with both phases successful
- **THEN** final summary includes:
  - Success summary indicator
  - Section header "Next Step: Retrieve Tunnel Credentials"
  - Dagger command with KCL source directory (`--source=./kcl`)
  - Dagger command with actual deployment parameters
  - Backend-specific flags if applicable
  - `cloudflared service install` command example
  - Link to example documentation

#### Scenario: UniFi succeeds but Cloudflare fails
- **WHEN** [`deploy()`](../../../../src/main/main.py:574-742) completes with UniFi success but Cloudflare failure
- **THEN** final summary MUST NOT include credential retrieval guidance

#### Scenario: UniFi fails before Cloudflare deployment
- **WHEN** [`deploy()`](../../../../src/main/main.py:574-742) fails at UniFi phase
- **THEN** final summary MUST NOT include credential retrieval guidance

### Requirement: Guidance commands use actual deployment parameters
Credential retrieval guidance in success messages SHALL use the exact parameters from the deployment function call, not placeholder values.

#### Scenario: Dagger command reflects actual parameter values
- **WHEN** success message includes Dagger command guidance
- **THEN** command MUST include:
  - Actual Cloudflare account ID from deployment
  - Actual zone name from deployment
  - Actual backend type if not local
  - Actual backend config file path if provided
  - Actual state directory path if provided

#### Scenario: Command formatting includes line continuations
- **WHEN** success message includes multi-parameter Dagger command
- **THEN** command MUST use line continuation backslashes (`\`) for readability
- **AND** parameters MUST be indented consistently

### Requirement: Guidance formatting improves readability
Credential retrieval guidance SHALL use visual separators and formatting to distinguish it from deployment output.

#### Scenario: Visual separation from deployment logs
- **WHEN** success message includes guidance section
- **THEN** guidance MUST be preceded by separator line (dashes)
- **AND** guidance MUST be followed by separator line
- **AND** section header MUST be clearly labeled

#### Scenario: Multi-step instructions
- **WHEN** guidance includes multiple retrieval options
- **THEN** options MUST be numbered (1. Terraform, 2. Dagger, 3. Install)
- **AND** each step MUST be on separate lines for clarity

---

## ADDED Requirements (from change: environment-examples)

### Requirement: Deployment patterns documentation file
The documentation SHALL include a comprehensive deployment patterns guide at `docs/deployment-patterns.md` explaining environment-specific strategies.

#### Scenario: Documentation file exists
- **WHEN** user navigates to `docs/deployment-patterns.md`
- **THEN** file exists with complete guidance on environment patterns

### Requirement: Environment characteristics documentation
The documentation SHALL describe the characteristics of each environment type (dev, staging, production).

#### Scenario: Development environment characteristics
- **WHEN** user reads deployment patterns documentation
- **THEN** dev environment section explains ephemeral state, local testing, zero costs, and fast iteration

#### Scenario: Staging environment characteristics  
- **WHEN** user reads deployment patterns documentation
- **THEN** staging environment section explains remote state, team collaboration, locking, and minimal costs

#### Scenario: Production environment characteristics
- **WHEN** user reads deployment patterns documentation
- **THEN** production environment section explains vals integration, full security, DynamoDB locking, and production best practices

### Requirement: When to use guidance
The documentation SHALL provide clear guidance on when to use each environment type.

#### Scenario: Development use cases
- **WHEN** user reads deployment patterns documentation
- **THEN** dev section explains appropriate scenarios like testing configurations, learning, and quick experiments

#### Scenario: Staging use cases
- **WHEN** user reads deployment patterns documentation
- **THEN** staging section explains team testing, pre-production validation, and collaboration scenarios

#### Scenario: Production use cases
- **WHEN** user reads deployment patterns documentation
- **THEN** production section explains workload requirements, compliance needs, and production security requirements

### Requirement: Environment comparison table
The documentation SHALL include a comparison table showing key differences across environments.

#### Scenario: Comparison table exists
- **WHEN** user reads deployment patterns documentation
- **THEN** table compares state management, secrets, purpose, and costs across all environments

#### Scenario: Table identifies tradeoffs
- **WHEN** user examines comparison table
- **THEN** table clearly shows progression from simple/fast (dev) to secure/complex (production)

### Requirement: Deployment commands for each environment
The documentation SHALL provide example deployment commands specific to each environment.

#### Scenario: Development commands
- **WHEN** user reads dev environment section
- **THEN** section includes example commands for setup, deployment, and cleanup

#### Scenario: Staging commands
- **WHEN** user reads staging environment section
- **THEN** section includes Makefile commands and backend setup steps

#### Scenario: Production commands
- **WHEN** user reads production environment section
- **THEN** section includes vals setup, Makefile commands, and secret management steps

### Requirement: Best practices section
The documentation SHALL include a best practices section with security and workflow recommendations.

#### Scenario: Best practices listed
- **WHEN** user reads best practices section
- **THEN** practices include never committing secrets, using appropriate state management, testing in staging before production

#### Scenario: Security guidance
- **WHEN** user reads best practices
- **THEN** recommendations address secret handling, state file security, and access control

### Requirement: Example setup instructions
The documentation SHALL provide complete setup instructions for each environment.

#### Scenario: Development setup
- **WHEN** user follows dev environment setup in documentation
- **THEN** instructions cover environment variables, script execution, and iteration workflow

#### Scenario: Staging setup
- **WHEN** user follows staging environment setup
- **THEN** instructions cover S3 backend creation, team coordination, and Makefile usage

#### Scenario: Production setup
- **WHEN** user follows production environment setup
- **THEN** instructions cover vals installation, 1Password configuration, and secure deployment

### Requirement: Documentation integration
The deployment patterns documentation SHALL be linked from main project navigation.

#### Scenario: Linked from docs README
- **WHEN** user reads `docs/README.md`
- **THEN** navigation table includes link to deployment patterns

#### Scenario: Linked from main README
- **WHEN** user reads project `README.md`
- **THEN** documentation section includes reference to deployment patterns

## ADDED Requirements (from change: deploy-function-consolidation)

### Requirement: Deploy function uses combined Terraform module
The `deploy()` function SHALL use the combined Terraform module at `terraform/modules/glue/` for all deployments.

#### Scenario: Full deployment uses combined module
- **WHEN** `deploy()` is called without `--unifi-only` or `--cloudflare-only` flags
- **THEN** the function SHALL use `terraform/modules/glue/` module
- **AND** apply both UniFi DNS and Cloudflare Tunnel configurations in a single Terraform operation

#### Scenario: UniFi-only deployment uses combined module
- **WHEN** `deploy()` is called with `--unifi-only` flag
- **THEN** the function SHALL use `terraform/modules/glue/` module
- **AND** apply only UniFi DNS configuration

#### Scenario: Cloudflare-only deployment uses combined module
- **WHEN** `deploy()` is called with `--cloudflare-only` flag
- **THEN** the function SHALL use `terraform/modules/glue/` module
- **AND** apply only Cloudflare Tunnel configuration

### Requirement: Selective deployment flags
The `deploy()` function SHALL support `--unifi-only` and `--cloudflare-only` boolean flags for selective component deployment.

#### Scenario: Deploy UniFi DNS only
- **WHEN** `deploy()` is called with `--unifi-only=true`
- **THEN** the function SHALL deploy only UniFi DNS resources
- **AND** Cloudflare credentials SHALL NOT be required
- **AND** Cloudflare configuration SHALL NOT be generated or applied

#### Scenario: Deploy Cloudflare only
- **WHEN** `deploy()` is called with `--cloudflare-only=true`
- **THEN** the function SHALL deploy only Cloudflare Tunnel resources
- **AND** UniFi credentials SHALL NOT be required
- **AND** UniFi configuration SHALL NOT be generated or applied

#### Scenario: Deploy both components (default)
- **WHEN** `deploy()` is called without `--unifi-only` or `--cloudflare-only` flags
- **THEN** the function SHALL deploy both UniFi DNS and Cloudflare Tunnel resources
- **AND** both UniFi and Cloudflare credentials SHALL be required

### Requirement: Mutual exclusion validation
The `deploy()` function SHALL validate that `--unifi-only` and `--cloudflare-only` flags are not used simultaneously.

#### Scenario: Both flags set causes error
- **WHEN** `deploy()` is called with both `--unifi-only` and `--cloudflare-only` set to true
- **THEN** the function SHALL return an error: "Cannot use both --unifi-only and --cloudflare-only"
- **AND** no deployment SHALL be attempted

### Requirement: Credential requirements based on scope
The `deploy()` function SHALL require credentials only for the components being deployed.

#### Scenario: UniFi-only requires only UniFi credentials
- **WHEN** `deploy()` is called with `--unifi-only`
- **THEN** UniFi credentials (API key or username/password) SHALL be required
- **AND** Cloudflare token SHALL NOT be required
- **AND** Cloudflare account ID SHALL NOT be required
- **AND** zone name SHALL NOT be required

#### Scenario: Cloudflare-only requires only Cloudflare credentials
- **WHEN** `deploy()` is called with `--cloudflare-only`
- **THEN** Cloudflare token SHALL be required
- **AND** Cloudflare account ID SHALL be required
- **AND** zone name SHALL be required
- **AND** UniFi credentials SHALL NOT be required

#### Scenario: Full deployment requires all credentials
- **WHEN** `deploy()` is called without selective flags
- **THEN** UniFi credentials (API key or username/password) SHALL be required
- **AND** Cloudflare token SHALL be required
- **AND** Cloudflare account ID SHALL be required
- **AND** zone name SHALL be required

### Requirement: Single Terraform operation
The `deploy()` function SHALL perform a single Terraform init/apply cycle regardless of deployment scope.

#### Scenario: Atomic deployment
- **WHEN** `deploy()` executes
- **THEN** only one `terraform init` SHALL be performed
- **AND** only one `terraform apply` SHALL be performed
- **AND** the container reference SHALL be preserved after execution

## REMOVED Requirements (from change: deploy-function-consolidation)

### Requirement: Separate deploy_unifi function
**Reason**: Consolidated into unified `deploy()` function with `--unifi-only` flag
**Migration**: Use `dagger call deploy --kcl-source=./kcl --unifi-only ...` instead of `dagger call deploy-unifi ...`

### Requirement: Separate deploy_cloudflare function
**Reason**: Consolidated into unified `deploy()` function with `--cloudflare-only` flag
**Migration**: Use `dagger call deploy --kcl-source=./kcl --cloudflare-only ...` instead of `dagger call deploy-cloudflare ...`
