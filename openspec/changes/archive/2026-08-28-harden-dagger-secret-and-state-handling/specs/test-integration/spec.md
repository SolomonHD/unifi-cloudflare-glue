## ADDED Requirements

### Requirement: Integration outcomes are machine-actionable
The integration function MUST fail the Dagger call when creation, validation, timeout enforcement, cleanup, or residual-resource verification fails.

#### Scenario: Validation reports a missing resource
- **WHEN** a resource expected after apply cannot be verified
- **THEN** the integration call MUST finish cleanup attempts
- **AND** it MUST return a failing Dagger outcome rather than a successful report string

### Requirement: Cleanup is guaranteed and verified
The integration function MUST attempt cleanup for every resource recorded as created and MUST verify that externally visible test resources are absent afterward.

#### Scenario: Primary test step fails after one provider applied
- **WHEN** one provider has created resources and a later test step fails
- **THEN** cleanup MUST run from the captured state for the created resources
- **AND** cleanup failure or residual resources MUST be included as non-secret failure context

### Requirement: Integration timeout is enforced
The integration function MUST parse and enforce its declared test timeout while preserving a bounded cleanup opportunity.

#### Scenario: Test work exceeds the configured timeout
- **WHEN** creation or validation exceeds `test_timeout`
- **THEN** the primary operation MUST be cancelled or failed
- **AND** cleanup MUST receive its bounded reserve
- **AND** the final result MUST indicate a timeout failure

### Requirement: Integration validation uses secret channels
Cloudflare and UniFi validation MUST use secret variables or secret files without extracting credentials into Python strings or command arguments.

#### Scenario: Cloudflare API validation executes
- **WHEN** the harness queries the Cloudflare API
- **THEN** the authorization credential MUST come from a Dagger secret variable
- **AND** the trace and report MUST contain only the test resource identifiers
