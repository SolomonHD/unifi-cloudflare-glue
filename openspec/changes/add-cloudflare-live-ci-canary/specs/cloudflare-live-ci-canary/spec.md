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

### Requirement: Canary names are unique and confined
Every record created by hosted CI MUST use a unique `gha-` run prefix and remain below `ci.solomonhd.ai`.

#### Scenario: Test configuration is generated
- **WHEN** a workflow run constructs its record names
- **THEN** each name MUST include bounded timestamp/run identity
- **AND** validation MUST reject any name outside the exact prefix and suffix allowlist before apply or cleanup

### Requirement: DNS CRUD lifecycle is validated
The canary MUST create, API-validate, publicly resolve, update, zero-drift plan, destroy, and API-verify its disposable DNS records.

#### Scenario: Trusted canary succeeds
- **WHEN** the TXT and unproxied CNAME fixture is applied
- **THEN** Cloudflare API and bounded public-DNS checks MUST observe the expected values
- **AND** one value update and a subsequent zero-drift plan MUST succeed
- **AND** destroy plus exact-name API queries MUST prove no test record remains

### Requirement: Cleanup failure fails the workflow
Cleanup MUST run regardless of primary-test outcome, and any failed destroy or residual record MUST fail the workflow with non-secret resource identifiers.

#### Scenario: Validation fails after apply
- **WHEN** the primary canary step fails after resources exist
- **THEN** the unconditional cleanup step MUST attempt state-based destroy
- **AND** it MUST query exact record names and fail if any remain

### Requirement: Stale-record janitor is narrowly bounded
A scheduled/manual janitor MUST identify only run-prefixed records below the canary suffix that are older than the configured stale threshold.

#### Scenario: Janitor evaluates records
- **WHEN** it lists records in `solomonhd.ai`
- **THEN** it MUST ignore names outside `gha-*.*.ci.solomonhd.ai`
- **AND** it MUST ignore records newer than the job-timeout-plus-buffer threshold
- **AND** deletion mode MUST report and verify each selected record

### Requirement: Hosted CI excludes Tunnel mutations
GitHub-hosted live CI MUST NOT create, update, or delete Cloudflare Tunnel or Tunnel configuration resources.

#### Scenario: Full Tunnel integration is needed
- **WHEN** an operator needs to validate Tunnel lifecycle behavior
- **THEN** the test MUST run through the hardened local Dagger integration path with explicitly supplied account-level credentials
- **AND** it MUST not reuse the hosted DNS canary token

### Requirement: Workflow permissions and execution are bounded
The workflow MUST use least-privilege GitHub permissions, a finite timeout, serialized live execution, and no uploaded Terraform state.

#### Scenario: Live workflow is evaluated
- **WHEN** GitHub Actions loads the job
- **THEN** repository permissions MUST be no broader than read-only contents unless a documented step requires more
- **AND** concurrency MUST prevent overlapping canary mutation windows
- **AND** Terraform state MUST remain ephemeral and MUST NOT be uploaded as an artifact
