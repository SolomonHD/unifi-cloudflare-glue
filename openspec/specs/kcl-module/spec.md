# kcl-module Specification

## Purpose
TBD - created by archiving change project-scaffolding. Update Purpose after archive.
## Requirements
### Requirement: KCL Module Manifest

The KCL module SHALL have a valid `kcl.mod` manifest file with proper metadata.

#### Scenario: kcl.mod exists and is valid
Given the `kcl/` directory exists
When the KCL module is initialized
Then `kcl.mod` SHALL exist with:
  - A valid module name (e.g., `unifi-cloudflare-glue`)
  - A version specification
  - Appropriate metadata for the module's purpose

### Requirement: KCL Directory Structure

The KCL module SHALL organize schemas and generators in separate subdirectories.

#### Scenario: KCL structure exists
Given the `kcl/` directory exists
When the scaffolding is complete
Then the following structure SHALL exist:
  - `kcl.mod` at the root of `kcl/`
  - `README.md` explaining KCL usage
  - `schemas/` subdirectory containing:
    - `base.k` for base/common schemas (placeholder)
    - `unifi.k` for UniFi-specific schemas (placeholder)
    - `cloudflare.k` for Cloudflare-specific schemas (placeholder)
  - `generators/` subdirectory containing:
    - `unifi.k` for UniFi configuration generators (placeholder)
    - `cloudflare.k` for Cloudflare configuration generators (placeholder)

### Requirement: KCL Placeholder Files

All KCL placeholder files SHALL contain valid KCL syntax or appropriate comments indicating their future purpose.

#### Scenario: Schema placeholders are valid KCL
Given the `kcl/schemas/` directory exists
When the base.k file is validated
Then it SHALL contain complete schema implementations with valid KCL syntax

#### Scenario: Base schemas have complete documentation
Given the `kcl/schemas/base.k` file exists
When the documentation is reviewed
Then it SHALL contain doc comments for every schema and field explaining usage

### Requirement: KCL Documentation

The KCL module SHALL have a README.md explaining its purpose and usage.

#### Scenario: KCL README exists
Given the `kcl/README.md` file exists
When the documentation is reviewed
Then it SHALL contain:
  - A heading explaining this is the KCL configuration module
  - A description of how KCL schemas and generators work together
  - References to the `schemas/` and `generators/` directories
  - Placeholder sections for usage examples

### Requirement: KCL Base Schemas - MACAddress Type

The KCL module SHALL provide a `MACAddress` type that validates and normalizes MAC addresses.

#### Scenario: MAC address with colon format is valid
Given a MAC address string "AA:BB:CC:DD:EE:FF"
When the MACAddress type validates it
Then it SHALL accept the format and normalize to "aa:bb:cc:dd:ee:ff"

#### Scenario: MAC address with hyphen format is valid
Given a MAC address string "AA-BB-CC-DD-EE-FF"
When the MACAddress type validates it
Then it SHALL accept the format and normalize to "aa:bb:cc:dd:ee:ff"

#### Scenario: MAC address with no separator format is valid
Given a MAC address string "AABBCCDDEEFF"
When the MACAddress type validates it
Then it SHALL accept the format and normalize to "aa:bb:cc:dd:ee:ff"

#### Scenario: Invalid MAC address format is rejected
Given a MAC address string "INVALID_MAC"
When the MACAddress type validates it
Then it SHALL reject with a validation error

### Requirement: KCL Base Schemas - Hostname Type

The KCL module SHALL provide a `Hostname` type that validates DNS hostnames according to RFC 1123.

#### Scenario: Valid hostname is accepted
Given a hostname string "server-01"
When the Hostname type validates it
Then it SHALL accept the hostname as valid

#### Scenario: Hostname with invalid characters is rejected
Given a hostname string "server_01"
When the Hostname type validates it
Then it SHALL reject with a validation error

#### Scenario: Hostname exceeding 63 characters is rejected
Given a hostname string with 64 characters
When the Hostname type validates it
Then it SHALL reject with a validation error

### Requirement: KCL Base Schemas - Distribution Enum

The KCL module SHALL provide a `Distribution` enum to control service visibility across providers.

#### Scenario: Distribution enum has required variants
Given the Distribution enum definition
When inspected
Then it SHALL contain exactly three variants: `unifi_only`, `cloudflare_only`, `both`

#### Scenario: Distribution defaults to both
Given a Service without explicit distribution
When the Service schema is instantiated
Then the distribution field SHALL default to `both`

### Requirement: KCL Base Schemas - Endpoint Schema

The KCL module SHALL provide an `Endpoint` schema representing a network interface on an entity.

#### Scenario: Endpoint with all fields is valid
Given an Endpoint with mac_address "aa:bb:cc:dd:ee:ff", nic_name "eth0", and service_cnames ["mgmt"]
When the Endpoint schema validates it
Then it SHALL accept the endpoint as valid

#### Scenario: Endpoint with minimal fields is valid
Given an Endpoint with only mac_address "aa:bb:cc:dd:ee:ff"
When the Endpoint schema validates it
Then it SHALL accept the endpoint as valid

#### Scenario: Endpoint with invalid MAC is rejected
Given an Endpoint with mac_address "invalid"
When the Endpoint schema validates it
Then it SHALL reject with a validation error on the mac_address field

### Requirement: KCL Base Schemas - Service Schema

The KCL module SHALL provide a `Service` schema representing an application service running on an entity.

#### Scenario: Service with all fields is valid
Given a Service with name "jellyfin", port 8096, protocol "http", distribution "both"
When the Service schema validates it
Then it SHALL accept the service as valid

#### Scenario: Service with invalid port is rejected
Given a Service with port 70000
When the Service schema validates it
Then it SHALL reject with a validation error on the port field

