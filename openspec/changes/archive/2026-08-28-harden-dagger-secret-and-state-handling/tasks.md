## 1. Exposure Response and Regression Baseline

- [x] 1.1 Record operator prerequisites to rotate the exposed S3 backend credentials and securely remove the affected local Terraform plan artifacts before further live tests
- [x] 1.2 Add sentinel-secret test fixtures covering successful execution, provider errors, validation errors, timeout errors, cleanup errors, reports, and exported artifacts
- [x] 1.3 Add a regression scan that fails when any sentinel value appears in captured output, exceptions, default exports, or ordinary Dagger files

## 2. Secret Transport Hardening

- [x] 2.1 Replace backend configuration plaintext file creation with a Dagger secret-file mount across plan, deploy, destroy, and tunnel-secret retrieval paths
- [x] 2.2 Remove Cloudflare `Secret.plaintext()` command interpolation and supply validation authentication only through secret environment variables or secret files
- [x] 2.3 Route UniFi and Cloudflare provider authentication through provider-supported secret environment variables instead of serialized Terraform input values
- [x] 2.4 Sanitize reports and propagated Terraform/API errors so they retain actionable non-secret context without request authorization material
- [x] 2.5 Remove obsolete sensitive Terraform credential variables and update Cloudflare/UniFi deployment contract tests for the provider environment names

## 3. Plan Artifact Safety

- [x] 3.1 Change the default plan directory to contain only redacted human-readable plans and the aggregated summary
- [x] 3.2 Add an explicit sensitive-artifact option for binary and raw JSON plans with a warning manifest
- [x] 3.3 Enforce owner-only permissions for sensitive plan artifacts and verify host export preserves them; disable general raw export if it cannot
- [x] 3.4 Update CLI help, README guidance, and tests for the breaking safe-default plan behavior

## 4. Strict Integration Lifecycle

- [x] 4.1 Refactor integration execution to track created resources and captured state in a non-secret cleanup ledger
- [x] 4.2 Make validation query the actual Cloudflare resources and UniFi DNS record rather than treating apply success as validation
- [x] 4.3 Parse and enforce `test_timeout`, including a bounded cleanup reserve after cancellation or failure
- [x] 4.4 Guarantee reverse-order cleanup for every recorded resource and verify externally visible test resources are absent
- [x] 4.5 Raise a Dagger-visible failure after cleanup for any creation, validation, timeout, cleanup, or residual-resource failure

## 5. Verification

- [x] 5.1 **Deferred:** Run Python formatting and the complete legacy unit/KCL generator suite under `modernize-legacy-unit-test-contracts`, after the queued provider baseline, provider migration, and live Cloudflare canary changes; the hardening-specific formatting, type/compile, KCL, and focused regression checks passed here
- [x] 5.2 Run offline failure-injection tests for partial apply, missing state, API failure, timeout, retry, and residual-resource reporting
- [x] 5.3 After credential rotation, run one controlled read-only production Dagger plan with the S3 backend and verify zero infrastructure drift
- [x] 5.4 Inspect the Dagger trace and safe plan export to confirm no backend credential, UniFi API key, Cloudflare token, or sentinel value is present
- [x] 5.5 Run `openspec validate harden-dagger-secret-and-state-handling --strict` and `git diff --check`
