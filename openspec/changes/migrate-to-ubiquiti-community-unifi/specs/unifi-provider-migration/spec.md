## ADDED Requirements

### Requirement: Migration prerequisites are enforced
Production migration MUST NOT begin until secret/state handling is hardened and the normalized current-provider baseline is published and produces zero drift.

#### Scenario: Migration pre-flight runs
- **WHEN** an operator prepares the production provider migration
- **THEN** both prerequisite OpenSpec changes MUST be complete
- **AND** the current consumer revision MUST produce 0 add, 0 change, and 0 destroy

### Requirement: Sandbox rehearses the exact provider handoff
The migration tooling MUST complete a legacy-create to community-import lifecycle on isolated `solomonhd.ai` resources before operating on production state.

#### Scenario: Sandbox rehearsal succeeds
- **WHEN** the legacy provider has created the run-specific sandbox resources
- **THEN** the tooling MUST snapshot state, remove legacy bindings, import the same live resources through the community provider, and produce zero drift
- **AND** it MUST perform one benign update, destroy through the community provider, and verify every sandbox resource is absent

### Requirement: Production resources are never destroyed for migration
Production ownership transfer MUST use Terraform state removal plus provider-supported import/adoption and MUST NOT invoke destroy for any production UniFi or Cloudflare resource.

#### Scenario: Production resource changes provider ownership
- **WHEN** a legacy UniFi binding is transferred
- **THEN** the remote object MUST remain continuously present
- **AND** the target resource MUST be imported by normalized MAC or `site:id`

### Requirement: Post-import plan is a hard gate
The migration MUST stop unless the full production plan reports zero changes for both UniFi and Cloudflare.

#### Scenario: Any post-import drift is detected
- **WHEN** the post-import plan reports an add, change, destroy, missing resource, or changed Cloudflare fingerprint
- **THEN** no production apply MUST run
- **AND** the operator MUST restore or repair state using the recorded rollback checkpoint

### Requirement: Rollback is state-only before mutation
The migration MUST retain an exact encrypted pre-handoff state checkpoint and immutable legacy revision so a failed import can be rolled back without remote infrastructure changes.

#### Scenario: Import or refresh fails
- **WHEN** failure occurs before any authorized production mutation
- **THEN** the exact pre-handoff backend version MUST be restorable
- **AND** the consumer MUST be able to repin the normalized legacy revision and regain a zero-drift plan
