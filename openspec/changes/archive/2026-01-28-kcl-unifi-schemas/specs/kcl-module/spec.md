## ADDED Requirements

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
