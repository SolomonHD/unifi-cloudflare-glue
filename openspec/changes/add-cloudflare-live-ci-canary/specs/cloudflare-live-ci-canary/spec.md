## Purpose

Provides a trusted DNS-only CI canary with Dagger-owned lifecycle, bounded mutation, protected durable recovery, and verifiable cleanup without exposing infrastructure secrets.

## ADDED Requirements

### Requirement: Live CI uses a dedicated zone-scoped credential
The hosted canary MUST authenticate with a dedicated token restricted to Zone Read and DNS Edit for `solomonhd.ai` and MUST NOT receive Cloudflare Tunnel Edit or access to production zones.

#### Scenario: Workflow authenticates to Cloudflare
- **WHEN** a trusted live-canary job starts
- **THEN** the token MUST come from the protected `cloudflare-live-ci` environment
- **AND** pre-flight MUST confirm the target zone is exactly `solomonhd.ai`

### Requirement: Secrets are unavailable to untrusted workflow code
The live canary MUST NOT execute with Cloudflare secrets in pull-request, fork, or `pull_request_target` contexts.

#### Scenario: Pull request workflow runs
- **WHEN** code is tested from a pull request
- **THEN** only offline tests MUST run
- **AND** no live-canary environment or Cloudflare credential may be requested

#### Scenario: Manual dispatch requests an untrusted ref
- **WHEN** a manual dispatch selects an unapproved branch or revision
- **THEN** the workflow MUST reject it before requesting Cloudflare or Wasabi credentials or executing secret-bearing code

#### Scenario: Explicitly authorized initial feature pilot
- **WHEN** a reviewed feature SHA is authorized for the initial hosted pilot before the workflow exists on main
- **THEN** only that exact SHA, branch and trusted repository push MAY pass the pre-environment gate
- **AND** the environment MUST separately admit only that named feature branch in addition to main
- **AND** temporary admission MUST be removed after a known terminal pilot without enabling recurring effects or trusting PR/dispatch input claims

### Requirement: Canary names are unique and confined
Every record created by hosted CI MUST use a unique `gha-` run prefix and remain below `ci.solomonhd.ai`.

#### Scenario: Test configuration is generated
- **WHEN** a workflow run constructs its record names
- **THEN** each name MUST include bounded timestamp/run identity
- **AND** validation MUST reject any name outside the exact prefix and suffix allowlist before apply or cleanup

### Requirement: DNS CRUD lifecycle is validated
One normal Dagger entry point MUST own create, API/public-DNS validation, update, zero-drift plan, destroy, and API absence verification for only a TXT marker and unproxied CNAME in the existing sandbox zone.

#### Scenario: Trusted canary succeeds
- **WHEN** the TXT and unproxied CNAME fixture is applied
- **THEN** Cloudflare API and bounded public-DNS checks MUST observe the expected values
- **AND** one value update and a subsequent zero-drift plan MUST succeed
- **AND** destroy plus exact-name API queries MUST prove no test record remains

### Requirement: Cleanup failure fails the workflow
Dagger MUST attempt bounded cleanup after handled primary-test failures. Failed cleanup, residual records, or unknown outcomes MUST prevent success and report non-secret identifiers; hard termination MUST NOT be claimed to guarantee finalization.

#### Scenario: Validation fails after apply
- **WHEN** the primary canary step fails after resources exist
- **THEN** the Dagger lifecycle failure path MUST attempt state-based destroy
- **AND** it MUST query exact record names and fail if any remain
- **AND** primary failure and cleanup outcome MUST both remain visible in sanitized reporting

#### Scenario: Runner is terminated during an effect
- **WHEN** cancellation or process death prevents completion/cleanup verification
- **THEN** the run MUST remain unknown or failed with durable recovery identity
- **AND** a later normal run MUST NOT blindly replay it or claim cleanup succeeded

### Requirement: Stale-record janitor is narrowly bounded
A scheduled/manual Dagger janitor MUST limit candidates to run-prefixed sandbox records older than the stale threshold, default to report-only, and require explicit deletion authorization, verified ownership/inactivity, and shared writer fencing before removal.

#### Scenario: Janitor evaluates records
- **WHEN** it lists records in `solomonhd.ai`
- **THEN** it MUST ignore names outside `gha-*.*.ci.solomonhd.ai`
- **AND** it MUST ignore records newer than the job-timeout-plus-buffer threshold
- **AND** deletion mode MUST report and verify each selected record
- **AND** active, unknown, unowned, or unfenced runs MUST be reported rather than deleted solely because of age

#### Scenario: Operator reviews report-only output
- **WHEN** candidate records are presented without deletion authorization
- **THEN** no record MUST be removed
- **AND** later authorized deletion MUST revalidate ownership, prior-writer termination, and exact resource identity

### Requirement: Hosted CI excludes Tunnel mutations
GitHub-hosted live CI MUST NOT create, update, or delete Cloudflare Tunnel or Tunnel configuration resources.

#### Scenario: Full Tunnel integration is needed
- **WHEN** an operator needs to validate Tunnel lifecycle behavior
- **THEN** the test MUST run through the hardened local Dagger integration path with explicitly supplied account-level credentials
- **AND** it MUST not reuse the hosted DNS canary token

