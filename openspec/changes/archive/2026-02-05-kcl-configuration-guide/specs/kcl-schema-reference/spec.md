## ADDED Requirements

### Requirement: Base schema documentation
The documentation SHALL comprehensively describe all base schemas (Entity, Endpoint, Service, MACAddress, Hostname, Distribution) including field types, validation rules, and purposes.

#### Scenario: User looks up Entity schema
- **WHEN** user reads the Entity schema documentation
- **THEN** documentation shows all fields (friendly_hostname, domain, endpoints, services), their types, validation rules, and example usage

#### Scenario: User understands MAC address normalization
- **WHEN** user encounters MAC address validation
- **THEN** documentation explains accepted formats (colon, hyphen, no separator) and normalization to lowercase colon format

#### Scenario: User learns Distribution enum
- **WHEN** user configures service distribution
- **THEN** documentation defines all Distribution values (unifi_only, cloudflare_only, both) with use cases

### Requirement: UniFi schema documentation
The documentation SHALL describe all UniFi-specific schemas (UniFiConfig, UniFiEntity, UniFiEndpoint, UniFiController) with configuration examples.

#### Scenario: User configures UniFi devices
- **WHEN** user defines UniFi devices in configuration
- **THEN** documentation shows UniFiEntity schema with friendly_hostname, domain, endpoints, and service_cnames fields

#### Scenario: User sets up UniFi controller connection
- **WHEN** user needs to connect to UniFi controller
- **THEN** documentation explains UniFiController schema with host, username, password, site, and verify_ssl fields

#### Scenario: User defines network interfaces
- **WHEN** user adds network interfaces to devices
- **THEN** documentation describes UniFiEndpoint schema with mac_address, nic_name, and service_cnames

### Requirement: Cloudflare schema documentation
The documentation SHALL describe all Cloudflare-specific schemas (CloudflareConfig, CloudflareTunnel, TunnelService) with tunnel configuration patterns.

#### Scenario: User creates Cloudflare tunnel
- **WHEN** user defines Cloudflare tunnel configuration
- **THEN** documentation shows CloudflareTunnel schema with tunnel_name, services, and MAC address linking

#### Scenario: User configures tunnel services
- **WHEN** user exposes services via Cloudflare tunnel
- **THEN** documentation describes TunnelService schema with public_hostname, local_service_url, and no_tls_verify fields

#### Scenario: User understands zone configuration
- **WHEN** user sets up Cloudflare DNS
- **THEN** documentation explains CloudflareConfig schema with zone_name, account_id, and tunnels dictionary

### Requirement: Schema field examples
The documentation SHALL provide concrete examples for every schema field showing valid and invalid values.

#### Scenario: User validates hostname format
- **WHEN** user reads hostname documentation
- **THEN** examples show valid hostnames (nas-01, server-prod) and invalid ones (server_prod, -server, server-)

#### Scenario: User understands port range
- **WHEN** user configures service ports
- **THEN** examples show valid ports (80, 8096, 443) and out-of-range values (0, 65536)

#### Scenario: User learns service protocol values
- **WHEN** user selects service protocol
- **THEN** examples demonstrate http, https, and tcp with use cases for each
