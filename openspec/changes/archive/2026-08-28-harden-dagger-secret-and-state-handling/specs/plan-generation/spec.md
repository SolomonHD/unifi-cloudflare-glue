## MODIFIED Requirements

### Requirement: Plan Output Formats

The `plan()` function MUST default to exportable artifacts that have been reviewed for secret disclosure, while raw Terraform plan formats MUST require explicit sensitive-artifact acknowledgement.

#### Scenario: Export safe default plan artifacts
- **GIVEN** Terraform has generated plans
- **WHEN** the caller exports the default plan result
- **THEN** the output contains a redacted human-readable plan and aggregated summary for each requested component
- **AND** the output does not contain binary plan files or raw JSON plan files

#### Scenario: Explicitly export sensitive plan artifacts
- **GIVEN** the caller has selected the sensitive-artifact option
- **WHEN** plan generation completes
- **THEN** the output may include Terraform binary and JSON plan files
- **AND** each sensitive artifact is owner-readable only
- **AND** a warning manifest explains that Terraform plans can contain credentials and sensitive values

#### Scenario: Provider credentials are absent from plan inputs
- **GIVEN** Terraform providers require Cloudflare or UniFi authentication
- **WHEN** the plan is generated in either output mode
- **THEN** provider credentials are supplied through provider-supported secret environment variables
- **AND** they are not supplied as Terraform input variables serialized into the plan

### Requirement: Output Directory Structure

The `plan()` function MUST return a `dagger.Directory` whose contents match the selected artifact-sensitivity mode.

#### Scenario: Return safe default directory
- **GIVEN** plan generation completed without sensitive-artifact opt-in
- **WHEN** the user exports the returned directory
- **THEN** the directory contains redacted human-readable plans and `plan-summary.txt`
- **AND** it contains no `.tfplan` or raw plan `.json` files

#### Scenario: Return acknowledged sensitive directory
- **GIVEN** plan generation completed with sensitive-artifact opt-in
- **WHEN** the user exports the returned directory
- **THEN** the directory additionally contains the requested `.tfplan` and JSON files
- **AND** it contains a sensitivity warning manifest

## ADDED Requirements

### Requirement: Plan output has secret-disclosure regression coverage
The plan implementation MUST be tested with sentinel provider credentials to detect disclosure in default artifacts and command output.

#### Scenario: Default plan export is scanned
- **WHEN** automated tests generate and inspect a default plan result with sentinel secrets
- **THEN** no sentinel credential MUST appear in any exported file or captured execution output
