## ADDED Requirements

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

## MODIFIED Requirements

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
