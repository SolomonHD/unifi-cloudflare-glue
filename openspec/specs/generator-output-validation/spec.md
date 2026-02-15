## ADDED Requirements

### Requirement: UniFi generator output has all required top-level fields
When the UniFi generator produces output, it SHALL contain all required top-level fields with correct types.

#### Scenario: UniFi output has devices array
- **WHEN** the UniFi generator processes a valid configuration
- **THEN** the output SHALL contain a `devices` field that is an array

#### Scenario: UniFi output has default_domain string
- **WHEN** the UniFi generator processes a valid configuration
- **THEN** the output SHALL contain a `default_domain` field that is a string

#### Scenario: UniFi output has site string
- **WHEN** the UniFi generator processes a valid configuration
- **THEN** the output SHALL contain a `site` field that is a string representing the UniFi controller site

#### Scenario: UniFi output missing required field fails validation
- **WHEN** validating UniFi generator output that is missing `devices`, `default_domain`, or `site`
- **THEN** the validation SHALL fail with a clear error message indicating which field is missing

### Requirement: UniFi generator device structure is valid
Each device in the UniFi generator output SHALL have the correct structure and required fields.

#### Scenario: Device has friendly_hostname
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `friendly_hostname` field that is a non-empty string

#### Scenario: Device has domain
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `domain` field that is a string

#### Scenario: Device has service_cnames array
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `service_cnames` field that is an array of strings

#### Scenario: Device has nics array
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `nics` field that is an array containing at least one NIC

### Requirement: UniFi generator NIC structure is valid
Each NIC in a UniFi device SHALL have the correct structure and MAC address format.

#### Scenario: NIC has mac_address in normalized format
- **WHEN** a NIC is present in UniFi generator output
- **THEN** it SHALL have a `mac_address` field in normalized lowercase colon format (aa:bb:cc:dd:ee:ff)

#### Scenario: NIC has optional nic_name
- **WHEN** a NIC is present in UniFi generator output
- **THEN** it MAY have a `nic_name` field that is either a string or null

#### Scenario: NIC has service_cnames array
- **WHEN** a NIC is present in UniFi generator output
- **THEN** it SHALL have a `service_cnames` field that is an array of strings

### Requirement: Cloudflare generator output has all required top-level fields
When the Cloudflare generator produces output, it SHALL contain all required top-level fields with correct types.

#### Scenario: Cloudflare output has zone_name string
- **WHEN** the Cloudflare generator processes a valid configuration
- **THEN** the output SHALL contain a `zone_name` field that is a string

#### Scenario: Cloudflare output has account_id string
- **WHEN** the Cloudflare generator processes a valid configuration
- **THEN** the output SHALL contain an `account_id` field that is a string

#### Scenario: Cloudflare output has tunnels object
- **WHEN** the Cloudflare generator processes a valid configuration
- **THEN** the output SHALL contain a `tunnels` field that is an object/dictionary

#### Scenario: Cloudflare output missing required field fails validation
- **WHEN** validating Cloudflare generator output that is missing `zone_name`, `account_id`, or `tunnels`
- **THEN** the validation SHALL fail with a clear error message indicating which field is missing

### Requirement: Cloudflare generator tunnel structure is valid
Each tunnel in the Cloudflare generator output SHALL have the correct structure and required fields.

#### Scenario: Tunnel has tunnel_name
- **WHEN** a tunnel is present in Cloudflare generator output
- **THEN** it SHALL have a `tunnel_name` field that is a non-empty string

#### Scenario: Tunnel has mac_address in normalized format
- **WHEN** a tunnel is present in Cloudflare generator output
- **THEN** it SHALL have a `mac_address` field in normalized lowercase colon format

#### Scenario: Tunnel has services array
- **WHEN** a tunnel is present in Cloudflare generator output
- **THEN** it SHALL have a `services` field that is an array (may be empty)

### Requirement: Cloudflare generator service structure is valid
Each service in a Cloudflare tunnel SHALL have the correct structure and required fields.

#### Scenario: Service has public_hostname
- **WHEN** a service is present in Cloudflare generator output
- **THEN** it SHALL have a `public_hostname` field that is a string ending with the zone name

#### Scenario: Service has local_service_url
- **WHEN** a service is present in Cloudflare generator output
- **THEN** it SHALL have a `local_service_url` field that is a valid URL string

#### Scenario: Service has no_tls_verify boolean or null
- **WHEN** a service is present in Cloudflare generator output
- **THEN** it SHALL have a `no_tls_verify` field that is either a boolean or null/omitted

### Requirement: Generator output validation handles edge cases
The validation SHALL handle various edge cases gracefully.

#### Scenario: Empty devices array validation
- **WHEN** the UniFi generator produces output with an empty `devices` array
- **THEN** validation SHALL pass (empty devices is valid) but may issue a warning

#### Scenario: Device with no services
- **WHEN** a device has no services (empty services array)
- **THEN** validation SHALL pass as this is a valid configuration

#### Scenario: Device with multiple NICs
- **WHEN** a device has multiple NICs in its `nics` array
- **THEN** validation SHALL pass and verify all NICs have valid structure

#### Scenario: MAC address normalization is consistent
- **WHEN** MAC addresses are provided in various formats (AA:BB:CC:DD:EE:FF, aa-bb-cc-dd-ee-ff, AABBCCDDEEFF)
- **THEN** the generator SHALL normalize all to lowercase colon format (aa:bb:cc:dd:ee:ff)

### Requirement: Validation provides clear error messages
When validation fails, it SHALL provide actionable error messages.

#### Scenario: Missing field error message
- **WHEN** validation detects a missing required field
- **THEN** the error message SHALL indicate:
  - Which field is missing
  - Where in the structure it is missing (path)
  - What type was expected

#### Scenario: Wrong type error message
- **WHEN** validation detects a field with incorrect type
- **THEN** the error message SHALL indicate:
  - Which field has wrong type
  - What type was expected
  - What type was found
  - The actual value (truncated if necessary)

#### Scenario: Invalid MAC address format error
- **WHEN** validation detects a MAC address not in normalized format
- **THEN** the error message SHALL show:
  - The invalid MAC address value
  - The expected format (aa:bb:cc:dd:ee:ff)
  - Suggestion to check the input configuration

### Requirement: Tests run without external dependencies
The generator validation tests SHALL run without requiring external services.

#### Scenario: Tests run locally without UniFi controller
- **WHEN** running generator validation tests
- **THEN** they SHALL NOT require connection to a UniFi controller

#### Scenario: Tests run locally without Cloudflare API
- **WHEN** running generator validation tests
- **THEN** they SHALL NOT require connection to Cloudflare API

#### Scenario: Tests run in CI pipeline
- **WHEN** generator validation tests run in CI/CD
- **THEN** they SHALL complete successfully without external credentials

### Requirement: Generator output matches Terraform module expectations
The validation SHALL verify that generator output matches what Terraform modules expect.

#### Scenario: UniFi output matches unifi-dns module variables
- **WHEN** validating UniFi generator output
- **THEN** it SHALL match the structure expected by `terraform/modules/unifi-dns`

#### Scenario: Cloudflare output matches cloudflare-tunnel module variables
- **WHEN** validating Cloudflare generator output
- **THEN** it SHALL match the structure expected by `terraform/modules/cloudflare-tunnel`

#### Scenario: Services distribution filtering works correctly
- **WHEN** services have different distribution modes (unifi_only, cloudflare_only, both)
- **THEN** UniFi generator SHALL only include unifi_only and both services
- **AND** Cloudflare generator SHALL only include cloudflare_only and both services
