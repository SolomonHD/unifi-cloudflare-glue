## 1. Prerequisites and Credential Boundary

- [x] 1.1 Record accepted repaired baseline and execution-foundation evidence from `docs/dagger-runtime-qualification.md` / `docs/execution-contracts.md`: beta27 CLI checksum/engine digest, Python SDK full SHA, native KCL 0.12.4 checksum and Terraform 1.13.5 digest, not a moving beta label. Require the foundation's feature-consumer/production-read gates; fallback remains unaccepted unless separately qualified. Verify no dependency on `migrate-to-ubiquiti-community-unifi` completion.
- [x] 1.2 Document token creation/independent rotation for Zone Read and DNS Edit on only `solomonhd.ai`, and verify credential policy excludes Tunnel and production-zone permissions
- [x] 1.3 Define the `cloudflare-live-ci` environment, trusted-ref/access policy, runtime secret bindings, and non-secret zone metadata; verify available GitHub enforcement rather than assume environment naming provides protection
- [x] 1.4 Add passing offline tests rejecting PR/fork/`pull_request_target` secret execution and untrusted manual-dispatch refs before requesting credentials
- [x] 1.5 Document the dedicated Wasabi sandbox prefix, per-run state/ledger/checkpoint layout, scoped CI identity, encryption, retention, and production isolation; verify the design grants no provisioning or credential access
- [x] 1.6 Under separately authorized backend qualification, record exact Wasabi conditional-write/version/lock semantics for the selected runtime/backend tuple and prove competing writers, renewal/loss, stale ownership, and failed preconditions fail closed before DNS mutation

## 2. DNS Canary Fixture

- [x] 2.1 Add the TXT/unproxied-CNAME-only Terraform fixture and one normal Dagger lifecycle entry point; verify resource allowlist tests exclude Tunnels, zones, routes, and UniFi
- [x] 2.2 Implement DNS-label-safe `gha-<timestamp>-<run-id>-<attempt>` naming and exact suffix/prefix checks; verify rejection tests run before apply and cleanup
- [x] 2.3 Supply Cloudflare and scoped Wasabi credentials only through runtime Dagger secret channels; verify sentinel tests exclude raw state/plan/credentials/provider logs from output and generic Actions artifacts
- [x] 2.4 Implement Dagger-owned create/API/public-DNS validation/update/zero-drift plan and verify unit tests for each phase plus bounded propagation failures
- [x] 2.5 Implement Dagger-owned handled-failure cleanup, state-based destroy, and exact-name API absence verification; verify primary and cleanup outcomes are retained and public negative DNS is informational only
- [x] 2.6 Add passing failure-injection tests for naming limits, allowlists, propagation timeout, partial apply, missing state, failed destroy, residuals, backend loss, and disclosure
- [x] 2.7 Persist run/revision/zone identity, exact intended records, and phase intent before effects in protected per-run Wasabi evidence; verify persistence failure stops mutation and uncertain-create recovery avoids duplicate creation
- [x] 2.8 Implement shared all-writer ownership/generation fencing and verify lost ownership, external writers, delayed/stalled prior work, and uncertain state block further effects; document why Actions concurrency or lease age alone is insufficient
- [x] 2.9 Document lifecycle, protected evidence, outcome meanings, and DNS/Tunnel boundaries; verify examples invoke the selected Dagger entry point without workflow Terraform logic

## 3. Trusted GitHub Actions Workflow

- [x] 3.1 Add a thin live workflow for trusted `main` pushes, schedule, and trusted-ref manual dispatch; verify workflow tests reject all untrusted secret contexts
- [x] 3.2 Set least permissions (read-only contents unless justified), finite timeout, `cancel-in-progress: false`, verified environment controls, and exact parent-selected CLI setup; verify lint and policy tests
- [x] 3.3 Invoke the one normal Dagger entry point with runtime secret handoff; verify workflow tests reject Terraform/API lifecycle logic in every step, including `if: always()`, and reject Dagger Cloud or other-template migration
- [x] 3.4 Verify sanitized failing job status for primary, cleanup, residual, and unknown outcomes, without claiming hard cancellation ran a finalizer
- [x] 3.5 Integrate one non-duplicated live result/status and verify no secret-bearing job is copied into either existing offline template

## 4. Stale Record Janitor

- [ ] 4.1 Add a Dagger scheduled/manual janitor inventory for exact `gha-*.*.ci.solomonhd.ai` candidates older than timeout plus buffer; verify age alone cannot select an active/unknown run for deletion
- [ ] 4.2 Add default report-only mode and passing tests excluding newer, outside-namespace, active, unowned, and uncertain candidates using protected ledger/ownership evidence
- [ ] 4.3 After explicit operator review/authorization, test fenced deletion of a selected aged owned record and verify exact-name/ID absence, with no overlap with live/recovery writers
- [ ] 4.4 Verify selection/deletion failures report sanitized identifiers/results without tokens or unrelated zone inventory and document remaining recovery actions
- [x] 4.5 Add a separately authorized Dagger reconciliation entry point accepting non-secret run identity; verify it reconciles protected ledger/state and exact API objects only after prior writer termination/exclusivity, with no blind retry or automatic takeover
- [x] 4.6 Add passing killed-run, missing/partial state, uncertain-create, stale-generation, and recovery-concurrency tests; verify unknown outcomes retain protected evidence and cannot be reported as verified cleanup

## 5. Live Verification and Documentation

- [ ] 5.1 Under separate scoped authorization, run the local Dagger fixture with zone-scoped Cloudflare and sandbox-prefix Wasabi credentials; verify full lifecycle, durable evidence, and no Tunnel API calls
- [ ] 5.2 Under separate setup/live authorization, configure verified GitHub environment controls and run trusted manual Actions create/update/plan/destroy acceptance; retain sanitized exact feature/runtime/run evidence before merge
- [ ] 5.3 Under explicit sandbox authorization, force a controlled validation failure and verify Dagger cleanup plus failing status; separately test termination and authorized reconciliation without a false finalizer guarantee
- [ ] 5.4 Run janitor report-only mode, review the selection, then test cleanup of a deliberately aged canary record
- [ ] 5.5 Verify documentation covers hosted DNS-only scope, manual local Tunnel testing, credential rotation, protected recovery retention, explicit reconciliation authorization, rollback, residual cleanup, and troubleshooting
- [ ] 5.6 Record pilot reliability/propagation measurements and a reviewed initial nightly rollout/status recommendation; verify schedule activation remains a separate explicitly authorized action
- [x] 5.7 Run offline test suites, workflow linting, `openspec validate add-cloudflare-live-ci-canary --strict`, and `git diff --check`

## Closeout

- Commit/push, review, merge, publication, specification sync, and archive remain separate lifecycle actions. Do not merge before qualified feature acceptance; do not archive the completed provider baseline here.
- After pilot acceptance, separately authorize and enable the initial nightly schedule, choosing required versus informational `main` status from observed reliability (remaining activation work from former 5.6).
- Provision/access the dedicated Wasabi sandbox prefix and configure scoped runtime credentials only under separate authorization. Never discard unresolved state/receipts or retire recovery access until run outcomes are reconciled.
