## ADDED Requirements

### Requirement: Migration state checkpoint is exact and protected
The provider migration MUST record an encrypted, access-restricted pre-handoff state snapshot plus backend version identity and checksum before modifying state.

#### Scenario: Production handoff is about to start
- **WHEN** the backend lock is acquired
- **THEN** the current state generation MUST be checkpointed and checksum-verified
- **AND** its storage location and content MUST not be printed in traces or reports

### Requirement: Import manifest is complete and secret-free
The migration MUST generate a manifest containing only target resource address, import identity, site, normalized MAC where applicable, and source-state address.

#### Scenario: Manifest is validated
- **WHEN** the production state inventory is transformed
- **THEN** all expected managed clients and DNS records MUST appear exactly once
- **AND** no Cloudflare address, credential, provider configuration value, or unrelated state object may appear

### Requirement: State handoff preserves Cloudflare ownership
Removing and importing UniFi bindings MUST leave Cloudflare state entries and remote objects unchanged.

#### Scenario: Handoff completes
- **WHEN** pre- and post-handoff inventories are compared
- **THEN** Cloudflare resource addresses, IDs, and recorded fingerprints MUST be identical
- **AND** the full Cloudflare plan MUST report zero changes

### Requirement: State handoff is lock-protected and single-owner
Production state operations MUST execute under backend locking and MUST NOT leave two persistent states claiming the same UniFi object.

#### Scenario: Resource is transferred
- **WHEN** its legacy binding is removed
- **THEN** its target import MUST occur within the controlled maintenance workflow
- **AND** failure MUST trigger checkpoint restoration or explicit repair before the lock is released
