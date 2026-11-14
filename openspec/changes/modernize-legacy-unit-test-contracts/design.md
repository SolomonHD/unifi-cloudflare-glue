## Context

The hardening implementation passes its focused secret, lifecycle, type/compile, KCL, and Terraform checks, but the repository-wide unit run includes older suites written for contracts that later changes removed or split. In particular, deployment-guidance tests instantiate a deleted `deploy_cloudflare()` path, while generator-output tests mix the standalone generator `result` contract with a consumer `main.k` contract that exports `unifi_output` and `cf_output`.

Repair the supported current surface before changing execution contracts. `modernize-dagger-execution-contracts` may qualify an exact 1.0 beta CLI/engine/Python SDK tuple in parallel, with a recorded 0.21.11 stable fallback decision, but its execution refactor waits for this baseline. Provider migration and Cloudflare canary then independently extend that foundation.

## Goals / Non-Goals

**Goals:**

- Restore one green, authoritative offline verification baseline before the execution refactor and dependent implementation.
- Make tests describe supported public Dagger and KCL contracts.
- Retain the hardening regression coverage and keep offline verification credential-free.
- Remove stale exclusions and finish repository-wide Python formatting.

**Non-Goals:**

- Restore deleted standalone deployment functions solely to satisfy old tests.
- Change infrastructure, provider state, production credentials, or live-test policy.
- Introduce future provider schemas, change the Dagger runtime, or constrain later fixtures beyond preserving supported behavior and security coverage.

## Decisions

### 1. Establish the baseline before refactoring

Use the implemented hardening and normalized legacy-provider behavior as inputs. Capture current failures and repair tests against existing supported APIs without waiting for migration, canary, archive, or the parent's runtime qualification. Record the accepted baseline revision for dependent changes.

Alternative considered: repair tests last. Rejected because it would let broad refactoring and provider work proceed without an authoritative regression signal. Future changes update their own tests; no temporary compatibility APIs are added.

### 2. Test supported behavior instead of preserving historical entry points

Deployment-guidance coverage moves to the combined `deploy()` function and its component-selection flags. Tests for removed standalone functions are deleted or rewritten; production code does not gain compatibility wrappers merely for the suite.

Generator tests separate two contracts: standalone generator modules expose their sample output as `result`, while Dagger generation consumes purpose-built KCL fixtures exporting the documented consumer keys. Tests do not run the repository library `main.k` as though it were a consumer configuration.

Test real transformations using varied MAC inputs, service distribution, empty/multiple NIC cases, and DNS-loop prevention; do not merely validate pre-normalized expected strings or manually raise the same errors the test asserts. Guidance tests cover full and selective scope, one combined Terraform execution, backend/state parameters, and absence of success guidance on failure. Guidance contains references/instructions, never resolved credentials or raw state.

### Approved contract fixes (2026-11-14)

After reviewing the initial test-only gaps, the operator explicitly approved the
recommended focused production fixes and corresponding specification revision:

- Dagger `Directory`/`File` inputs do not expose original host paths. Guidance
  therefore uses shell-quoted, clearly labeled path placeholders and instructs
  callers to reuse deployment inputs. Account, zone, and backend selections
  remain actual supplied values. Do not add path-hint parameters or pretend that
  conventional paths are recovered caller paths.
- Validate provider output objects and required/nested field types against the
  existing Terraform input contracts before returning generated files. Preserve
  legitimate optional fields and empty collections. Reject malformed output
  with `KCLGenerationError` naming the field path and expected/found type, never
  the offending value or full configuration. Add no validation dependency.
- Enforce the existing DNS-loop rule on resolved origins in KCL generation,
  covering explicit services and entity-generated/fallback URLs. Reject the
  zone apex and its subdomains before output, including case/trailing-dot
  variants; retain unrelated names and internal domains. Fail with an actionable
  tunnel/service location rather than silently dropping services.
- Preserve full deployment's combined module and selective deployment's current
  provider module selection. Every scope still runs only one Terraform cycle;
  reconciliation does not restore separate-phase orchestration.

### 3. Establish one complete offline verification baseline

