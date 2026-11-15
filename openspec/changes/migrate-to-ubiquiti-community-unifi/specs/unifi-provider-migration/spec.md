## Purpose

Supports a rehearsed, guarded UniFi provider ownership transfer that preserves existing remote resources and safely reconciles uncertain state or provider effects.

## ADDED Requirements

### Requirement: Migration prerequisites are enforced
Production migration MUST NOT begin until hardening, normalized-provider evidence, repaired current-contract tests, and the accepted execution foundation are available with qualified feature evidence and a zero-drift consumer baseline.

#### Scenario: Migration pre-flight runs
- **WHEN** an operator prepares the production provider migration
- **THEN** accepted evidence MUST cover `modernize-legacy-unit-test-contracts`, `modernize-dagger-execution-contracts`, and the existing hardening/normalized-provider baseline
- **AND** the current consumer revision MUST produce 0 add, 0 change, and 0 destroy
- **AND** Cloudflare canary completion or baseline archive MUST NOT be a prerequisite

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
- **AND** controller/site/object checks MUST stop missing-object or wrong-site execution before potentially mutating provider reads/imports

### Requirement: Post-import plan is a hard gate
The migration MUST stop unless the full production plan reports zero changes for both UniFi and Cloudflare.

#### Scenario: Any post-import drift is detected
- **WHEN** the post-import plan reports an add, change, destroy, missing resource, or changed Cloudflare functional field/identity
- **THEN** no production apply MUST run
- **AND** the operator MUST restore or repair state using the recorded rollback checkpoint

### Requirement: Rollback is state-only before mutation
The migration MUST retain an exact encrypted checkpoint and immutable legacy revision for guarded state-only rollback when absence of remote mutation and conflicting writers is established. Import/refresh MUST NOT be assumed read-only, and state restoration MUST NOT be claimed to undo remote effects.

#### Scenario: Import or refresh fails
- **WHEN** failure occurs and authoritative evidence confirms no remote mutation or conflicting newer state
- **THEN** the exact pre-handoff backend version MUST be restorable
- **AND** the consumer MUST be able to repin the normalized legacy revision and regain a zero-drift plan

#### Scenario: Provider effect is unknown or observed
- **WHEN** Read/import may have created a client or another remote effect cannot be excluded
- **THEN** automatic state-only rollback guarantees MUST be withheld
- **AND** execution MUST stop for authoritative reconciliation and separately authorized remote repair if required

### Requirement: Production acceptance and promotion remain explicit
Production state/provider execution MUST require separate scoped operator authorization; qualified feature acceptance MUST precede merge, and matched downstream Dagger/KCL pins MUST be verified independently of routine publication.

#### Scenario: Consumer adopts the provider-bearing revision
- **WHEN** adoption is coordinated with `adopt-modernized-dns-dagger-workspace`
- **THEN** exact feature pins and authorized full-plan acceptance MUST be recorded before merge
- **AND** execution-only foundation adoption MUST NOT be blocked on this later provider handoff