#### Scenario: Service with invalid protocol is rejected
Given a Service with protocol "ftp"
When the Service schema validates it
Then it SHALL reject with a validation error on the protocol field

### Requirement: KCL Base Schemas - Entity Schema

The KCL module SHALL provide an `Entity` schema representing a physical device with network interfaces and services.

#### Scenario: Entity with all fields is valid
Given an Entity with friendly_hostname "nas-01", domain "internal.lan", endpoints [...], services [...]
When the Entity schema validates it
Then it SHALL accept the entity as valid

#### Scenario: Entity with empty lists is valid
Given an Entity with friendly_hostname "router", domain "internal.lan", endpoints [], services []
When the Entity schema validates it
Then it SHALL accept the entity as valid

### Requirement: KCL UniFi Schema - UniFiEntity

The KCL module SHALL provide a `UniFiEntity` schema that extends the base `Entity` schema with UniFi-specific fields.

#### Scenario: UniFiEntity extends base Entity
Given a base Entity with friendly_hostname "nas-01", domain "internal.lan"
When the UniFiEntity schema extends it with service_cnames and unifi_site
Then it SHALL inherit all base Entity fields and add UniFi-specific properties

#### Scenario: UniFiEntity has service_cnames field
Given a UniFiEntity configuration
When the service_cnames field is provided
Then it SHALL accept a list of additional device-level CNAME aliases for services

#### Scenario: UniFiEntity defaults unifi_site to "default"
Given a UniFiEntity without explicit unifi_site
When the schema is instantiated
Then the unifi_site field SHALL default to "default"

#### Scenario: UniFiEntity accepts custom unifi_site
Given a UniFiEntity with unifi_site "site-alpha"
When the schema is instantiated
Then the unifi_site field SHALL be set to "site-alpha"

### Requirement: KCL UniFi Schema - UniFiEndpoint

The KCL module SHALL provide a `UniFiEndpoint` schema that extends the base `Endpoint` schema with UniFi-specific properties for IP management.

#### Scenario: UniFiEndpoint extends base Endpoint
Given a base Endpoint with mac_address "aa:bb:cc:dd:ee:ff"
When the UniFiEndpoint schema extends it with query_unifi and static_ip
Then it SHALL inherit all base Endpoint fields and add UniFi-specific properties

#### Scenario: UniFiEndpoint has query_unifi boolean field
Given a UniFiEndpoint configuration
When the query_unifi field is set to true
Then it SHALL indicate that the UniFi Controller should be queried for the current IP

#### Scenario: UniFiEndpoint has static_ip optional field
Given a UniFiEndpoint configuration
When the static_ip field is provided as "192.168.1.100"
Then it SHALL use this static IP when query_unifi is false

#### Scenario: UniFiEndpoint requires MAC or static_ip
Given a UniFiEndpoint without mac_address and without static_ip
When the schema is validated
Then it SHALL reject with a validation error

### Requirement: KCL UniFi Schema - UniFiConfig

The KCL module SHALL provide a `UniFiConfig` schema as the root configuration container for UniFi-specific settings.

#### Scenario: UniFiConfig contains devices list
Given a UniFiConfig with a list of UniFiEntity objects
When the schema is instantiated
Then it SHALL accept and store the devices configuration

#### Scenario: UniFiConfig has default_domain field
Given a UniFiConfig with default_domain "internal.lan"
When the schema is instantiated
Then it SHALL accept the default domain for internal DNS records

#### Scenario: UniFiConfig has unifi_controller connection details
Given a UniFiConfig with unifi_controller host, port, and credentials reference
When the schema is instantiated
Then it SHALL store the connection configuration for the UniFi Controller

### Requirement: KCL UniFi Schema - Validation Rules

The KCL module SHALL enforce validation rules specific to UniFi configurations to ensure safe and correct DNS management.

#### Scenario: Device must have at least one endpoint
Given a UniFiEntity with an empty endpoints list
When the schema is validated
Then it SHALL reject with a validation error requiring at least one endpoint

#### Scenario: Valid DNS label for friendly_hostname
Given a UniFiEntity with friendly_hostname "server-01"
When the schema is validated
Then it SHALL accept the hostname as a valid DNS label

#### Scenario: Invalid DNS label for friendly_hostname is rejected
Given a UniFiEntity with friendly_hostname "server_01" (contains underscore)
When the schema is validated
Then it SHALL reject with a validation error

#### Scenario: Safe internal domain suffix is accepted
Given a UniFiEntity with domain "home.internal.lan"
When the schema is validated
Then it SHALL accept the domain ending in .lan

#### Scenario: Unsafe external domain suffix is rejected
Given a UniFiEntity with domain "example.com"
When the schema is validated
Then it SHALL reject with a validation error allowing only .lan, .local, or .home domains

#### Scenario: MAC address takes precedence over static_ip
Given a UniFiEndpoint with both mac_address and static_ip provided
When generating UniFi configuration
Then the MAC address SHALL be used for IP query and assignment

### Requirement: KCL UniFi Schema - Module Integration

The KCL module SHALL properly integrate UniFi schemas with the base module and maintain clean imports.

#### Scenario: UniFi schema imports base module
Given the `kcl/schemas/unifi.k` file
When it imports from `base.k`
Then it SHALL use proper KCL import syntax and reference base types correctly

#### Scenario: KCL module validates without errors
Given the complete UniFi schema implementation
When running `kcl vet` or `kcl mod check`
Then it SHALL pass validation with no errors

#### Scenario: Placeholder schemas are removed
Given the existing placeholder `UniFiClient` and `UniFiDNSRecord` schemas
When the UniFi schema implementation is complete
Then the placeholder schemas SHALL be removed and replaced with proper extensions

