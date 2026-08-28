## ADDED Requirements

### Requirement: Backend configuration is mounted as a secret
Remote-backend configuration containing credentials MUST be delivered to Terraform as a Dagger secret-file mount and MUST NOT be recreated as an ordinary file from its plaintext contents.

#### Scenario: S3 backend file is supplied
- **WHEN** a caller supplies an S3 backend configuration file
- **THEN** the module MUST make the configuration available at the Terraform backend path through a secret mount
- **AND** the Dagger trace, cache metadata, report, and error output MUST NOT contain the file contents

### Requirement: Backend compatibility is preserved
Secret mounting MUST preserve the supported backend configuration formats and state-locking behavior.

#### Scenario: Existing YAML-backed S3 configuration is used
- **WHEN** the existing S3 backend YAML file is passed to plan, deploy, or destroy
- **THEN** Terraform initialization MUST use the same backend address, key, and locking behavior
- **AND** no managed infrastructure change MUST result solely from the transport hardening
