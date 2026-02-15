## ADDED Requirements

### Requirement: Module combines UniFi DNS and Cloudflare Tunnel deployments
The combined module SHALL wrap both the `unifi-dns` and `cloudflare-tunnel` modules to enable atomic deployment from a single Terraform configuration.

#### Scenario: Module calls both sub-modules
- **WHEN** the combined module is instantiated
- **THEN** it SHALL call the `unifi-dns` module with provided configuration
- **AND** it SHALL call the `cloudflare-tunnel` module with provided configuration

#### Scenario: Relative module paths are used
- **WHEN** the combined module sources its sub-modules
- **THEN** it SHALL use relative paths (`../unifi-dns/` and `../cloudflare-tunnel/`)

### Requirement: Providers are configured at root module level
The combined module SHALL configure both the `filipowm/unifi` and `cloudflare/cloudflare` providers at the root level to avoid provider conflicts.

#### Scenario: UniFi provider configuration
- **WHEN** the module is initialized
- **THEN** the UniFi provider SHALL be configured with URL, API key, and optional insecure flag

#### Scenario: Cloudflare provider configuration
- **WHEN** the module is initialized
- **THEN** the Cloudflare provider SHALL be configured with API token

### Requirement: Cloudflare deployment depends on UniFi DNS completion
The combined module SHALL declare an explicit dependency ensuring Cloudflare Tunnel resources are created only after UniFi DNS resources are successfully applied.

#### Scenario: Dependency chain is enforced
- **WHEN** `terraform apply` is executed
- **THEN** UniFi DNS resources SHALL be created first
- **AND** Cloudflare Tunnel resources SHALL wait for UniFi DNS completion

#### Scenario: DNS records are resolvable before tunnel creation
- **WHEN** Cloudflare Tunnel services reference internal hostnames
- **THEN** those hostnames SHALL already exist in UniFi DNS

### Requirement: Module accepts all configuration inputs
The combined module SHALL accept all input variables required by both sub-modules, including configuration objects, file paths, and provider credentials.

#### Scenario: Configuration file inputs
- **WHEN** `unifi_config_file` is provided
- **THEN** it SHALL be passed to the `unifi-dns` module
- **WHEN** `cloudflare_config_file` is provided
- **THEN** it SHALL be passed to the `cloudflare-tunnel` module

#### Scenario: Configuration object inputs
- **WHEN** `unifi_config` object is provided
- **THEN** it SHALL be passed to the `unifi-dns` module
- **WHEN** `cloudflare_config` object is provided
- **THEN** it SHALL be passed to the `cloudflare-tunnel` module

#### Scenario: Provider credential inputs
- **WHEN** UniFi credentials (URL, API key, username, password) are provided
- **THEN** they SHALL configure the UniFi provider
- **WHEN** Cloudflare token is provided
- **THEN** it SHALL configure the Cloudflare provider

### Requirement: Module exposes all sub-module outputs
The combined module SHALL expose all outputs from both the `unifi-dns` and `cloudflare-tunnel` modules.

#### Scenario: UniFi DNS outputs are exposed
- **WHEN** the module is applied
- **THEN** UniFi DNS outputs (dns_records, cname_records, device_ips, missing_devices, summary) SHALL be accessible

#### Scenario: Cloudflare Tunnel outputs are exposed
- **WHEN** the module is applied
- **THEN** Cloudflare Tunnel outputs (tunnel_ids, credentials_json, public_hostnames, zone_id, tunnel_names, record_ids) SHALL be accessible

### Requirement: Module declares required provider versions
The combined module SHALL declare version constraints for all required providers in `versions.tf`.

#### Scenario: Provider versions are declared
- **WHEN** `versions.tf` is defined
- **THEN** it SHALL declare `filipowm/unifi` provider version `~> 1.0`
- **AND** it SHALL declare `cloudflare/cloudflare` provider version `~> 5.0`
- **AND** it SHALL declare `hashicorp/random` provider version `~> 3.0`

### Requirement: Module includes documentation
The combined module SHALL include a `README.md` file documenting its purpose, inputs, outputs, and usage examples.

#### Scenario: README is complete
- **WHEN** the README is reviewed
- **THEN** it SHALL describe the module's purpose
- **AND** it SHALL document all input variables
- **AND** it SHALL document all outputs
- **AND** it SHALL provide usage examples
