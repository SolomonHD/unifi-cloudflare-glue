## Context

The repository currently runs duplicated offline Python/KCL jobs in `test.yml` and `status-check.yml`. Its existing `test_integration` function creates a Cloudflare Tunnel, Tunnel configuration, and proxied CNAME, which requires account-level Tunnel Edit permission and is therefore too privileged for an unattended hosted runner. `solomonhd.ai` is a separate public zone suitable for bounded DNS mutation without involving production `sghd.io` records.

This change follows the secret-hardening and provider changes so it can reuse strict failure/cleanup behavior. GitHub-hosted runners cannot reach the private UniFi controllers, so UniFi live testing remains an authorized local Dagger operation.

## Goals / Non-Goals

**Goals:**

- Continuously prove Cloudflare provider authentication and DNS create/read/update/delete behavior against `solomonhd.ai`.
- Confine every mutation to a recognizable, unique `ci.solomonhd.ai` name.
- Keep the CI credential zone-scoped and unavailable to untrusted pull-request code.
- Fail on validation, cleanup, or residual-resource errors and provide a janitor for abandoned records.
- Preserve the local full-Tunnel integration path for higher-privilege manual testing.

**Non-Goals:**

- Create or delete Cloudflare zones or registered domains.
- Create Cloudflare Tunnels or use Account Cloudflare Tunnel Edit in GitHub Actions.
- Test private UniFi controllers from GitHub-hosted runners.
- Route a test hostname to a live internal or public application.

## Decisions

### 1. Test DNS resources directly, not the Tunnel module

A dedicated canary fixture uses `cloudflare_dns_record` to create a TXT marker and an unproxied CNAME below a unique run prefix. This exercises the provider and public DNS behavior with only Zone Read and DNS Edit. Full module testing remains local because the module also manages account-scoped Tunnels.

Alternative considered: create an inactive Tunnel and proxied CNAME in every CI run. Rejected because the required token could modify production account-level Tunnel resources if compromised.

### 2. Run only in trusted workflow contexts

The live workflow triggers on pushes to `main`, a schedule, and `workflow_dispatch`. It does not run with secrets for `pull_request`, `pull_request_target`, or fork-controlled code. Credentials live in a `cloudflare-live-ci` GitHub Environment restricted to the protected `main` branch and approved workflow.

Alternative considered: run on every pull request from the base workflow. Rejected because repository write access or workflow changes could exfiltrate the zone token.

### 3. Use deterministic unique naming and metadata

Names follow `gha-<unix>-<run-id>-<attempt>.<record>.ci.solomonhd.ai`, shortened to DNS label limits. Values/comments contain a non-secret run marker. The timestamp and Cloudflare `created_on` value allow cleanup without persistent Terraform state.

### 4. Separate primary execution and unconditional cleanup steps

Terraform apply, API validation, public-DNS validation, update, and zero-drift plan run in the primary step. A separate `if: always()` step destroys from the runner-local state and then queries the Cloudflare API by exact name. State is never uploaded as an artifact. Cleanup or residual failure fails the job even when the primary test already failed.

### 5. Add an API-driven age-bounded janitor

A scheduled/manual janitor lists only records matching the exact `gha-*.*.ci.solomonhd.ai` convention and deletes those older than a threshold exceeding the maximum workflow duration plus DNS propagation reserve. It never enumerates a deletion target outside the test suffix and prefix. Every deletion is reported by record ID/name, never token.

### 6. Validate public DNS with bounded retries

After create and update, the job polls public resolvers until the expected value appears or a bounded deadline expires. After destroy, Cloudflare API absence is authoritative; public negative lookup is informational because recursive caches may retain the record until TTL expiry.

## Risks / Trade-offs

- [Zone-scoped DNS token can still alter any `solomonhd.ai` record] → Restrict workflow contexts/environment, keep permissions minimal, mask secrets, and rotate the dedicated token independently.
- [Runner termination bypasses cleanup] → Use unique timestamped names and the scheduled age-bounded janitor.
- [Public DNS propagation is variable] → Use low supported TTL, multiple bounded retries, and separate API verification from recursive-DNS verification.
- [Janitor deletes an active record] → Set the stale threshold beyond job timeout plus buffer and serialize live canary runs.
- [Two existing workflow files duplicate offline checks] → Add one live workflow and one required status integration point; do not duplicate the secret-bearing job.

## Migration Plan

1. Complete and publish the first three ordered changes.
2. Add the DNS fixture and run it locally against `solomonhd.ai` with a temporary zone-scoped token.
3. Add offline tests for naming, suffix/prefix allowlists, age calculation, cleanup, and failure propagation.
4. Create the protected `cloudflare-live-ci` GitHub Environment and add the dedicated zone token plus non-secret zone metadata.
5. Add the trusted-trigger live workflow with least-privilege GitHub permissions, timeout, serialization, and unconditional cleanup.
6. Add the janitor in report-only mode, verify selection, then authorize deletion mode.
7. Run `workflow_dispatch`, verify CRUD and cleanup, then enable schedule and required-status reporting as desired.

Rollback disables the schedule and removes the environment secret after the janitor confirms no stale canary records remain. It does not affect `solomonhd.ai` records outside the canary namespace.

## Open Questions

- Choose the final schedule frequency after measuring Cloudflare propagation and workflow duration; nightly is the initial recommendation.
- Decide whether the live canary is a required `main` status signal or an informational scheduled signal after observing reliability.
