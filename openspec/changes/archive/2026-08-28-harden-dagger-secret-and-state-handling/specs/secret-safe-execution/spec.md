## ADDED Requirements

### Requirement: Secrets remain on secret-typed channels
The Dagger module MUST keep backend credentials, provider tokens, API keys, usernames, and passwords on Dagger secret variables or secret-file mounts from ingestion through cleanup.

#### Scenario: Secret is used by Terraform or an API validator
- **WHEN** a Terraform or validation container requires a credential
- **THEN** the credential MUST be supplied through a Dagger secret environment variable or secret-file mount
- **AND** application code MUST NOT interpolate its plaintext value into a command, ordinary file, cache key, or report

### Requirement: Observable output excludes secret values
Execution traces, stdout, stderr, returned reports, exceptions, and exported default artifacts MUST NOT contain supplied secret values.

#### Scenario: Sentinel credentials exercise success and failure paths
- **WHEN** tests execute success, provider-error, validation-error, timeout, and cleanup-error paths with sentinel secrets
- **THEN** no sentinel value MUST appear in captured output, returned values, exception text, or exported default artifacts

### Requirement: Sensitive artifacts require explicit handling
Artifacts that Terraform documents as potentially containing secrets MUST NOT be included in the default export and MUST require explicit caller acknowledgement.

#### Scenario: Caller requests raw plan artifacts
- **WHEN** the caller explicitly enables sensitive plan artifact export
- **THEN** the output MUST identify the artifacts as sensitive
- **AND** the artifacts MUST be owner-readable only
- **AND** the report MUST provide secure storage and disposal guidance without displaying their contents