The change records and runs a single documented command sequence covering formatting, type/compile checks, the full unit suite, and KCL schema/generator checks. Hardening sentinel and failure-injection tests remain included. Live infrastructure tests stay separately authorized and are not required for the offline baseline.

Here offline means credential-free and without live infrastructure calls. Document exact bootstrap/tool prerequisites and distinguish initial dependency acquisition from offline verification; do not falsely promise an air-gapped fresh install. The existing task runner or a minimal wrapper may expose the sequence, without waiting for later CI-template migrations.

## Risks / Trade-offs

- [Later changes alter an accepted contract] -> Require each dependent change to extend this baseline and rerun it, rather than preserving obsolete mocks or deferring failures.
- [Deleting obsolete tests reduces accidental coverage] → Map each removed test to a supported behavior test or explicitly document why the behavior no longer exists.
- [A green suite masks skipped legacy tests] → Inventory skips, xfails, and marker exclusions and permit only documented live-integration boundaries.
- [Formatting creates a broad diff] → Isolate mechanical formatting from behavioral test rewrites where practical and verify with `git diff --check`.

## Migration Plan

1. Confirm the existing hardening and normalized provider baseline; record the current supported contracts without an archive prerequisite.
2. Capture the full failing-test and formatting inventory without credentials.
3. Reconcile requirements, fixtures, mocks, and tests with current supported APIs; preserve unrelated deployment documentation.
4. Run the complete offline baseline and strict OpenSpec validation.
5. Record accepted results and revision for the parent before execution refactoring; perform no infrastructure mutation.

Rollback reverts the focused guidance/validation, test, formatting, and specification changes; no provider state or managed resource rollback is involved.

## Closeout

- Commit/push, review, merge, specification sync, and archive are separate closeout actions, not implementation completion. Do not merge before applicable feature acceptance, and do not archive `normalize-current-unifi-provider-baseline` as part of this change.
- Main-spec structural repair and read-only merge preflight are included in this implementation, preserving historical/pending requirements. Specification sync and archive remain separate lifecycle work. The existing `rules.general` YAML defect in project config is unchanged.

## Implementation Evidence (2026-11-14)

- Starting revision: `6d87ec01164fb338c33ee02cf755a491dc745ef3`; branch
  `modernize-legacy-unit-test-contracts` created and pushed to origin before edits.
  Existing dirty planning changes in this and other changes were preserved.
- Prior hardening and normalized-provider evidence is retained in
  `docs/unifi-provider-baseline.md`: archived hardening, rotated credentials,
  zero-drift safe production plans and isolated provider lifecycle acceptance.
  This change does not rerun live checks or imply fresh infrastructure approval.
- Supported APIs: `deploy()` and selection flags, one Terraform execution,
  standalone generators' `result`, consumer `unifi_output` / `cf_output`.
  No removed deployment wrapper or consumer output is added to library `main.k`.
- This baseline remains before execution refactoring and provider/canary
  implementation. Exact beta qualification may proceed separately; no archive,
  provider migration, or runtime selection is required to repair these tests.
- Initial full unit inventory: **15 failed, 75 passed, 29 setup errors**, with
  zero skips, xfails, or marker exclusions. Failures are removed deployment
  methods/stale mocks and library-as-consumer output assumptions. The first
  direct `.venv/bin/python -m pytest` failed because pytest was not installed;
  `uv run --with ...` provided isolated verification tools without project
  dependency edits.
- Initial Black check failed four files: backend parser, backend tests, guidance
  tests, generator tests. isort failed six files: those four plus main module
  and secret-safety tests. No formatting failures were excluded.
- Initial mypy invocation needed PyYAML stubs and reported the direct-module
  fallback import missing. Added a narrowly scoped `import-not-found` ignore
  beside the existing fallback-only `no-redef` ignore; normal package imports
  remain checked. `uv run --with mypy --with types-PyYAML mypy src/main` and
  Python compilation subsequently passed without changing project configuration.
- KCL 0.12.4 standalone generators and all four existing root check files
  execute successfully. `kcl test` reports **no test files**, so it is not an
  adequate baseline. Root check files now assert their results; the documented
  wrapper executes them explicitly rather than treating printed booleans as a
  passing test.
