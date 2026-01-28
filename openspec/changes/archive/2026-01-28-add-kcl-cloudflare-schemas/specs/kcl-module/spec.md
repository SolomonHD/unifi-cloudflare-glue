## ADDED Requirements

### Requirement: KCL Cloudflare Schema - CloudflareTunnel

The KCL module SHALL provide a `CloudflareTunnel` schema that defines tunnel configuration linked to a physical device by MAC address.

#### Scenario: CloudflareTunnel with all fields is valid
Given a CloudflareTunnel with tunnel_name "homelab-tunnel", mac_address "aa:bb:cc:dd:ee:ff", and services []
When the schema validates it
Then it SHALL accept the tunnel as valid

#### Scenario: CloudflareTunnel requires tunnel_name
Given a CloudflareTunnel with empty tunnel_name ""
When the schema validates it
Then it SHALL reject with a validation error

#### Scenario: CloudflareTunnel requires valid MAC address
Given a CloudflareTunnel with mac_address "invalid-mac"
When the schema validates it
Then it SHALL reject with a validation error on the mac_address field

#### Scenario: CloudflareTunnel accepts optional credentials_path
Given a CloudflareTunnel with tunnel_name "test", mac_address "aa:bb:cc:dd:ee:ff", and credentials_path "/secrets/tunnel.json"
When the schema validates it
Then it SHALL accept the tunnel with credentials_path set

### Requirement: KCL Cloudflare Schema - TunnelService

The KCL module SHALL provide a `TunnelService` schema that defines ingress rules for routing public traffic to local services.

#### Scenario: TunnelService with all fields is valid
Given a TunnelService with public_hostname "media.example.com", local_service_url "https://jellyfin.internal.lan:8096", no_tls_verify false, and path_prefix "/api"
When the schema validates it
Then it SHALL accept the service as valid

#### Scenario: TunnelService requires public_hostname
Given a TunnelService with empty public_hostname ""
When the schema validates it
Then it SHALL reject with a validation error

#### Scenario: TunnelService requires local_service_url
Given a TunnelService with empty local_service_url ""
When the schema validates it
Then it SHALL reject with a validation error

#### Scenario: TunnelService accepts minimal configuration
Given a TunnelService with only public_hostname "app.example.com" and local_service_url "http://app.internal.lan"
When the schema validates it
Then it SHALL accept the service with defaults for optional fields

### Requirement: KCL Cloudflare Schema - CloudflareConfig

The KCL module SHALL provide a `CloudflareConfig` schema as the root configuration container for all Cloudflare Tunnel settings.

#### Scenario: CloudflareConfig with all fields is valid
Given a CloudflareConfig with zone_name "example.com", account_id "abc123", tunnels {}, and default_no_tls_verify false
When the schema validates it
Then it SHALL accept the configuration as valid

#### Scenario: CloudflareConfig requires zone_name
Given a CloudflareConfig with empty zone_name ""
When the schema validates it
Then it SHALL reject with a validation error

#### Scenario: CloudflareConfig requires account_id
Given a CloudflareConfig with empty account_id ""
When the schema validates it
Then it SHALL reject with a validation error

#### Scenario: CloudflareConfig accepts tunnels dictionary
Given a CloudflareConfig with tunnels mapping MAC addresses to CloudflareTunnel objects
When the schema validates it
Then it SHALL accept the tunnels dictionary

### Requirement: KCL Cloudflare Schema - Validation Rules

The KCL module SHALL enforce validation rules specific to Cloudflare configurations to prevent DNS loops and ensure proper zone configuration.

#### Scenario: local_service_url must use internal domain
Given a TunnelService with local_service_url "http://app.internal.lan:8080"
When the schema validates it
Then it SHALL accept the URL ending in .lan

#### Scenario: local_service_url with public domain is rejected
Given a TunnelService with local_service_url "http://app.example.com:8080"
When the schema validates it
Then it SHALL reject with a validation error to prevent DNS loops

#### Scenario: public_hostname must match zone_name
Given a CloudflareConfig with zone_name "example.com" and a TunnelService with public_hostname "app.example.com"
When the schema validates it
Then it SHALL accept the hostname as matching the zone

#### Scenario: public_hostname with different zone is rejected
Given a CloudflareConfig with zone_name "example.com" and a TunnelService with public_hostname "app.other.com"
When the schema validates it
Then it SHALL reject with a validation error

#### Scenario: One tunnel per MAC address is enforced
Given a CloudflareConfig with two tunnels both using mac_address "aa:bb:cc:dd:ee:ff"
When the schema validates it
Then it SHALL reject with a validation error for duplicate MAC

#### Scenario: no_tls_verify warning is issued
Given a TunnelService with no_tls_verify true
When the schema validates it
Then it SHALL issue a warning about disabled TLS verification

### Requirement: KCL Cloudflare Schema - Module Integration

The KCL module SHALL properly integrate Cloudflare schemas with the base module and maintain clean imports.

#### Scenario: Cloudflare schema imports base module
Given the `kcl/schemas/cloudflare.k` file
When it imports from `base.k`
Then it SHALL use proper KCL import syntax and reference base types correctly

#### Scenario: KCL module validates without errors
Given the complete Cloudflare schema implementation
When running `kcl vet` or `kcl mod check`
Then it SHALL pass validation with no errors

#### Scenario: Placeholder schemas are removed
Given the existing placeholder Cloudflare schemas
When the Cloudflare schema implementation is complete
Then the placeholder schemas SHALL be removed and replaced with proper implementations