### Requirement: Workflow permissions and execution are bounded
The workflow MUST use least-privilege GitHub permissions, a finite timeout, trusted refs, bounded concurrency, and no generic state/plan artifacts. It MUST be a thin adapter for exact CLI setup, runtime secrets, Dagger invocation, and sanitized reporting, not infrastructure lifecycle implementation.

#### Scenario: Live workflow is evaluated
- **WHEN** GitHub Actions loads the job
- **THEN** repository permissions MUST be no broader than read-only contents unless a documented step requires more
- **AND** workflow concurrency MUST use `cancel-in-progress: false` without claiming it fences other callers
- **AND** Terraform state MUST use protected durable recovery and MUST NOT be uploaded as a generic Actions artifact
- **AND** workflow steps MUST NOT implement Terraform or API create/update/destroy/cleanup logic
- **AND** the pilot MUST NOT introduce Dagger Cloud or migrate other CI templates

### Requirement: Recovery survives runner loss in an isolated protected store
Canary state, encrypted protected checkpoints, and run ledgers MUST use a dedicated Wasabi sandbox prefix with isolated per-run keys, scoped runtime credentials, and no production state or credential reuse. Unknown/failed-run evidence MUST survive runner loss until reconciled.

#### Scenario: Run preparation begins
- **WHEN** a canary prepares a possible DNS mutation
- **THEN** exact zone/run/revision identity, intended record names/types, and phase intent MUST be durably recorded before the effect
- **AND** failure to commit or reconcile intent MUST stop mutation

#### Scenario: Recovery material is retained
- **WHEN** state or receipts are stored, reported, or expired
- **THEN** verified encryption, access restrictions, version identity, and reviewed retention MUST protect them
- **AND** unresolved evidence MUST NOT be removed by routine retention or exposed in generic artifacts

### Requirement: Backend semantics and all-writer fencing are qualified
Live mutation MUST be gated on exact Wasabi/backend conditional-write and lock qualification plus writer exclusion across normal runs, janitor, recovery, and external callers. S3 compatibility, Actions concurrency, or lease age alone MUST NOT establish continuous locking or safe takeover.

#### Scenario: Backend or ownership precondition fails
- **WHEN** conditional-write/lock semantics are unsupported or unproven, ownership is lost, or state/ledger generation changes unexpectedly
- **THEN** further effects MUST stop and protected recovery identity MUST be retained
- **AND** no continuous multi-CLI lock guarantee MUST be inferred

#### Scenario: Stale writer may still act
- **WHEN** a prior writer is stalled, expired, or has an uncertain in-flight request
- **THEN** recovery/deletion MUST wait for authoritative prior termination and effect reconciliation
- **AND** inability to establish exclusion MUST fail closed for explicit operator reconciliation

#### Scenario: Non-expiring ownership claim exists
- **WHEN** a run encounters an existing maintenance claim, regardless of its age
- **THEN** it MUST NOT automatically expire, replace or take over that claim
- **AND** ownership revalidation MUST compare the expected owner and generation before further effects
- **AND** recovery MUST require operator-established prior termination and exclusion rather than interpreting age as authority

#### Scenario: Verified completed ownership is handed to a successor
- **WHEN** the owner has observed successful destroy and authoritative API/state absence without pending or unknown receipts
- **THEN** it MUST conditionally create and verify immutable per-run completed history before CAS-marking the active claim completed
- **AND** a successor MUST verify the archive identity, full receipt body and opaque versions before conditional replacement
- **AND** uncertain writes or unverifiable history MUST retain the blocked claim without automatic retry or takeover

### Requirement: Recovery is an explicit separate operation
A separate Dagger reconciliation entry point MUST accept a non-secret run identity, require scoped authorization and runtime credentials, and reconcile durable state/ledger plus exact API identity before guarded cleanup or retry.

#### Scenario: Operator authorizes recovery after hard cancellation
- **WHEN** the named run's prior writer termination and exclusive recovery ownership are established
- **THEN** recovery MUST load protected evidence and reconcile intended names/known IDs, missing or partial state, and uncertain effects
- **AND** unknown ownership MUST stop deletion or retry rather than create duplicates or overwrite a newer generation

### Requirement: Secret channels and diagnostics remain bounded
Cloudflare and Wasabi credentials MUST be supplied through runtime Dagger secret channels. Raw state, plans, credential-bearing configuration, and provider credential logs MUST NOT enter reports, workflow logs, or generic artifacts.

#### Scenario: Lifecycle or recovery fails
- **WHEN** an exception, report, or exported diagnostic is produced
- **THEN** it MUST contain only reviewed non-secret run/resource/phase/outcome metadata
- **AND** sentinel-secret and failure-injection tests MUST verify these boundaries

### Requirement: Execution foundation and live acceptance are explicit gates
Canary implementation MUST consume the accepted repaired baseline and parent's exact qualified CLI/engine/Python SDK tuple, independently of UniFi migration. Scoped live authorization and qualified feature acceptance MUST precede production activation and merge.

#### Scenario: Parent runtime is selected
- **WHEN** `modernize-dagger-execution-contracts` completes exact 1.0 beta qualification or records a 0.21.11 fallback decision
- **THEN** the canary MUST use that accepted exact tuple without guessing a beta version
- **AND** planning completion MUST NOT claim runtime qualification or live execution is complete
