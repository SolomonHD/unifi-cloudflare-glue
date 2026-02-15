## ADDED Requirements

### Requirement: KCL execution provides detailed error messages
When KCL execution fails, the system SHALL provide detailed error information including exit code, stdout, stderr, and actionable hints.

#### Scenario: KCL syntax error
- **WHEN** `generate_unifi_config()` or `generate_cloudflare_config()` is called with invalid KCL syntax
- **THEN** the system SHALL raise `KCLGenerationError` with:
  - Exit code from KCL process
  - Full stdout content (if any)
  - Full stderr content with actual error message
  - Actionable hint suggesting local debugging with `kcl run generators/<name>.k`

#### Scenario: KCL file not found
- **WHEN** the generator file is missing or inaccessible
- **THEN** the system SHALL raise `KCLGenerationError` with a clear message indicating which generator file was not found

### Requirement: Empty KCL output is detected and reported
When KCL produces empty or whitespace-only output, the system SHALL provide specific error messages explaining possible causes.

#### Scenario: Empty generator output
- **WHEN** KCL runs successfully but produces no output
- **THEN** the system SHALL raise `KCLGenerationError` with a message explaining possible causes:
  - Generator file is empty
  - KCL module has no output statements
  - All configurations are commented out

### Requirement: yq conversion failures show problematic YAML
When yq fails to convert KCL YAML output to JSON, the system SHALL display the actual KCL output that failed to parse.

#### Scenario: Invalid YAML from KCL
- **WHEN** KCL produces output that yq cannot parse as valid YAML
- **THEN** the system SHALL raise `KCLGenerationError` with:
  - The specific yq error message
  - The problematic KCL output (truncated to 1000 characters if necessary)
  - Possible causes (validation warnings, invalid YAML structure, syntax errors)
  - Actionable hint to run KCL locally to see raw output

#### Scenario: Large output with parsing error
- **WHEN** KCL produces output larger than 1000 characters that fails yq parsing
- **THEN** the system SHALL truncate the output display to 1000 characters with an ellipsis indicator

### Requirement: JSON validation continues to work after conversion
After successful yq conversion, the system SHALL validate the resulting JSON and provide clear error messages if invalid.

#### Scenario: Invalid JSON after yq conversion
- **WHEN** yq produces output that is not valid JSON
- **THEN** the system SHALL raise `KCLGenerationError` with:
  - The JSON parse error details
  - A preview of the invalid output (first 500 characters)

#### Scenario: Successful JSON validation
- **WHEN** yq produces valid JSON output
- **THEN** the system SHALL return the JSON as a `dagger.File` object without errors

### Requirement: Container reference is preserved through multi-step execution
The system SHALL properly preserve container references when executing multiple commands in sequence.

#### Scenario: Multi-step KCL processing
- **WHEN** the system executes KCL, writes output to a file, and runs yq on that file
- **THEN** the container reference SHALL be preserved after each step to ensure file accessibility

### Requirement: Error message format consistency
All error messages SHALL follow a consistent format using the `✗` prefix and provide structured information.

#### Scenario: KCL execution error format
- **WHEN** any KCL-related error occurs
- **THEN** the error message SHALL:
  - Start with `✗` followed by the error category (e.g., "✗ KCL execution failed:")
  - Include relevant technical details
  - End with an actionable hint for resolution
