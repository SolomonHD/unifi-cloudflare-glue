## ADDED Requirements

### Requirement: Unified Configuration Schema

The system SHALL provide a UnifiedConfig schema that combines UniFi and Cloudflare configurations into a single source of truth for the entire infrastructure.

#### Scenario: Valid unified configuration
- **GIVEN** a user has defined UniFi devices with endpoints and services
- **AND** the user has defined Cloudflare tunnels with services referencing those devices
- **WHEN** the user creates a UnifiedConfig with both configurations
- **THEN** the schema accepts the configuration without validation errors

#### Scenario: Configuration with missing required fields
- **GIVEN** a user creates a UnifiedConfig without required UniFi controller settings
- **WHEN** the configuration is instantiated
- **THEN** a validation error is raised indicating missing required fields

### Requirement: Cross-MAC Validation

The system SHALL validate that every MAC address referenced in Cloudflare tunnels exists in at least one UniFi device endpoint.

#### Scenario: All Cloudflare MACs exist in UniFi
- **GIVEN** UniFi devices with MAC addresses ["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"]
- **AND** Cloudflare tunnels referencing MACs ["aa:bb:cc:dd:ee:01"]
- **WHEN** cross-MAC validation is executed
- **THEN** validation passes with no errors

#### Scenario: Cloudflare MAC missing from UniFi
- **GIVEN** UniFi devices with MAC addresses ["aa:bb:cc:dd:ee:01"]
- **AND** Cloudflare tunnels referencing MACs ["aa:bb:cc:dd:ee:99"]
- **WHEN** cross-MAC validation is executed
- **THEN** validation fails with error message showing the missing MAC and available MACs

#### Scenario: MAC address normalization during validation
- **GIVEN** UniFi devices with MAC address "AA:BB:CC:DD:EE:01"
- **AND** Cloudflare tunnels referencing MAC "aa-bb-cc-dd-ee-01" (different format)
- **WHEN** cross-MAC validation is executed
- **THEN** validation passes because MACs match after normalization

### Requirement: Hostname Uniqueness Validation

The system SHALL validate that no two devices share the same friendly_hostname.

#### Scenario: All hostnames are unique
- **GIVEN** devices with friendly_hostnames ["media-server", "backup-server", "iot-hub"]
- **WHEN** hostname uniqueness validation is executed
- **THEN** validation passes with no errors

#### Scenario: Duplicate friendly hostnames detected
- **GIVEN** devices with friendly_hostnames ["media-server", "media-server", "backup-server"]
- **WHEN** hostname uniqueness validation is executed
- **THEN** validation fails with error showing the duplicate hostname and conflicting devices

### Requirement: Public Hostname Uniqueness Validation

The system SHALL validate that no two tunnel services share the same public_hostname.

#### Scenario: All public hostnames are unique
- **GIVEN** tunnel services with public_hostnames ["jellyfin.example.com", "plex.example.com"]
- **WHEN** public hostname uniqueness validation is executed
- **THEN** validation passes with no errors

#### Scenario: Duplicate public hostnames detected
- **GIVEN** tunnel services with public_hostnames ["jellyfin.example.com", "jellyfin.example.com"]
- **WHEN** public hostname uniqueness validation is executed
- **THEN** validation fails with error showing the duplicate public hostname and conflicting tunnels

### Requirement: Internal Domain Validation

The system SHALL validate that all Cloudflare local_service_url values use internal domain suffixes.

#### Scenario: All URLs use internal domains
- **GIVEN** local_service_url values ["http://jellyfin.internal.lan:8096", "https://nas.local:443"]
- **WHEN** internal domain validation is executed
- **THEN** validation passes with no errors

#### Scenario: URL with public domain detected
- **GIVEN** local_service_url values ["http://jellyfin.example.com:8096"]
- **WHEN** internal domain validation is executed
- **THEN** validation fails with error indicating the URL uses a public domain

### Requirement: Fail-Fast Validation in Generation

The system SHALL run all validations before any generation occurs and fail immediately on the first validation error.

#### Scenario: Valid configuration generates successfully
- **GIVEN** a UnifiedConfig passing all validation rules
- **WHEN** the generate() function is called
- **THEN** all validations pass
- **AND** both unifi_json and cloudflare_json are generated and returned

#### Scenario: Invalid configuration fails before generation
- **GIVEN** a UnifiedConfig with a MAC address mismatch
- **WHEN** the generate() function is called
- **THEN** validation fails with a clear error message
- **AND** no JSON output is generated

### Requirement: Comprehensive Error Messages

The system SHALL provide validation error messages that include context and actionable suggestions.

#### Scenario: MAC mismatch error message
- **GIVEN** a MAC mismatch validation failure for MAC "aa:bb:cc:dd:ee:ff"
- **WHEN** the error message is generated
- **THEN** the message includes:
  - The specific MAC address causing the issue
  - The tunnel name referencing it
  - A list of available devices
  - A list of available MAC addresses

#### Scenario: Duplicate hostname error message
- **GIVEN** a duplicate hostname validation failure for "media-server"
- **WHEN** the error message is generated
- **THEN** the message includes:
  - The duplicate hostname value
  - The list of devices using that hostname
  - Suggestion to use unique hostnames

### Requirement: Combined JSON Output

The system SHALL provide a generate() function that returns both UniFi and Cloudflare JSON configurations from a single UnifiedConfig input.

#### Scenario: Generate both configurations
- **GIVEN** a valid UnifiedConfig with devices and tunnels
- **WHEN** generate() is called
- **THEN** the result contains:
  - `unifi_json` field with UniFi-compatible configuration
  - `cloudflare_json` field with Cloudflare-compatible configuration

#### Scenario: Output matches individual generators
- **GIVEN** the same configuration used with individual generators
- **WHEN** generate() is called on the unified config
- **THEN** unifi_json matches the output of the UniFi generator
- **AND** cloudflare_json matches the output of the Cloudflare generator
