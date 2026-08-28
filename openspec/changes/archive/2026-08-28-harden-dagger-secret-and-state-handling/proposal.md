## Why

Real Dagger execution revealed that backend credentials can be embedded in the Dagger trace and that generated plan artifacts can retain the UniFi API key. The existing integration function also converts the Cloudflare token to plaintext shell text and can report failures without failing the command, so it must be hardened before additional live tests or CI automation are safe.

## What Changes

- Keep backend credentials, provider tokens, and controller credentials on Dagger secret mounts or secret environment variables from ingestion through cleanup.
- **BREAKING**: Stop exporting raw binary and JSON Terraform plans by default; require an explicit sensitive-artifact opt-in and restrictive permissions.
- Prevent secret-bearing backend configuration and Terraform plan data from appearing in traces, command arguments, reports, caches, or broadly readable exported artifacts.
- Make integration validation, cleanup, and timeout behavior deterministic and machine-actionable.
- Add cleanup accounting and explicit residual-resource reporting without printing credential material.
- Document credential rotation and artifact cleanup required after the empirically observed exposure.

## Capabilities

### New Capabilities
- `secret-safe-execution`: Defines end-to-end handling requirements for backend files, provider credentials, logs, caches, reports, and exported artifacts.

### Modified Capabilities
- `test-integration`: Requires real validation failures and incomplete cleanup to produce failing outcomes, enforces timeouts, and keeps secrets out of commands and reports.
- `plan-generation`: Requires sensitive plan exports to be avoided or protected and prevents credentials from being serialized into plan configuration.
- `state-management`: Requires backend configuration to be supplied without embedding its contents in the Dagger execution trace.
- `cloudflare-deployment`: Changes Cloudflare provider authentication from serialized Terraform variables to the provider's secret environment variable.
- `unifi-deployment`: Changes UniFi provider authentication from serialized Terraform variables to provider-supported secret environment variables.

## Impact

- Affects `src/main/main.py`, Terraform provider-variable wiring, plan export behavior, integration cleanup, unit tests, and operator documentation.
- Changes failure semantics for integration callers: a failed validation or cleanup is no longer returned as a successful string result.
- Requires rotation of credentials exposed during the 2026-08-27 baseline investigation and secure disposal of affected local plan artifacts.
- Establishes the safety prerequisite for live `solomonhd.ai` tests and GitHub Actions.
