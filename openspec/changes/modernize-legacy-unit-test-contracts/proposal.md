## Why

The secret-hardening change exposed stale legacy tests that still target removed standalone deployment functions and superseded KCL output names. Repairing those contracts now would be repeated by the already queued provider baseline, provider migration, and live-canary work, so the full-suite cleanup is deferred until those changes stabilize the final APIs and fixtures.

## What Changes

- Sequence this change after `normalize-current-unifi-provider-baseline`, `migrate-to-ubiquiti-community-unifi`, and `add-cloudflare-live-ci-canary` are complete.
- Reconcile legacy deployment-guidance tests and requirements with the combined `deploy()` interface and its selective component flags.
- Reconcile generator-output tests and requirements with the final KCL entry-point and output contract established by the queued changes.
- Preserve and run the hardening sentinel, failure-injection, type/compile, and KCL checks as part of one authoritative offline verification command.
- Format the remaining legacy Python files and require the complete offline unit suite and static checks to pass without obsolete test exclusions.

## Capabilities

### New Capabilities

- `offline-verification-baseline`: Defines the authoritative, credential-free offline verification suite and prevents stale tests from silently remaining outside the supported contract.

### Modified Capabilities

- `deployment-guidance`: Updates guidance requirements and tests to cover the supported combined deployment interface instead of removed standalone functions.
- `generator-output-validation`: Updates validation tests to consume the final supported KCL output structure rather than superseded output keys.

## Impact

- Affects legacy tests under `tests/unit/`, their fixtures/mocks, relevant KCL test entry points, and stale main OpenSpec requirements.
- May remove tests that only assert deleted APIs, but does not restore those APIs or change managed infrastructure.
- Depends on all currently queued OpenSpec changes and runs only after their implementation contracts have stabilized.
