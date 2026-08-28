## Context

The production pre-flight on 2026-08-27 succeeded, but it exposed two security defects in the execution path: backend-file contents were rendered into a Dagger trace, and the exported Terraform JSON plan contained the UniFi API key. The integration harness separately calls `Secret.plaintext()` for the Cloudflare token, interpolates that value into shell commands, catches failures into a successful string return, and does not enforce its declared timeout.

This change is the prerequisite for all subsequent live provider and `solomonhd.ai` tests. It changes how sensitive inputs and outputs cross the Dagger/Terraform boundary without changing managed DNS or Tunnel resources.

## Goals / Non-Goals

**Goals:**

- Preserve Dagger secret typing from function input through Terraform and API validation.
- Keep backend credentials out of traces and cacheable ordinary files.
- Make the default plan product safe for routine export and review.
- Guarantee cleanup attempts and make validation, timeout, and residual-resource failures observable to automation.
- Add regression tests that use sentinel secrets and fail if they appear in captured output or exported artifacts.

**Non-Goals:**

- Rotate Cloudflare or UniFi credentials as part of repository implementation; exposed credentials are rotated through the operator's credential workflow.
- Change Terraform providers, resource schemas, KCL DNS behavior, or production resources.
- Add GitHub Actions secrets or execute public live tests.

## Decisions

### 1. Convert secret-bearing files into Dagger secret mounts

The existing backend-file CLI remains usable, but its content is converted immediately into a Dagger secret and mounted at the Terraform backend path. Code must not recreate the content with `with_new_file`, return it, or place it in a normal environment variable.

Alternative considered: continue mounting the backend input as an ordinary Dagger file. Rejected because ordinary files are cacheable objects and lack explicit redaction semantics.

### 2. Authenticate providers through secret environment channels

Provider credentials and validation tokens remain `dagger.Secret` values and are exposed only with `with_secret_variable` or secret-file mounts. Validation commands refer to secret environment-variable names; Python never calls `plaintext()` to build a command string.

Alternative considered: rely on shell quoting after plaintext extraction. Rejected because quoting prevents injection but does not prevent trace, exception, or report disclosure.

### 3. Make safe plan output the default

The default plan directory contains a secret-reviewed summary and human-readable plan with Terraform's sensitive-value redaction. Raw binary and JSON plans are available only through an explicit sensitive-artifact option, retain a warning manifest, and export with owner-only permissions. Provider credentials are supplied through provider environment variables so they are not serialized as Terraform input variables.

Alternative considered: continue exporting all formats and only apply `0600`. Rejected because permissions do not protect uploads, CI artifacts, or accidental source-control inclusion.

### 4. Model integration execution as a failing test with `finally` cleanup

Creation, validation, and cleanup results are tracked independently. Cleanup always runs for every resource whose state was captured. After cleanup, any primary failure, timeout, failed cleanup, or verified residual resource raises a Dagger-visible error; a report may accompany the error but cannot turn it into success.

Alternative considered: preserve the current report-only contract. Rejected because CI cannot reliably distinguish a successful test from a report containing failure text.

### 5. Enforce a single operation deadline and a cleanup reserve

The declared timeout is parsed and applied to the test lifecycle. Cleanup receives a bounded reserve even when the main deadline expires. Each created resource is recorded in a cleanup ledger containing only non-secret identifiers.

## Risks / Trade-offs

- [Raw plans become less convenient] → Provide an explicit sensitive-artifact option with warnings and restrictive permissions.
- [A timeout can occur during provider activity] → Capture state immediately after each successful apply and reserve time for cleanup.
- [Terraform or provider errors can echo request context] → Sanitize returned errors and validate with sentinel-secret regression tests.
- [Cleanup can still fail because an external API is unavailable] → Report exact non-secret resource identifiers, fail the run, and retain deterministic manual-cleanup guidance.
- [Credential rotation is external to this repository] → Record it as an operator prerequisite before further live tests.

## Migration Plan

1. Rotate the backend credentials exposed by the baseline trace and securely remove affected local plan artifacts.
2. Add sentinel-secret tests around backend setup, plan export, validation, exception, and report paths.
3. Replace plaintext extraction and ordinary backend-file creation with secret mounts/variables.
4. Introduce safe default plan output and the explicit sensitive-artifact mode.
5. Enforce timeout, strict validation, cleanup ledger, residual checks, and failing outcomes.
6. Run offline tests, then a single controlled read-only production plan to confirm zero drift and no trace/artifact disclosure.

Rollback restores the prior code only after disabling live execution; it must not restore or reuse rotated credentials.

## Open Questions

- Final naming of the explicit raw-plan export option should align with Dagger CLI conventions during implementation.
- Whether Dagger can preserve `0600` on every supported host export path must be verified; if not, raw export must require a caller-supplied secure destination rather than returning a general directory.
