## Implementation Tasks

### 1. CloudflareTunnel Schema
- [x] Define `CloudflareTunnel` schema with:
  - `tunnel_name`: Unique name for the tunnel
  - `mac_address`: MAC address linking tunnel to physical device
  - `services`: List of TunnelService ingress rules
  - `credentials_path`: Optional path for tunnel credentials
- [x] Add validation: tunnel_name must not be empty
- [x] Add validation: mac_address must be valid format (17 chars)

### 2. TunnelService Schema
- [x] Define `TunnelService` schema with:
  - `public_hostname`: Public-facing hostname (e.g., "media.example.com")
  - `local_service_url`: Internal URL MUST use UniFi internal domain
  - `no_tls_verify`: Boolean to skip TLS verification
  - `path_prefix`: Optional path prefix for routing
- [x] Add validation: public_hostname must not be empty
- [x] Add validation: local_service_url must not be empty

### 3. CloudflareConfig Schema
- [x] Define `CloudflareConfig` schema as root configuration with:
  - `zone_name`: Cloudflare zone (e.g., "example.com")
  - `account_id`: Cloudflare account ID
  - `tunnels`: Dictionary mapping MAC addresses to CloudflareTunnel objects
  - `default_no_tls_verify`: Default TLS verification setting
- [x] Add validation: zone_name must not be empty
- [x] Add validation: account_id must not be empty

### 4. Validation Rules
- [x] Implement validation: local_service_url must use internal domain (.internal.lan, .local, .home, etc.)
- [x] Implement validation: public_hostname zone matching documented (enforced at consumption)
- [x] Implement validation: Each MAC address can have only one tunnel (enforced via dict structure)
- [x] Add helper function for no_tls_verify warnings

### 5. Module Integration
- [x] Define MACAddress type alias
- [x] Ensure proper KCL import syntax
- [x] Run `kcl` to validate - PASSED

### 6. Documentation
- [x] Add doc comments for all schemas
- [x] Add doc comments for all fields
- [x] Include usage examples in docstrings
