## ADDED Requirements

### Requirement: Destroy function supports selective component destruction
The `destroy()` function SHALL support `--unifi-only` and `--cloudflare-only` boolean flags for selective component destruction.

#### Scenario: Destroy both components (default behavior)
- **WHEN** the user invokes `destroy()` without `--unifi-only` or `--cloudflare-only` flags
- **THEN** the function SHALL destroy both UniFi DNS and Cloudflare Tunnel configurations
- **AND** the function SHALL use the combined `terraform/modules/glue/` module

#### Scenario: Destroy only UniFi DNS
- **WHEN** the user invokes `destroy()` with `--unifi-only` flag set
- **THEN** the function SHALL destroy only UniFi DNS configurations
- **AND** the function SHALL use Terraform `-target=module.unifi_dns` option
- **AND** the function SHALL NOT require Cloudflare credentials

#### Scenario: Destroy only Cloudflare Tunnel
- **WHEN** the user invokes `destroy()` with `--cloudflare-only` flag set
- **THEN** the function SHALL destroy only Cloudflare Tunnel configurations
- **AND** the function SHALL use Terraform `-target=module.cloudflare_tunnel` option
- **AND** the function SHALL NOT require UniFi credentials

### Requirement: Mutual exclusion of selective destroy flags
The `destroy()` function SHALL prevent simultaneous use of `--unifi-only` and `--cloudflare-only` flags.

#### Scenario: Both flags provided
- **WHEN** the user invokes `destroy()` with both `--unifi-only` and `--cloudflare-only` flags set
- **THEN** the function SHALL return an error: "Cannot use both --unifi-only and --cloudflare-only"
- **AND** the function SHALL NOT execute any destruction

### Requirement: Selective destroy uses combined Terraform module
The `destroy()` function SHALL use the combined `terraform/modules/glue/` module for all destroy operations.

#### Scenario: Destroy with combined module
- **WHEN** the user invokes `destroy()` in any mode (default, unifi-only, or cloudflare-only)
- **THEN** the function SHALL use the `terraform/modules/glue/` module
- **AND** the function SHALL generate only the KCL configuration files needed for the selected components
- **AND** the function SHALL maintain proper state management for partial destroys

### Requirement: Conditional KCL config generation for selective destroy
The `destroy()` function SHALL generate only the necessary KCL configuration files based on the selected destroy mode.

#### Scenario: Generate only UniFi config for unifi-only mode
- **WHEN** the user invokes `destroy()` with `--unifi-only` flag
- **THEN** the function SHALL generate only `unifi.json` configuration file
- **AND** the function SHALL NOT generate `cloudflare.json`

#### Scenario: Generate only Cloudflare config for cloudflare-only mode
- **WHEN** the user invokes `destroy()` with `--cloudflare-only` flag
- **THEN** the function SHALL generate only `cloudflare.json` configuration file
- **AND** the function SHALL NOT generate `unifi.json`

#### Scenario: Generate both configs for default mode
- **WHEN** the user invokes `destroy()` without selective flags
- **THEN** the function SHALL generate both `unifi.json` and `cloudflare.json` configuration files

### Requirement: Selective destroy status reporting
The `destroy()` function SHALL return clear status messages indicating which components were destroyed.

#### Scenario: Report unifi-only destruction
- **WHEN** the user invokes `destroy()` with `--unifi-only` flag successfully
- **THEN** the function SHALL return a message indicating UniFi DNS configurations were destroyed
- **AND** the message SHALL NOT mention Cloudflare

#### Scenario: Report cloudflare-only destruction
- **WHEN** the user invokes `destroy()` with `--cloudflare-only` flag successfully
- **THEN** the function SHALL return a message indicating Cloudflare Tunnel configurations were destroyed
- **AND** the message SHALL NOT mention UniFi

#### Scenario: Report combined destruction
- **WHEN** the user invokes `destroy()` without selective flags successfully
- **THEN** the function SHALL return a message indicating both UniFi DNS and Cloudflare Tunnel configurations were destroyed
