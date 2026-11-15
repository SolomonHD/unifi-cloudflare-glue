## MODIFIED Requirements

### Requirement: Persistent Local State Directory Parameter
Plan MAY consume protected local-state input for a read-only preview. Public deploy and destroy SHALL require an explicit remote backend and SHALL reject local-state input or missing durable-state selection before generation, initialization or mutation. No operation SHALL promise automatic Directory host write-back. Durable local effects are deferred to separately tracked DLR-1 by operator decision.

#### Scenario: User provides state directory for persistent storage
- **WHEN** local state is selected for a preview
- **THEN** the operation identifies its protected read-only state input and does not claim updated effectful state handoff
- **AND** the interface does not describe a Directory copy as a writable host bind mount

#### Scenario: User omits state directory for ephemeral storage
- **WHEN** neither durable state mode is selected
- **THEN** the interface identifies ephemeral state and restricts effectful use to explicitly disposable owned lifecycles with recovery/cleanup
- **AND** it does not silently deploy production resources with disposable state

### Requirement: State Directory Mounting and Setup
Read-only local preview preparation SHALL preserve the selected root and sibling module layout. Public local apply/destroy SHALL fail before effects; it SHALL NOT replace a durable recovery contract with a returned Secret, Directory copy or cache-retention claim.

#### Scenario: Mount state directory to container
- **WHEN** protected local state is supplied
- **THEN** it becomes a read-only preview input rather than implied host write-through

#### Scenario: Copy module files to state directory
- **WHEN** a combined root references sibling modules
- **THEN** execution preparation retains their relative paths without flattening the root into an incompatible location
- **AND** state contents are not listed or logged as diagnostics

#### Scenario: Set working directory to state directory
- **WHEN** a local-state preview begins
- **THEN** the selected working root can resolve all module dependencies and state location explicitly

### Requirement: Mutual Exclusion Validation
Local-state input and remote backend selection SHALL remain mutually exclusive. Missing durable state selection SHALL NOT silently authorize production effects with ephemeral state.

#### Scenario: User attempts to use both local state directory and remote backend
- **WHEN** a caller provides both local state and S3 backend selection
- **THEN** validation fails nonzero before mutation and explains the valid protected modes

#### Scenario: User uses only remote backend
- **WHEN** a caller selects only a remote backend with valid Secret-typed settings
- **THEN** initialization uses that backend without requiring local state

#### Scenario: User uses only local state directory
- **WHEN** a caller selects local state for public deploy or destroy
- **THEN** validation fails nonzero before generation, initialization or provider mutation
- **AND** the diagnostic points to a remote backend without claiming DLR-1 is complete

#### Scenario: User provides neither (default ephemeral)
- **WHEN** a caller omits durable state selection
- **THEN** only preview or explicitly disposable owned lifecycle use is accepted
- **AND** production mutation fails before dispatch rather than silently creating empty state

### Requirement: Consistent Implementation Across Functions
The current combined deploy, selective modes and destroy SHALL enforce the same remote-only effect contract without requiring removed standalone deployment APIs. Plan SHALL preserve remote root/backend equivalence; local previews remain read-only and do not authorize local effects.

#### Scenario: deploy-unifi supports state directory
- **WHEN** UniFi-only execution uses the current combined interface
- **THEN** it obeys the common protected state contract without restoring deploy_unifi

#### Scenario: deploy-cloudflare supports state directory
- **WHEN** Cloudflare-only execution uses the current combined interface
- **THEN** it obeys that same state contract without restoring deploy_cloudflare

#### Scenario: deploy orchestration function supports state directory
- **WHEN** full deployment supplies local state
- **THEN** it rejects that selection before generation, initialization or effects for either component

#### Scenario: destroy function supports state directory
- **WHEN** cleanup selects the remote backend from an earlier operation
- **THEN** it targets that state identity and preserves recovery metadata after partial cleanup
- **AND** local-state cleanup through the public destroy interface is rejected

### Requirement: Working Directory Behavior
Execution SHALL resolve working roots from scope and state ownership consistently, preserving relative module references and explicit backend paths.

#### Scenario: Working directory for ephemeral mode
- **WHEN** a disposable lifecycle uses ephemeral state
- **THEN** its root and state are owned by that lifecycle and remain available through cleanup or recorded recovery

#### Scenario: Working directory for remote backend mode
- **WHEN** the selected backend is remote
- **THEN** plan and execution use the same root, backend identity and state namespace

#### Scenario: Working directory for persistent local mode
- **WHEN** local state is selected
- **THEN** only a read-only preview is accepted, retaining module dependencies without an updated-state or host-writeback promise

### Requirement: Backend compatibility is preserved
Secret-input migration SHALL preserve supported YAML/HCL configuration semantics, remote address/key/workspace, state lineage and locking behavior without treating malformed input or failed authentication as a reason to select another backend.

#### Scenario: Existing YAML-backed S3 configuration is used
- **WHEN** the caller migrates the same backend settings to Secret-typed input
- **THEN** initialization targets the same address, key, workspace and locking settings
- **AND** no infrastructure change results solely from input transport migration

#### Scenario: Backend validation or authentication fails
- **WHEN** the configured remote backend cannot be initialized
- **THEN** the operation fails before provider effects without falling back to local state

## ADDED Requirements

### Requirement: Partial effects retain recoverable state
Failed or uncertain remote effects SHALL retain a non-secret operation/recovery identity and preserve the configured remote backend as state authority. Unconfirmed remote custody SHALL NOT be reported as successful completion or trigger automatic retry. DLR-1 owns future durable local-state handoff acceptance.

#### Scenario: Apply fails after creating a resource
- **WHEN** execution partially succeeds before failure
- **THEN** reconciliation uses the same remote backend and retained operation identity
- **AND** the operation does not claim remote state recovery succeeded without evidence
- **AND** ordinary summaries and CI artifacts do not expose raw state

#### Scenario: State recovery cannot be confirmed
- **WHEN** a deadline or connection loss prevents confirming state custody
- **THEN** the result identifies the uncertain operation and blocks blind replay until reconciliation
