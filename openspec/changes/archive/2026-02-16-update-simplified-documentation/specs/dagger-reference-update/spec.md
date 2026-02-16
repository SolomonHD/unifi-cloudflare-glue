## ADDED Requirements

### Requirement: Document unified function signatures
The docs/dagger-reference.md SHALL document the unified `deploy`, `plan`, and `destroy` function signatures with all parameters.

#### Scenario: User views deploy function documentation
- **WHEN** a user views the deploy function documentation
- **THEN** they see the complete parameter list including `--kcl-source`, `--unifi-url`, `--unifi-api-key`, `--cloudflare-token`, `--cloudflare-account-id`, `--zone-name`
- **AND** they see the optional flags `--unifi-only` and `--cloudflare-only`

#### Scenario: User views plan function documentation
- **WHEN** a user views the plan function documentation
- **THEN** they see the same parameter structure as deploy
- **AND** they understand plan performs a dry-run of the deployment

#### Scenario: User views destroy function documentation
- **WHEN** a user views the destroy function documentation
- **THEN** they see the parameter structure for resource destruction
- **AND** they see the selective flags for destroying only specific components

### Requirement: Document selective deployment flags
The docs/dagger-reference.md SHALL clearly document the `--unifi-only` and `--cloudflare-only` flags with usage guidelines and mutual exclusion rules.

#### Scenario: User reads flag documentation
- **WHEN** a user reads about the selective deployment flags
- **THEN** they understand `--unifi-only` deploys only UniFi DNS resources
- **AND** they understand `--cloudflare-only` deploys only Cloudflare resources
- **AND** they see a note that both flags cannot be used simultaneously

### Requirement: Remove deleted function documentation
The docs/dagger-reference.md SHALL NOT contain documentation for `deploy_unifi()` or `deploy_cloudflare()` functions.

#### Scenario: User searches for old functions
- **WHEN** a user searches the dagger-reference.md for "deploy_unifi" or "deploy_cloudflare"
- **THEN** no function documentation is found for these removed functions
- **AND** any migration notes point users to the unified `deploy` function

## REMOVED Requirements

### Requirement: deploy_unifi function documentation
**Reason**: Function removed in favor of unified `deploy --unifi-only`
**Migration**: Use `dagger call deploy --unifi-only` with the same UniFi parameters

### Requirement: deploy_cloudflare function documentation
**Reason**: Function removed in favor of unified `deploy --cloudflare-only`
**Migration**: Use `dagger call deploy --cloudflare-only` with the same Cloudflare parameters
