## Why

The secret-hardening change exposed stale tests targeting removed deployment functions and superseded KCL output names. Repairing the currently supported contracts first establishes the credential-free regression baseline needed to safely modernize Dagger execution and subsequently migrate providers or add live CI.

## What Changes

- Use the existing hardening and normalized provider baseline as inputs; complete this baseline before the execution refactor in `modernize-dagger-execution-contracts` and before provider/canary implementation.
- Allow the parent's exact Dagger 1.0 beta qualification to proceed in parallel; do not wait for its runtime selection to repair current contracts.
- Reconcile legacy deployment-guidance tests and requirements with the combined `deploy()` interface and its selective component flags.
- Reconcile generator-output tests and requirements with the current standalone `result` and dedicated consumer `unifi_output`/`cf_output` contracts, exercising actual transformations rather than self-testing assertions.
- Apply the explicitly approved contract fixes: label unavailable host paths as placeholders without new public parameters, validate generated JSON structures before export, and enforce DNS-loop rejection in KCL generation for explicit and entity-derived origins.
- Preserve and run the hardening sentinel, failure-injection, type/compile, and KCL checks as part of one authoritative offline verification command.
- Format the remaining legacy Python files and require the complete offline unit suite and static checks to pass without obsolete test exclusions.

## Capabilities

### New Capabilities

- `offline-verification-baseline`: Defines the authoritative, credential-free offline verification suite and prevents stale tests from silently remaining outside the supported contract.

### Modified Capabilities

- `deployment-guidance`: Updates guidance requirements and tests to cover the supported combined deployment interface instead of removed standalone functions.
- `generator-output-validation`: Updates validation tests to consume the currently supported KCL output structures rather than superseded output keys.

## Impact

- Affects legacy tests under `tests/unit/`, their fixtures/mocks, relevant KCL test entry points, and stale main OpenSpec requirements.
- Includes focused production guidance/validation changes approved after the initial test-only implementation exposed gaps; no new dependency, provider schema, or Dagger runtime selection is introduced.
- May remove tests that only assert deleted APIs, but does not restore those APIs, add temporary old-API wrappers, or change managed infrastructure.
- Establishes a baseline later changes must extend and keep green; it does not depend on `migrate-to-ubiquiti-community-unifi` or `add-cloudflare-live-ci-canary`, or require archiving the completed provider baseline.
