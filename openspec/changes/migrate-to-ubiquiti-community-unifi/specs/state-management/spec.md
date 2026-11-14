## ADDED Requirements

### Requirement: Migration state checkpoint is exact and protected
The provider migration MUST record an encrypted, access-restricted pre-handoff state snapshot plus backend version identity and checksum before modifying state.

#### Scenario: Production handoff is about to start
- **WHEN** authorized serialized maintenance ownership and the qualified snapshot lock/version boundary are established
- **THEN** the current state generation MUST be checkpointed and checksum-verified
- **AND** its storage location and content MUST not be printed in traces or reports

### Requirement: Import manifest is complete and secret-free
The migration MUST generate a manifest containing only target resource address, import identity, site, normalized MAC where applicable, and source-state address.

#### Scenario: Manifest is validated
- **WHEN** the production state inventory is transformed
- **THEN** all expected managed clients and DNS records MUST appear exactly once
- **AND** no Cloudflare address, credential, provider configuration value, or unrelated state object may appear

### Requirement: State handoff preserves Cloudflare ownership
Removing and importing UniFi bindings MUST preserve Cloudflare resource identity, provider ownership, and reviewed functional fields without changing remote Cloudflare objects; raw serialized state byte equality MUST NOT be required.

#### Scenario: Handoff completes
- **WHEN** pre- and post-handoff inventories are compared
- **THEN** Cloudflare addresses, IDs, provider ownership, and reviewed functional projections MUST match
- **AND** the full Cloudflare plan MUST report zero changes
- **AND** benign metadata/serialization differences MUST be explained without exposing raw state or weakening functional invariants

### Requirement: State handoff is lock-protected and single-owner
Production handoff MUST exclude competing writers across the maintenance workflow, use actual per-command backend locks and state-generation checks, and MUST NOT leave two active states claiming the same object. Separate CLI invocations MUST NOT be described as one continuously locked transaction.

#### Scenario: Resource is transferred
- **WHEN** its legacy binding is removed
- **THEN** its target import MUST occur within the controlled maintenance workflow
- **AND** each phase MUST verify its expected state generation and retain intent/result receipts
- **AND** failure MUST retain maintenance ownership or explicit operator handover until safe restoration or repair, without claiming a CLI lock remains held

#### Scenario: External writer or interrupted command is detected
- **WHEN** state generation changes unexpectedly, writer exclusion fails, or a command outcome is unknown
- **THEN** the next mutation MUST stop until authoritative state/remote effects and prior process termination are reconciled
- **AND** rollback MUST NOT overwrite a newer generation or blindly retry an uncertain import

### Requirement: Recovery evidence excludes secret-bearing output
Migration diagnostics MUST expose only reviewed non-secret manifest, phase, resource, and result metadata; runtime credentials, raw state, raw plans, and provider credential logs MUST NOT appear in reports or generic artifacts.

#### Scenario: A handoff phase fails
- **WHEN** recovery evidence is retained or a failure is reported
- **THEN** protected snapshots MUST remain encrypted/access-restricted and public diagnostics MUST remain sanitized
