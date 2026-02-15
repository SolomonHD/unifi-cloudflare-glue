## ADDED Requirements

### Requirement: KCL dependencies are pre-downloaded before running generators
The system SHALL run `kcl mod update` before executing `kcl run` on generator files to ensure all git dependencies are downloaded and cached before output generation.

#### Scenario: KCL module with git dependencies
- **WHEN** `generate_unifi_config()` is called with a KCL module that has git dependencies
- **THEN** the system SHALL first execute `kcl mod update` to download dependencies
- **AND** then execute `kcl run generators/unifi.k` to generate clean YAML output
- **AND** the output SHALL contain only valid YAML without git clone messages

#### Scenario: KCL module without git dependencies
- **WHEN** `generate_unifi_config()` is called with a KCL module that has no external dependencies
- **THEN** `kcl mod update` SHALL complete successfully without error
- **AND** `kcl run generators/unifi.k` SHALL execute normally
- **AND** the output SHALL be valid YAML

#### Scenario: Cloudflare config generation with dependencies
- **WHEN** `generate_cloudflare_config()` is called with a KCL module that has git dependencies
- **THEN** the system SHALL first execute `kcl mod update` to download dependencies
- **AND** then execute `kcl run generators/cloudflare.k` to generate clean YAML output
- **AND** the output SHALL contain only valid YAML without git clone messages

### Requirement: KCL dependency download errors are handled gracefully
The system SHALL provide clear error messages when `kcl mod update` fails due to network issues or invalid kcl.mod files.

#### Scenario: Network failure during dependency download
- **WHEN** `kcl mod update` fails due to network connectivity issues
- **THEN** the system SHALL raise a `KCLGenerationError` with a clear error message
- **AND** the error message SHALL include "Failed to download KCL dependencies"
- **AND** the error message SHALL suggest checking network connectivity

#### Scenario: Invalid kcl.mod file
- **WHEN** `kcl mod update` fails due to an invalid kcl.mod syntax
- **THEN** the system SHALL raise a `KCLGenerationError` with a clear error message
- **AND** the error message SHALL include the original KCL error output
- **AND** the error message SHALL suggest validating the kcl.mod file

### Requirement: Generated JSON is valid and parseable
The system SHALL ensure that the JSON output from KCL generators is valid and can be parsed by Terraform.

#### Scenario: JSON validation passes
- **WHEN** KCL generators produce output after `kcl mod update`
- **THEN** the YAML to JSON conversion SHALL succeed
- **AND** the resulting JSON SHALL be parseable by `json.loads()`
- **AND** the JSON SHALL be passed to Terraform without contamination

#### Scenario: Contaminated output detection
- **WHEN** KCL output contains unexpected strings (e.g., git clone messages)
- **THEN** the YAML to JSON conversion SHALL fail
- **AND** the system SHALL raise a `KCLGenerationError` with the contaminated output preview
- **AND** the error message SHALL suggest running `kcl mod update` manually