- Main-spec structural repair preserves 17 guidance and 10 generator current
  requirements, including pending historical obligations; prior removal notes
  are retained separately. Both affected main specs pass strict validation.
  No deltas were synced, no change archived, and `rules.general` remains
  unchanged (the CLI warns about its pre-existing unquoted YAML scalars).
- Archive spec-merge preflight used OpenSpec 1.16.1's read-only
  `findSpecUpdates` / `buildUpdatedSpec` and in-memory `Validator` APIs, not the
  archive command. Strict baseline and simulated merged validation passed:
  guidance 17 -> 19 requirements (3 added, 1 modified, 1 removed), generators
  10 -> 13 (3 added), new offline baseline 0 -> 4. No merge warnings. This is
  spec-merge compatibility evidence, not authorization or full lifecycle archive.
- Guidance test mapping: old standalone header/command/parameters/local/remote/
  persistent/install/documentation/separators cases now use the parameterized
  combined success suite. Full success/source assertions now use that suite and
  the three-scope one-init/apply test. Old separate UniFi-success/Cloudflare-fail
  mocks now use six combined init/apply failure cases. The raw Terraform output
  instruction test was removed: supported guidance recommends `get-tunnel-secrets`
  with `env:CF_TOKEN`, not raw state. Missing-input, selection-conflict, generation,
  backend and state failures add coverage. The guidance suite passes 30 cases;
  guidance plus existing security/provider regressions passes 59, zero skips,
  xfails or exclusions.
- Independently reran all 21 secret-safety sentinel/failure-injection cases and
  8 normalized-provider cases with the pinned offline environment: **29 passed**,
  no skips, xfails, deselections or infrastructure credentials. Existing warnings
  concern unset pytest-asyncio fixture-loop scope and anyio's deprecated pytest
  `CallSpec2` import; no project configuration was changed to suppress them.
- Generator mapping: all 12 UniFi and 11 Cloudflare field/type tests now validate
  actual standalone `result` and both public consumer-generation results against
  nested Terraform shapes. Four real MAC inputs replace expected-string
  normalization self-checks. Empty-device/tunnel/service, multi-NIC and distribution
  placeholders now execute option-driven KCL transformations, including aliases,
  hostname resolution and provider-specific empty-NIC boundaries. Missing-main
  and manually raised missing-key tests now exercise public `KCLGenerationError`
  paths. Library-as-consumer fixtures are replaced. Hand-crafted validation-error,
  `assert True`, marker-only and import-self tests were removed because they
  tested no supported behavior; actual generator tests carry the marker.
- Malformed fixtures expose acceptance of wrong `devices`/`tunnels` types;
  these two characterization cases are evidence of the unresolved production
  gap, not rejection acceptance. DNS tests call the real predicate for five
  safe/unsafe origin examples, not fabricated exceptions. The local transport
  executes KCL but models yq extraction/encoding with YAML/JSON and does not
  perform image bootstrap or downloads. It is not live Dagger/yq qualification.
- Initial complete `bash scripts/verify-offline.sh`: **114 passed**, no skips,
  xfails or deselections; Black/isort across all eight Python files, mypy all
  three production Python files, compilation and all seven KCL entry points
  passed. Strict change validation and `git diff --check` passed. The first
  wrapper attempt exposed the formatter moving a fallback-import ignore to the
  wrong line; it was moved to the import statement and the full sequence rerun.
  The same two existing dependency/configuration warnings remain visible.
- Skip/exclusion audit: no `skip`, `skipif`, `xfail`, or explicit deselection in
  `tests`; no pytest `addopts` exclusion in project configuration; the generator
  marker labels real tests but the wrapper does not filter by it. Live
  `test-integration` remains outside this offline command and retains the
  separate infrastructure authorization documented in `CONTRIBUTING.md`.
- This green current-behavior suite is not accepted completion of the four
  blocked contract tasks below, nor a committed baseline revision for dependent
  implementation. No implementation commit/push, merge, spec sync or archive was
  performed; origin currently holds the pre-implementation branch revision.

