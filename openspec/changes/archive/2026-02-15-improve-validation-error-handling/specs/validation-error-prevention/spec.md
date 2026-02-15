## ADDED Requirements

### Requirement: Empty JSON files are not written when validation fails
When KCL validation fails, the system SHALL NOT write empty or placeholder JSON files that would cause Terraform errors.

#### Scenario: Validation failure prevents file write
- **WHEN** KCL validation detects errors and returns an empty result object
- **THEN** the system SHALL NOT write the empty JSON to unifi.json or cloudflare.json files

#### Scenario: Existing valid files are preserved
- **WHEN** validation fails and valid JSON files from a previous run exist
- **THEN** the system SHALL preserve the existing files rather than overwriting with empty content

#### Scenario: File absence indicates validation failure
- **WHEN** validation fails and prevents JSON file creation
- **THEN** the absence of output files SHALL serve as an indicator that validation failed

### Requirement: Validation state is explicitly communicated
The system SHALL explicitly communicate validation state through the GenerateResult structure and error handling.

#### Scenario: GenerateResult indicates validation failure
- **WHEN** the generate() function detects validation errors
- **THEN** the GenerateResult SHALL have:
  - `valid` field set to False
  - `errors` field populated with validation error details
  - `unifi_json` and `cloudflare_json` fields either empty or containing error metadata

#### Scenario: Error detection before Terraform execution
- **WHEN** validation fails during KCL generation
- **THEN** the system SHALL fail with a clear error before Terraform attempts to read the generated JSON

#### Scenario: CI/CD pipeline failure on validation error
- **WHEN** validation fails in an automated pipeline
- **THEN** the pipeline SHALL fail with exit code indicating validation failure

### Requirement: Error metadata replaces empty JSON when helpful
When validation fails, the system SHALL write JSON files containing error metadata instead of empty objects, if it improves error visibility.

#### Scenario: Error metadata JSON structure
- **WHEN** validation fails and error metadata is written to JSON
- **THEN** the JSON SHALL contain a clear structure indicating:
  - Validation failed
  - Error details
  - Timestamp of failure
  - Suggestion to check KCL output for details

#### Scenario: Terraform detects error metadata
- **WHEN** Terraform reads JSON with error metadata
- **THEN** Terraform SHALL fail with a clear error message referencing the validation failure

### Requirement: Dagger functions handle validation errors appropriately
Dagger functions that call KCL generation SHALL detect validation failures and return appropriate error messages.

#### Scenario: Dagger detects KCL validation failure
- **WHEN** a Dagger function executes KCL and validation fails
- **THEN** the Dagger function SHALL:
  - Detect the validation failure from the GenerateResult
  - Return an error string with validation details
  - NOT proceed with file writes or Terraform operations

#### Scenario: Dagger error message includes KCL errors
- **WHEN** validation fails within a Dagger pipeline
- **THEN** the Dagger function output SHALL include the KCL validation error messages

### Requirement: Validation-only mode is available
The system SHALL provide a way to validate configuration without generating output files.

#### Scenario: Validate-only execution
- **WHEN** user runs generation in validation-only mode
- **THEN** the system SHALL:
  - Execute all validation checks
  - Report validation results
  - NOT write any JSON files

#### Scenario: Pre-deployment validation check
- **WHEN** validation-only mode is used in CI/CD
- **THEN** the pipeline can verify configuration correctness before attempting deployment
