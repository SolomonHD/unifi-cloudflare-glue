## MODIFIED Requirements

### Requirement: Terraform Module Structure

Each Terraform module SHALL follow a standard file structure with current provider declarations and documentation.

#### Scenario: unifi-dns module structure
Given the `terraform/modules/unifi-dns/` directory exists
When the community provider migration is complete
Then the following files SHALL exist:
  - `versions.tf` declaring Terraform >= 1.5.0 and `ubiquiti-community/unifi` ~> 0.55.0
  - `main.tf` defining community-provider client and DNS resources
  - `variables.tf` for input variables
  - `outputs.tf` for output values
  - `README.md` documenting API-key and compatibility authentication plus migration behavior

#### Scenario: cloudflare-tunnel module structure
Given the `terraform/modules/cloudflare-tunnel/` directory exists
When the UniFi provider migration is complete
Then its Terraform files and `cloudflare/cloudflare` v5 provider declaration SHALL remain functionally unchanged

### Requirement: Terraform Version Constraints

All Terraform modules SHALL declare current Terraform core and provider constraints appropriate to their implementation.

#### Scenario: unifi-dns versions.tf is valid
Given the `terraform/modules/unifi-dns/versions.tf` file exists
When validated with Terraform
Then it SHALL declare:
  - `required_version` of `>= 1.5.0`
  - `required_providers.unifi.source = "ubiquiti-community/unifi"`
  - `required_providers.unifi.version = "~> 0.55.0"`

#### Scenario: glue versions.tf is valid
Given the `terraform/modules/glue/versions.tf` file exists
When validated with Terraform
Then its UniFi declaration SHALL match the unifi-dns module
And its Cloudflare and random provider declarations SHALL remain on their reviewed versions

#### Scenario: cloudflare-tunnel versions.tf is unchanged
Given the `terraform/modules/cloudflare-tunnel/versions.tf` file exists
When the UniFi provider migration is applied
Then it SHALL continue to declare `cloudflare/cloudflare` v5.x and `hashicorp/random` v3.x

## ADDED Requirements

### Requirement: Community client model preserves DNS IP derivation
The UniFi DNS module MUST create or adopt one `unifi_client` per normalized configured MAC and derive DNS A-record values from the client's observed `last_ip` without active-only lookup regressions.

#### Scenario: Existing remembered or active client is evaluated
- **WHEN** the community provider refreshes the client resource
- **THEN** the resource MUST retain `allow_existing = true` and `skip_forget_on_destroy = true`
- **AND** its usable `last_ip` MUST feed the corresponding device A record

### Requirement: Community DNS schema preserves record semantics
The module MUST map each existing A and CNAME record to `unifi_dns_record` using `record_type`, `value`, and duration-form TTL while preserving name, enabled state, site, and target.

#### Scenario: Existing DNS configuration is planned after import
- **WHEN** the community provider refreshes all imported DNS records
- **THEN** Terraform MUST propose no record recreation or value change solely because of schema translation
