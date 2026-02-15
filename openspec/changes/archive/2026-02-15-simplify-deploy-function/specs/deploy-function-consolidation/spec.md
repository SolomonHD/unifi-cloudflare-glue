## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Separate deploy_unifi function
**Reason**: Consolidated into unified `deploy()` function with `--unifi-only` flag
**Migration**: Use `dagger call deploy --kcl-source=./kcl --unifi-only ...` instead of `dagger call deploy-unifi ...`

### Requirement: Separate deploy_cloudflare function
**Reason**: Consolidated into unified `deploy()` function with `--cloudflare-only` flag
**Migration**: Use `dagger call deploy --kcl-source=./kcl --cloudflare-only ...` instead of `dagger call deploy-cloudflare ...`
