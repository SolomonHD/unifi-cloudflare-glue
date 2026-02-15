## ADDED Requirements

### Requirement: Validation errors are prominently displayed
When KCL validation fails, the system SHALL display validation errors prominently in the output with clear formatting that distinguishes them from successful execution.

#### Scenario: Validation failure output visibility
- **WHEN** KCL validation detects one or more errors
- **THEN** the system SHALL output validation errors with clear visual markers (e.g., "✗" prefix or "VALIDATION FAILED" header)

#### Scenario: Multiple validation errors
- **WHEN** multiple validation errors occur simultaneously
- **THEN** the system SHALL display all validation errors in a structured list format

#### Scenario: Validation success indication
- **WHEN** KCL validation passes without errors
- **THEN** the system SHALL indicate successful validation (e.g., "✓" prefix or "VALIDATION PASSED" message)

### Requirement: Error messages include actionable guidance
Each validation error message SHALL include specific guidance on how to resolve the error.

#### Scenario: MAC consistency error guidance
- **WHEN** a MAC consistency error occurs (Cloudflare tunnel references MAC not found in UniFi devices)
- **THEN** the error message SHALL include:
  - The missing MAC addresses
  - The list of available UniFi MAC addresses
  - Suggestion to either add UniFi devices with the missing MACs or update tunnel configurations

#### Scenario: Duplicate hostname error guidance
- **WHEN** duplicate friendly_hostnames are detected
- **THEN** the error message SHALL include:
  - The list of duplicate hostnames
  - Which devices have conflicting hostnames
  - Suggestion to use unique friendly_hostnames for each device

#### Scenario: Duplicate public hostname error guidance
- **WHEN** duplicate public_hostnames are detected across tunnel services
- **THEN** the error message SHALL include:
  - The list of duplicate public hostnames
  - Which tunnels/services have conflicting public hostnames
  - Suggestion to use unique public_hostnames for each tunnel service

#### Scenario: Domain syntax error guidance
- **WHEN** local_service_url values fail RFC 1123 domain validation
- **THEN** the error message SHALL include:
  - The invalid service URLs
  - Examples of valid domain formats (e.g., http://service.internal.lan:8080)
  - Explanation that internal domains (.internal.lan, .local, .home) or public domains are required

### Requirement: Error messages use consistent formatting
All validation error messages SHALL follow a consistent format for readability and parseability.

#### Scenario: Error format structure
- **WHEN** a validation error is displayed
- **THEN** the error message SHALL include:
  - Error category (e.g., "MAC_CONSISTENCY_ERROR", "DUPLICATE_HOSTNAME_ERROR")
  - Human-readable error message
  - Specific details about what failed
  - Actionable suggestion for resolution

#### Scenario: Structured error output for tooling
- **WHEN** validation errors are output
- **THEN** errors SHALL be formatted in a way that can be parsed by CI/CD tools and text processors

### Requirement: Error output is displayed before JSON file operations
Validation error output SHALL be displayed immediately when detected, before any file write operations.

#### Scenario: Early error display
- **WHEN** validation fails during KCL execution
- **THEN** error messages SHALL be displayed to stderr or stdout before attempting to write JSON files

#### Scenario: Error visibility in containerized environments
- **WHEN** KCL runs in a Dagger container
- **THEN** validation errors SHALL be captured and displayed in the Dagger function output
