## ADDED Requirements

### Requirement: Document unified deployment pattern
The docs/deployment-patterns.md SHALL describe the unified deployment pattern using the combined Terraform module approach.

#### Scenario: User reads full deployment pattern
- **WHEN** a user reads the Full Deployment pattern
- **THEN** they see a single `dagger call deploy` command that deploys both UniFi and Cloudflare
- **AND** they understand the combined module handles both providers in one operation
- **AND** they do NOT see warnings about provider conflicts (since they are now resolved)

### Requirement: Document selective deployment patterns
The docs/deployment-patterns.md SHALL document patterns for deploying only UniFi DNS or only Cloudflare tunnels using the new flags.

#### Scenario: User reads UniFi-only deployment pattern
- **WHEN** a user reads the UniFi-only deployment pattern
- **THEN** they see the `dagger call deploy --unifi-only` command
- **AND** they understand this pattern is useful for internal-only services
- **AND** they see the minimal required parameters for UniFi-only deployment

#### Scenario: User reads Cloudflare-only deployment pattern
- **WHEN** a user reads the Cloudflare-only deployment pattern
- **THEN** they see the `dagger call deploy --cloudflare-only` command
- **AND** they understand this pattern requires existing UniFi DNS for local resolution
- **AND** they see a warning about DNS loop prevention when using Cloudflare-only

### Requirement: Remove provider conflict warnings
The docs/deployment-patterns.md SHALL remove warnings about provider conflicts that are now resolved by the combined Terraform module.

#### Scenario: User reads deployment patterns
- **WHEN** a user reads through deployment patterns
- **THEN** they do NOT see warnings about Terraform provider conflicts
- **AND** they do NOT see workarounds for separate UniFi and Cloudflare deployments
- **AND** they see explanations of how the combined module simplifies the workflow

## MODIFIED Requirements

### Requirement: Full Deployment Pattern
The Full Deployment pattern SHALL be updated to use the unified `deploy` command instead of separate deployment steps.

#### Scenario: User follows full deployment pattern
- **WHEN** a user follows the Full Deployment pattern documentation
- **THEN** they run a single `dagger call deploy` command
- **AND** the command deploys both UniFi DNS and Cloudflare tunnels
- **AND** they see examples with the `--source` parameter pointing to their KCL configuration
