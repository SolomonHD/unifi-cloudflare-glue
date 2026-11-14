## MODIFIED Requirements

### Requirement: Plan Function Signature
The module SHALL accept source, scoped authentication, state selection and explicit tool identity for non-mutating previews. Provider and credential-bearing backend inputs SHALL use secret-typed channels; live freshness SHALL be automatic.

#### Scenario: Plan function accepts authentication parameters
- **WHEN** a caller selects full, UniFi-only or Cloudflare-only planning
- **THEN** only credentials required for that scope are requested, using API-key or complete username/password UniFi authentication and secret Cloudflare tokens
- **AND** insecure TLS requires explicit opt-in

#### Scenario: Plan function accepts state management parameters
- **WHEN** a caller supplies a protected local-state input or remote-backend selection
- **THEN** those modes are mutually exclusive and credential-bearing backend input is Secret-typed with an explicit supported format

#### Scenario: Plan function accepts version control parameters
- **WHEN** no tool override is supplied
- **THEN** accepted exact tool identities are selected rather than latest tags

#### Scenario: Plan function accepts cache control parameters
- **WHEN** the caller supplies no timestamp or cache flag
- **THEN** live observations are fresh automatically without invalidating deterministic source generation

### Requirement: Plan Generation Process
Planning SHALL validate selected configuration and use the same scope, root, backend identity and resource address layout as the corresponding execution path without applying managed-resource changes.

#### Scenario: Generate plans for both modules
- **WHEN** the caller requests the full deployment preview
- **THEN** both configurations are validated and the existing combined-root state is planned once
- **AND** the preview does not create separate states for its component modules

#### Scenario: Plan execution order matches deployment
- **WHEN** the preview is compared with the corresponding execution mode
- **THEN** root, backend, resource addresses and dependency ordering agree
- **AND** incompatible state/root combinations stop before effects

### Requirement: Plan Summary Generation
Planning SHALL provide accurate aggregated add/change/destroy counts and selected-scope metadata from structured action data, with malformed data treated as an error rather than a misleading zero-drift result.

#### Scenario: Generate plan summary file
- **WHEN** planning succeeds
- **THEN** the summary includes scope, add/change/destroy counts, timestamp, resolved Terraform/KCL identities and backend type
- **AND** sensitive plan values are not copied into the summary

#### Scenario: Parse resource counts from plan output
- **WHEN** structured action arrays contain creates, updates, deletes, replacements or no-ops
- **THEN** their string actions are counted correctly, replacements contribute create and delete, and no-ops contribute neither
- **AND** malformed actions fail summary verification instead of falling back to fragile phrase counting

### Requirement: Plan function uses combined Terraform module
Full previews SHALL preserve the existing combined Terraform root. Selective previews SHALL use the same qualified root and state ownership as the corresponding execution mode rather than choosing a different root solely because the operation is plan.

#### Scenario: Plan generation uses combined module
- **WHEN** the caller selects full deployment against the combined state
- **THEN** planning and execution both use the combined root with stable addresses

#### Scenario: Selective root matches state ownership
- **WHEN** a caller selects a standalone component
- **THEN** its preview and execution use the same previously qualified standalone state/root combination or reject an incompatible combination before mutation

### Requirement: Cache Control
Live planning SHALL enforce automatic freshness at function and execution boundaries, without requiring or accepting an ineffective no-cache boolean as a guarantee.

#### Scenario: Force fresh execution with no-cache
- **WHEN** a caller attempts to use the removed no-cache interface
- **THEN** migration guidance identifies automatic live freshness rather than instructing the caller to create timestamps

#### Scenario: Custom cache buster value
- **WHEN** a supported transitional call includes a manual run label
- **THEN** it is handled only as bounded data and freshness is enforced independently

#### Scenario: Mutually exclusive cache control options
- **WHEN** unsupported legacy cache options are supplied
- **THEN** argument validation rejects them before contacting the backend or providers

### Requirement: State Management Consistency
Remote planning SHALL use the same remote-backend/root contract as deploy and destroy, with explicit Secret-typed backend configuration and no automatic host Directory write-back. A protected local-state preview is read-only and SHALL NOT imply support or authorization for local deploy/destroy; durable local effects remain deferred to DLR-1.

#### Scenario: Plan with persistent local state
- **WHEN** a supported local-state preview is requested
- **THEN** it uses the specified state and preserved module layout with explicit protected artifact custody

#### Scenario: Plan with remote backend
- **WHEN** S3 planning is selected with Secret-typed backend settings
- **THEN** initialization and refresh use the existing remote state identity and locking configuration

#### Scenario: Mutually exclusive state options
- **WHEN** both local state and a remote backend are supplied
- **THEN** validation fails nonzero before execution and explains the supported alternatives without disclosing backend contents

### Requirement: Error Handling
Planning SHALL fail nonzero with useful sanitized diagnostics for execution, generation and argument errors, without exposing provider/backend output or proceeding after a required phase fails.

#### Scenario: Terraform plan failure
- **WHEN** Terraform planning fails
- **THEN** command status is unsuccessful, phase/exit metadata is retained and dependent work stops without reproducing raw provider output

#### Scenario: KCL generation failure
- **WHEN** source generation fails validation
- **THEN** planning fails with bounded non-secret validation context before provider operations

#### Scenario: Missing required parameters
- **WHEN** required selected-scope parameters are absent
- **THEN** argument validation fails before backend or provider access

### Requirement: Plan output directory structure
Default plan output SHALL contain reviewed human-readable preview and summary artifacts only. Raw binary and JSON plans SHALL require explicit sensitive-artifact acknowledgement and protected storage.

#### Scenario: Plan output files
- **WHEN** the default result is exported
- **THEN** it contains plan text and an aggregated summary without raw plan JSON, binary state or credentials
- **AND** explicitly acknowledged raw plans retain owner-only permissions and handling warnings

## ADDED Requirements

### Requirement: Preview is not saved-plan execution approval
The interface SHALL state whether execution consumes the exact reviewed plan. A preview followed by independent replanning SHALL NOT be represented as approved saved-plan execution.

#### Scenario: Deploy follows preview
- **WHEN** a caller requests deployment after inspecting a preview
- **THEN** documentation and command guidance explain that deploy replans against fresh state and needs its own authorization
- **AND** raw preview artifacts are not implicitly promoted to execution inputs
