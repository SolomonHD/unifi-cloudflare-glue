## ADDED Requirements

### Requirement: README Quick Start shows unified deployment
The README.md SHALL display the unified `deploy` function as the primary deployment method, replacing separate `deploy_unifi` and `deploy_cloudflare` examples.

#### Scenario: User views Quick Start section
- **WHEN** a user reads the Quick Start section in README.md
- **THEN** they see the unified `dagger call deploy` command as the primary example
- **AND** the example includes all required parameters for both UniFi and Cloudflare

### Requirement: README Quick Start shows selective deployment flags
The README.md SHALL document the `--unifi-only` and `--cloudflare-only` flags with clear examples for deploying individual components.

#### Scenario: User wants to deploy only UniFi DNS
- **WHEN** a user wants to deploy only UniFi DNS
- **THEN** the README.md shows an example using `dagger call deploy --unifi-only`
- **AND** the example includes only UniFi-specific parameters

#### Scenario: User wants to deploy only Cloudflare
- **WHEN** a user wants to deploy only Cloudflare tunnels
- **THEN** the README.md shows an example using `dagger call deploy --cloudflare-only`
- **AND** the example includes only Cloudflare-specific parameters

### Requirement: Remove deprecated function references
The README.md SHALL NOT contain any references to `deploy_unifi()` or `deploy_cloudflare()` functions.

#### Scenario: User searches for old functions
- **WHEN** a user searches the README.md for "deploy_unifi" or "deploy_cloudflare"
- **THEN** no matches are found
- **AND** all examples use the unified `deploy` function
