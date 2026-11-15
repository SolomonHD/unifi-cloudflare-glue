# secret-safe-execution Specification

## Purpose
Protect supplied and generated credentials throughout execution, diagnostics and explicit sensitive-artifact handling.
## Requirements
### Requirement: Secrets remain on secret-typed channels
Backend credentials, provider tokens, API keys, usernames and passwords MUST remain on secret-typed channels from ingestion through cleanup. Credential-bearing backend configuration MUST NOT enter as an ordinary File and become secret only after a plaintext application read.

#### Scenario: Secret is used by Terraform or an API validator
- **WHEN** an execution or validation container needs a credential
- **THEN** it receives a secret environment variable or owner-only secret-file mount
- **AND** plaintext is absent from ordinary files, command arguments, cache keys and reports

#### Scenario: Backend YAML or HCL is supplied
- **WHEN** a caller provides credential-bearing backend settings
- **THEN** the selected format is delivered and validated on a secret-typed path
- **AND** conversion errors do not print input or silently reinterpret malformed content

### Requirement: Observable output excludes secret values
Execution traces, stdout, stderr, returned reports, exceptions and default artifacts MUST exclude supplied secrets. Behavioral tests MUST execute real success and failure paths rather than infer safety only from source patterns.

#### Scenario: Sentinel credentials exercise success and failure paths
- **WHEN** synthetic credentials traverse success, provider error, validation error, timeout and cleanup error paths
- **THEN** no sentinel value appears in captured output, exceptions, returned reports or default exported files
- **AND** phase, exit status and safe recovery guidance remain usable

### Requirement: Sensitive artifacts require explicit handling
Artifacts that Terraform documents as potentially containing secrets MUST NOT be included in the default export and MUST require explicit caller acknowledgement.

#### Scenario: Caller requests raw plan artifacts
- **WHEN** the caller explicitly enables sensitive plan artifact export
- **THEN** the output MUST identify the artifacts as sensitive
- **AND** the artifacts MUST be owner-readable only
- **AND** the report MUST provide secure storage and disposal guidance without displaying their contents

### Requirement: Generated credentials have explicit disclosure boundaries
Newly generated tunnel credentials MUST remain secret-oriented outputs or require an explicitly selected protected disclosure path instead of ordinary default reports.

#### Scenario: Caller inspects a deployment result
- **WHEN** deployment or credential verification completes
- **THEN** default output provides only non-secret identifiers and success/status information
- **AND** generated credential values are not included in the normal human-readable or JSON report
