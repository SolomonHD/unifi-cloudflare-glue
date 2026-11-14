## 1. Current Contract and Failure Inventory

- [x] 1.1 Record existing hardening/normalized-provider evidence and supported current APIs; verify this change precedes the parent's execution refactor and provider/canary implementation while exact beta qualification may run in parallel, without archive prerequisites
- [x] 1.2 Run the complete credential-free unit, formatting, type/compile, and KCL checks and record every failure, skip, xfail, and marker exclusion
- [x] 1.3 Map each obsolete test to a supported replacement behavior or document why its historical contract is removed

## 2. Deployment Guidance Contract

- [x] 2.1 Reconcile deployment-guidance requirements with current combined `deploy()` and selection flags; verify no separate-phase assumption contradicts the single-operation contract
- [x] 2.2 Rewrite Cloudflare-only guidance tests against combined deployment and verify full, UniFi-only, and invalid-selection cases with no unnecessary credentials
- [x] 2.3 Update guidance mocks/assertions for current Terraform execution, local/remote backend and state parameters, success/failure output, and secret-safe instructions; verify focused guidance tests pass
- [x] 2.4 Remove obsolete standalone-function tests without temporary compatibility wrappers and verify each removal has the replacement/removal evidence from 1.3

## 3. KCL Generator Contract

- [x] 3.1 Reconcile generator requirements with current standalone `result` and Dagger consumer-output contracts and verify the documented fixture boundary
- [x] 3.2 Update standalone UniFi and Cloudflare generator tests to validate their `result` objects and Terraform-compatible structures
- [x] 3.3 Add purpose-built consumer `main.k` fixtures for valid, missing-key, and malformed-output Dagger generation cases
- [x] 3.4 Verify actual generator transformations for varied MAC inputs, service distribution, DNS-loop prevention, empty/multiple NICs, and both provider outputs; replace tautological helper/placeholder assertions with behavioral coverage

## 4. Authoritative Offline Baseline

- [x] 4.1 Format all in-scope Python files and resolve remaining repository-wide formatting failures
- [x] 4.2 Define one documented offline verification command sequence covering formatting, type/compile, full unit, and KCL checks; verify bootstrap prerequisites are distinct from credential-free/no-live verification
- [x] 4.3 Confirm hardening sentinel and failure-injection tests remain collected and passing without infrastructure credentials
- [x] 4.4 Review all remaining skips, xfails, and marker exclusions and retain only documented live-infrastructure gates
- [x] 4.5 Run the complete offline baseline, `openspec validate modernize-legacy-unit-test-contracts --strict`, and `git diff --check`
- [x] 4.6 During separately scoped implementation/spec reconciliation, repair affected main-spec structure for `deployment-guidance` and `generator-output-validation` while preserving historical requirements and pending obligations; verify main-spec parsing/strict validation and archive preflight before specification sync or archive

## Closeout

- Record the accepted baseline revision and results for `modernize-dagger-execution-contracts`; dependent changes extend this suite rather than defer it.
- Commit/push, review, merge, specification sync, and archive remain separate lifecycle work. Do not merge before applicable feature acceptance or archive the completed normalized-provider baseline in this scope.
- The implementation repaired the affected main-spec structure and preflighted spec merging without syncing or archiving. Project `openspec/config.yaml` is unchanged; its pre-existing `rules.general` warning remains outside scope.
