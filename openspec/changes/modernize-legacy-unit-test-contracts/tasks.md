## 1. Queue Gate and Failure Inventory

- [ ] 1.1 Confirm `normalize-current-unifi-provider-baseline`, `migrate-to-ubiquiti-community-unifi`, and `add-cloudflare-live-ci-canary` are complete and archived before implementation begins
- [ ] 1.2 Run the complete credential-free unit, formatting, type/compile, and KCL checks and record every failure, skip, xfail, and marker exclusion
- [ ] 1.3 Map each obsolete test to a supported replacement behavior or document why its historical contract is removed

## 2. Deployment Guidance Contract

- [ ] 2.1 Reconcile main deployment-guidance requirements with the final combined `deploy()` interface and selection flags
- [ ] 2.2 Rewrite Cloudflare-only guidance tests to call the supported combined deployment path
- [ ] 2.3 Update guidance mocks and assertions for current Terraform execution, backend parameters, success output, and failure behavior
- [ ] 2.4 Remove obsolete standalone-function tests without adding production compatibility wrappers solely for test support

## 3. KCL Generator Contract

- [ ] 3.1 Reconcile main generator requirements with the final standalone `result` and Dagger consumer-output contracts
- [ ] 3.2 Update standalone UniFi and Cloudflare generator tests to validate their `result` objects and Terraform-compatible structures
- [ ] 3.3 Add purpose-built consumer `main.k` fixtures for valid, missing-key, and malformed-output Dagger generation cases
- [ ] 3.4 Verify MAC normalization, service distribution, DNS-loop prevention, and both provider outputs across the repaired fixtures

## 4. Authoritative Offline Baseline

- [ ] 4.1 Format all in-scope Python files and resolve remaining repository-wide formatting failures
- [ ] 4.2 Define one documented offline verification command sequence covering formatting, type/compile, full unit, and KCL checks
- [ ] 4.3 Confirm hardening sentinel and failure-injection tests remain collected and passing without infrastructure credentials
- [ ] 4.4 Review all remaining skips, xfails, and marker exclusions and retain only documented live-infrastructure gates
- [ ] 4.5 Run the complete offline baseline, `openspec validate modernize-legacy-unit-test-contracts --strict`, and `git diff --check`
