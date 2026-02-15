## ADDED Requirements

### Requirement: UniFi generator outputs single-document YAML
The `generators/unifi.k` file SHALL output only a single YAML document containing the generated UniFi configuration when run directly.

#### Scenario: Running unifi.k produces single-document output
- **WHEN** `kcl run generators/unifi.k` is executed
- **THEN** the output SHALL contain exactly one YAML document (the `result` variable)
- **AND** the output SHALL NOT contain the `sample_config` document
- **AND** the output SHALL be parseable by `yq eval -o=json '.'`

### Requirement: UniFi generator remains importable
The `generators/unifi.k` file SHALL remain importable by user configurations without side effects from sample configuration.

#### Scenario: Importing unifi.k in user configuration
- **WHEN** a user configuration imports `generators.unifi`
- **THEN** the generator functions SHALL be available
- **AND** no sample configuration SHALL be output unless explicitly requested

### Requirement: UniFi generator output is valid JSON after yq conversion
The UniFi generator output SHALL produce valid JSON when piped through yq.

#### Scenario: yq conversion succeeds
- **WHEN** `kcl run generators/unifi.k | yq eval -o=json '.'` is executed
- **THEN** the command SHALL exit with code 0
- **AND** the output SHALL be valid JSON containing UniFi configuration