### Initial Pause (Resolved Scope Decision)

The initial scope question was dismissed and the first implementation paused at
13/17 tasks. The operator subsequently requested potential fixes and explicitly
approved the recommendations above. The following records the original gaps,
not current completion evidence; final verification is recorded separately.

- `deploy()` receives opaque Dagger `Directory`/`File` objects, not their original
  host paths. Current guidance substitutes `./kcl` (full), `.` (Cloudflare-only),
  `./backend.hcl`, and `./terraform-state`. The new tests verify actual account,
  zone and backend selections and current path conventions, but cannot establish
  exact original-path fidelity required by tasks 2.1/2.3. A reviewed API/behavior
  decision is needed, such as explicit non-secret path hints. Merely relabeling
  examples would not satisfy the existing exact-path requirement.
- Public `generate_*_config()` checks JSON syntax, not Terraform structure.
  Valid JSON scalars/wrong structures can pass. Generator DNS-loop helpers also
  return validation decisions without being invoked by the generation path.
  Tests must distinguish current helper behavior from enforced rejection. New
  production validation/enforcement requires separate approval; green test-only
  coverage is not complete acceptance of those requirements.

### Approved Follow-up Verification

- Revised the guidance deltas to require clearly labeled shell-quoted path
  placeholders, actual known account/zone/backend selections, and reuse-input
  instructions, rather than unavailable original host paths. Reconciled the
  full/selective module requirements and supported Dagger/install options;
  historical scenario identities remain intact for archive compatibility.
- Both success paths now emit the same explicit source placeholder and applicable
  backend/state placeholders. Tests reject the prior conventional-path claims
  and verify module selection and exactly one init/apply cycle for each scope.
  All **30 guidance cases pass**; strict change validation passes.
- Public generation now validates root/provider fields, nested device/NIC/tunnel/
  service objects, string-list members and normalized MAC formats before export.
  Positional tunnel paths avoid echoing arbitrary map keys; malformed structure
  diagnostics contain only field paths and expected/found types. JSON syntax
  failures now report line/column without payload previews or exception chaining.
  The generator suite passes **120 cases**, including real public rejection,
  missing/null/type/format cases, optional/nullable/empty preservation and secret
  sentinel checks. No test-only validator manufactures production rejection.
- KCL generation now rejects explicit and entity-derived public-zone origins,
  including overrides, unsafe fallbacks, case/root-dot variants and URLs whose
  path/query contains another scheme. Host parsing splits only the first scheme
  delimiter, so a path cannot disguise the actual authority. Safe unrelated
  domains, internal domains and original emitted URLs remain intact. Entity
  output now includes the normalized tunnel MAC required by the existing public
  output contract; both safe entity and fallback results pass public validation.
  The DNS suite passes **52 cases**, including failure before yq/file creation.
- The first integration baseline passed all 263 Python cases but correctly failed
  a legacy KCL check that treated a single terminal DNS root dot as invalid.
  Reconciled that check with the approved root-dot handling: a single root dot
  is valid; repeated trailing dots remain rejected. No check was skipped.
- Final serial `bash scripts/verify-offline.sh` passes: **263 tests**, no skips,
  xfails or deselections, Black/isort all nine Python files, mypy all three
  production files, compile checks and all seven KCL entry points. Strict change
  validation and `git diff --check` pass. Existing pytest-asyncio and anyio
  warnings remain visible. Concurrent worker KCL runs initially produced stdout
  contamination; serial focused and complete runs passed without output filters,
  retries inside tests, or configuration changes.
- Revised spec-merge preflight remains read-only and passes strict baseline,
  strict merged and archive-equivalent content validation without warnings:
  guidance 19 merged requirements (3 added, 4 modified, 1 removed), generators
  15 merged requirements (5 added), offline baseline 4 new requirements. Historical
  scenario identities were retained rather than omitted by replacement deltas.
- All approved implementation acceptance is now demonstrated offline. The
  immutable baseline revision for dependent work remains a closeout item until
  a separately requested commit/push records these working-tree changes. No
  live engine/provider acceptance, infrastructure mutation, merge, spec sync or
  archive was performed.
