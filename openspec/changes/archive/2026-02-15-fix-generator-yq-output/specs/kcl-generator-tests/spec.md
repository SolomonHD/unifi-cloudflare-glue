## ADDED Requirements

### Requirement: UniFi sample configuration moved to test file
The `sample_config` variable from `generators/unifi.k` SHALL be moved to a dedicated test file for standalone testing of the generator.

#### Scenario: UniFi test file outputs both sample and result
- **WHEN** `kcl run generators/test_unifi.k` is executed
- **THEN** the output SHALL contain both `sample_config` and `result` documents
- **AND** both documents SHALL be valid YAML
- **AND** the `result` document SHALL be the UniFi configuration generated from `sample_config`

### Requirement: Cloudflare sample configuration moved to test file
The `sample_config` variable from `generators/cloudflare.k` SHALL be moved to a dedicated test file for standalone testing of the generator.

#### Scenario: Cloudflare test file outputs both sample and result
- **WHEN** `kcl run generators/test_cloudflare.k` is executed
- **THEN** the output SHALL contain both `sample_config` and `result` documents
- **AND** both documents SHALL be valid YAML
- **AND** the `result` document SHALL be the Cloudflare configuration generated from `sample_config`

### Requirement: Test files import generator functions
The test files SHALL import and use the generator functions from the main generator files.

#### Scenario: Test file imports generator
- **WHEN** `generators/test_unifi.k` is created
- **THEN** it SHALL import `generators.unifi` to access `generate_unifi_config`
- **AND** it SHALL define its own `sample_config` for testing
- **AND** it SHALL output both `sample_config` and `result`

#### Scenario: Cloudflare test imports generator
- **WHEN** `generators/test_cloudflare.k` is created
- **THEN** it SHALL import `generators.cloudflare` to access `generate_cloudflare_config`
- **AND** it SHALL define its own `sample_config` for testing
- **AND** it SHALL output both `sample_config` and `result`

### Requirement: Sample configurations preserved for testing
The sample configurations SHALL be preserved in test files to allow standalone validation of generator behavior.

#### Scenario: UniFi sample preserved
- **WHEN** viewing `generators/test_unifi.k`
- **THEN** the sample configuration SHALL include realistic UniFi device and service definitions
- **AND** the sample SHALL demonstrate MAC address normalization
- **AND** the sample SHALL demonstrate service distribution (unifi_only, cloudflare_only, both)

#### Scenario: Cloudflare sample preserved
- **WHEN** viewing `generators/test_cloudflare.k`
- **THEN** the sample configuration SHALL include realistic Cloudflare tunnel definitions
- **AND** the sample SHALL demonstrate multiple tunnels per configuration
- **AND** the sample SHALL demonstrate DNS loop prevention concepts
