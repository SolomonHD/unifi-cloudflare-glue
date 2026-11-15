## MODIFIED Requirements

### Requirement: Terraform Module Structure

Each Terraform module SHALL follow a standard file structure with current provider declarations and documentation.

#### Scenario: unifi-dns module structure
- **GIVEN** the `terraform/modules/unifi-dns/` directory exists
- **WHEN** the community provider migration is complete
- **THEN** `versions.tf` MUST declare Terraform >= 1.5.0 and `ubiquiti-community/unifi` = 0.65.0
- **AND** `main.tf`, `variables.tf`, and `outputs.tf` MUST define the community client/DNS resources, inputs, and outputs
- **AND** `README.md` MUST document API-key and compatibility authentication plus migration behavior

#### Scenario: cloudflare-tunnel module structure
- **GIVEN** the `terraform/modules/cloudflare-tunnel/` directory exists
- **WHEN** the UniFi provider migration is complete
- **THEN** its `versions.tf`, `main.tf`, `variables.tf`, `outputs.tf`, and `README.md` MUST remain present and functionally unchanged with Terraform >= 1.5.0 and the reviewed `cloudflare/cloudflare` v5 declaration

### Requirement: Terraform Version Constraints

All Terraform modules SHALL declare current Terraform core and provider constraints appropriate to their implementation.

#### Scenario: unifi-dns versions.tf is valid
- **GIVEN** the `terraform/modules/unifi-dns/versions.tf` file exists
- **WHEN** validated with Terraform
- **THEN** it MUST declare `required_version = ">= 1.5.0"`
- **AND** it MUST declare `required_providers.unifi.source = "ubiquiti-community/unifi"` and `required_providers.unifi.version = "= 0.65.0"`

#### Scenario: glue versions.tf is valid
- **GIVEN** the `terraform/modules/glue/versions.tf` file exists
- **WHEN** validated with Terraform
- **THEN** its UniFi declaration MUST match the unifi-dns module
- **AND** its Cloudflare and random provider declarations MUST remain on their reviewed versions

#### Scenario: cloudflare-tunnel versions.tf is valid
- **GIVEN** the `terraform/modules/cloudflare-tunnel/versions.tf` file exists
- **WHEN** the UniFi provider migration is applied
- **THEN** it MUST continue to declare Terraform `>= 1.5.0`, `cloudflare/cloudflare` v5.x, and `hashicorp/random` v3.x on their reviewed constraints

## ADDED Requirements

### Requirement: Community client model preserves DNS IP derivation
The UniFi DNS module MUST manage one client per normalized configured MAC and derive A-record values from qualified `last_ip` without active-only regressions; production migration MUST guard existing-object/site identity before potentially mutating reads/imports.

#### Scenario: Existing remembered or active client is evaluated
- **WHEN** the community provider refreshes the client resource
- **THEN** the resource MUST retain `allow_existing = true` and `skip_forget_on_destroy = true`
- **AND** its usable `last_ip` MUST feed the corresponding device A record

#### Scenario: Offline client has an unusable IP
- **WHEN** an offline client's `last_ip` is null, stale against qualified policy, or unexpectedly differs from intended legacy behavior
- **THEN** strict-mode diagnostics MUST identify the affected MAC without secrets
- **AND** production migration MUST stop before state removal or apply

### Requirement: Community DNS schema preserves record semantics
The module MUST map A/CNAME records using `record_type`, `value`, and qualified duration/null TTL semantics while preserving name, enabled state, site, and target.

#### Scenario: Existing DNS configuration is planned after import
- **WHEN** the community provider refreshes all imported DNS records
- **THEN** Terraform MUST propose no record recreation or value change solely because of schema translation

#### Scenario: Legacy TTL is zero or default
- **WHEN** the exact provider contract maps legacy zero/default to null or omission
- **THEN** configuration MUST preserve that semantic value rather than blindly emit `0s`
- **AND** explicit positive-duration and null/default round trips MUST produce zero drift
