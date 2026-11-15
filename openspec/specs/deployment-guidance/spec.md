# Deployment Guidance

## Purpose

Specify deployment guidance and environment documentation contracts. Historical
requirements remain pending reconciliation by the active change deltas; this
structural repair does not apply those deltas or declare their behavior complete.

## Requirements

### Requirement: Full deploy success message includes credential retrieval guidance
After successful full deployment via `deploy()` using one combined Terraform operation, the final summary SHALL include clear instructions for retrieving tunnel credentials.

#### Scenario: Both UniFi and Cloudflare deployments succeed
- **WHEN** the combined operation for both components succeeds
- **THEN** the final summary MUST include a success indicator, a labeled credential-retrieval section, supported Dagger retrieval guidance with actual account/zone/backend selections and a labeled KCL-source path placeholder, an installation example, and the example documentation link

#### Scenario: UniFi succeeds but Cloudflare fails
- **WHEN** a combined operation partially affects UniFi but fails before completing the selected Cloudflare deployment
- **THEN** the final summary MUST NOT include success credential-retrieval guidance
- **AND** tests MUST NOT require separate UniFi and Cloudflare apply cycles

#### Scenario: UniFi fails before Cloudflare deployment
- **WHEN** the combined operation fails before completing the selected components
- **THEN** the final summary MUST NOT include success credential-retrieval guidance

### Requirement: Guidance commands use actual deployment parameters
Credential retrieval guidance SHALL use actual account, zone, and backend selections while clearly distinguishing unavailable original host paths from known parameter values.

#### Scenario: Dagger command reflects actual parameter values
- **WHEN** a successful deployment includes Dagger retrieval guidance
- **THEN** the command MUST include the actual account ID, zone name, and applicable backend type
- **AND** unavailable original source, backend-file, and state-directory paths MUST be shell-quoted placeholders with instructions to reuse deployment inputs
- **AND** it MUST NOT imply that conventional example paths are the original deployment paths

#### Scenario: Command formatting includes line continuations
- **WHEN** guidance includes a multi-parameter command
- **THEN** parameters MUST use consistent indentation and line-continuation backslashes

### Requirement: Guidance formatting improves readability
Credential retrieval guidance SHALL use visual separators, a labeled section,
and separate numbered options for supported Dagger retrieval and cloudflared
installation without requiring raw Terraform output instructions.

#### Scenario: Visual separation from deployment logs
- **WHEN** a successful deployment includes credential retrieval guidance
- **THEN** the section MUST have dash separators and a clearly labeled header

#### Scenario: Multi-step instructions
- **WHEN** guidance describes retrieval and installation
- **THEN** it MUST label Dagger retrieval as Option 1 and installation as Option 2 on separate lines
- **AND** it MUST NOT require printing raw Terraform state or token output

---

<!-- Requirements retained from change: environment-examples. -->

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

<!-- Requirements retained from change: deploy-function-consolidation. -->

### Requirement: Deploy function uses combined Terraform module
The `deploy()` function SHALL use `terraform/modules/glue/` for full deployment and the current provider-specific module for selective deployment, with one Terraform init/apply cycle for every scope.
Historical scenario titles are retained as identifiers; their bodies define the reconciled module selection.

#### Scenario: Full deployment uses combined module
- **WHEN** `deploy()` runs without selective flags
- **THEN** it MUST apply both providers using `terraform/modules/glue/` in one operation

#### Scenario: UniFi-only deployment uses combined module
- **WHEN** the combined `deploy()` entry point runs with `unifi_only`
- **THEN** it MUST use `terraform/modules/unifi-dns/`
- **AND** unselected provider credentials and configuration generation MUST NOT be required
- **AND** it MUST NOT run separate UniFi and Cloudflare apply cycles

#### Scenario: Cloudflare-only deployment uses combined module
- **WHEN** the combined `deploy()` entry point runs with `cloudflare_only`
- **THEN** it MUST use `terraform/modules/cloudflare-tunnel/`
- **AND** unselected provider credentials and configuration generation MUST NOT be required
- **AND** it MUST NOT run separate UniFi and Cloudflare apply cycles

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

### Requirement: Selective combined deployment includes applicable credential guidance
The combined `deploy()` function SHALL include tunnel credential-retrieval guidance after a successful deployment that includes Cloudflare, including a Cloudflare-only deployment, and MUST omit that guidance when Cloudflare is excluded or deployment fails.

#### Scenario: Cloudflare-only combined deployment succeeds
- **WHEN** `deploy()` completes successfully with Cloudflare selected and UniFi excluded
- **THEN** the result MUST include credential-retrieval guidance using actual account, zone, and backend selections and explicitly labeled placeholders for unavailable original host paths

#### Scenario: Combined deployment excludes Cloudflare
- **WHEN** `deploy()` completes successfully with UniFi selected and Cloudflare excluded
- **THEN** the result MUST NOT include Cloudflare tunnel credential-retrieval guidance

#### Scenario: Combined deployment fails
- **WHEN** `deploy()` fails before completing the selected Cloudflare deployment
- **THEN** a success guidance section MUST NOT be emitted

### Requirement: Deployment guidance tests use supported public functions
Deployment-guidance unit tests MUST invoke the supported combined deployment interface and MUST NOT require compatibility wrappers for deleted standalone functions.

#### Scenario: Guidance unit tests construct the module
- **WHEN** deployment-guidance tests exercise Cloudflare-only, UniFi-only, or combined behavior
- **THEN** they MUST call `deploy()` with the corresponding selection flags
- **AND** their mocks MUST match the current combined Terraform execution path

### Requirement: Guidance is parameter-correct and secret-safe
Guidance SHALL describe supported credential retrieval without emitting resolved credentials or raw state, using actual non-secret account, zone, and backend selections. Original host paths unavailable from opaque Dagger inputs MUST be represented by clearly labeled, shell-quoted placeholders with instructions to reuse deployment inputs; no new path-hint parameters are required.

#### Scenario: Local remote or persistent-state deployment succeeds
- **WHEN** Cloudflare is included in a successful deployment using a local backend, remote backend, or explicit persistent state
- **THEN** guidance MUST use the actual account, zone, and backend type and include only applicable source/backend/state flags
- **AND** original source, backend-file, and state-directory paths MUST be explicitly labeled placeholders, not invented conventional paths
- **AND** guidance MUST instruct the caller to replace placeholders with the same inputs used for deployment
- **AND** secret inputs MUST remain runtime references rather than rendered values

## Historical Removals

The following removed contracts are retained for migration history, not as
current requirements (from change: deploy-function-consolidation).

### Removed Contract: Separate deploy_unifi function
**Reason**: Consolidated into unified `deploy()` function with `--unifi-only` flag
**Migration**: Use `dagger call deploy --kcl-source=./kcl --unifi-only ...` instead of `dagger call deploy-unifi ...`

### Removed Contract: Separate deploy_cloudflare function
**Reason**: Consolidated into unified `deploy()` function with `--cloudflare-only` flag
**Migration**: Use `dagger call deploy --kcl-source=./kcl --cloudflare-only ...` instead of `dagger call deploy-cloudflare ...`
