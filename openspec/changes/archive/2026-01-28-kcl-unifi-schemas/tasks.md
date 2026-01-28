## Implementation Tasks: KCL UniFi Schema Extensions

### 1. Schema Design
- [x] 1.1 Design UniFiEntity schema extending base Entity
- [x] 1.2 Design UniFiEndpoint schema extending base Endpoint
- [x] 1.3 Design UniFiConfig root configuration schema
- [x] 1.4 Define UniFiController connection schema (host, port, credentials reference)

### 2. UniFiEntity Schema Implementation
- [x] 2.1 Create UniFiEntity schema in `kcl/schemas/unifi.k`
- [x] 2.2 Add service_cnames field (list of additional device-level CNAMEs)
- [x] 2.3 Add unifi_site field with default value "default"
- [x] 2.4 Import and extend base Entity schema properly

### 3. UniFiEndpoint Schema Implementation
- [x] 3.1 Create UniFiEndpoint schema in `kcl/schemas/unifi.k`
- [x] 3.2 Add query_unifi boolean field
- [x] 3.3 Add static_ip optional field
- [x] 3.4 Import and extend base Endpoint schema properly

### 4. UniFiConfig Schema Implementation
- [x] 4.1 Create UniFiConfig root schema
- [x] 4.2 Add devices field (list of UniFiEntity objects)
- [x] 4.3 Add default_domain field for internal DNS
- [x] 4.4 Add unifi_controller connection details field

### 5. Validation Rules
- [x] 5.1 Implement validation: Each device must have at least one endpoint
- [x] 5.2 Implement validation: Each endpoint must have MAC address or static_ip
- [x] 5.3 Implement validation: friendly_hostname must be valid DNS label
- [x] 5.4 Implement validation: Domain must end in .lan, .local, or .home

### 6. Documentation
- [x] 6.1 Add doc comments to all UniFi schemas
- [x] 6.2 Add doc comments to all fields
- [x] 6.3 Update `kcl/schemas/unifi.k` module documentation

### 7. Testing & Validation
- [x] 7.1 Ensure KCL module validates without errors: `kcl run schemas/unifi.k`
- [x] 7.2 Test UniFiEntity instantiation with valid data
- [x] 7.3 Test UniFiEndpoint instantiation with valid data
- [x] 7.4 Verify validation rules reject invalid configurations
- [x] 7.5 Test default values (unifi_site = "default")

### 8. Cleanup
- [x] 8.1 Remove placeholder UniFiClient schema (replaced with new implementation)
- [x] 8.2 Remove placeholder UniFiDNSRecord schema (replaced with new implementation)
- [x] 8.3 Verify no broken imports or references
