## 1. Prerequisites and Credential Boundary

- [ ] 1.1 Confirm the first three ordered changes are complete and the hardened integration/cleanup contract is available
- [ ] 1.2 Document creation and independent rotation of a token restricted to Zone Read and DNS Edit for only `solomonhd.ai`, with no Tunnel permissions
- [ ] 1.3 Define the protected `cloudflare-live-ci` GitHub Environment, trusted-branch policy, secret names, and non-secret zone metadata
- [ ] 1.4 Add offline assertions that pull-request and `pull_request_target` contexts cannot request the live environment or token

## 2. DNS Canary Fixture

- [ ] 2.1 Add a Terraform/Dagger fixture containing only a TXT marker and unproxied CNAME under caller-supplied run-prefixed names
- [ ] 2.2 Implement DNS-label-safe `gha-<timestamp>-<run-id>-<attempt>` naming and exact `ci.solomonhd.ai` suffix/prefix validation
- [ ] 2.3 Supply Cloudflare authentication only through the hardened secret environment path and keep runner-local Terraform state out of artifacts and logs
- [ ] 2.4 Implement create, Cloudflare API verification, bounded public-DNS verification, one value update, and a zero-drift plan
- [ ] 2.5 Implement state-based destroy plus authoritative exact-name API absence verification, with public negative DNS as informational only
- [ ] 2.6 Add unit/failure-injection tests for naming limits, allowlist rejection, propagation timeout, partial apply, missing state, failed destroy, residual detection, and secret disclosure

## 3. Trusted GitHub Actions Workflow

- [ ] 3.1 Add a dedicated live workflow triggered only by protected `main` pushes, schedule, and `workflow_dispatch`
- [ ] 3.2 Set read-only contents permission, finite job timeout, serialized concurrency with `cancel-in-progress: false`, and the protected environment
- [ ] 3.3 Separate primary CRUD/validation from an `if: always()` cleanup and residual-verification step
- [ ] 3.4 Ensure a cleanup or residual failure fails the job even when the primary canary step has already failed
- [ ] 3.5 Integrate one non-duplicated live result into repository status reporting without copying the secret-bearing job into both existing workflow files

## 4. Stale Record Janitor

- [ ] 4.1 Add a scheduled/manual API inventory that selects only `gha-*.*.ci.solomonhd.ai` records older than the job-timeout-plus-buffer threshold
- [ ] 4.2 Add report-only mode and tests proving newer records and every name outside the exact canary namespace are ignored
- [ ] 4.3 After operator review of report-only output, enable guarded deletion and exact-name post-delete verification
- [ ] 4.4 Make janitor selection/deletion failures visible without logging the token or unrelated zone records

## 5. Live Verification and Documentation

- [ ] 5.1 Run the fixture locally with an authorized temporary zone-scoped token and verify no Tunnel API call occurs
- [ ] 5.2 Configure the protected environment and run one manual GitHub Actions dispatch through successful create/update/plan/destroy verification
- [ ] 5.3 Force one controlled validation failure and prove unconditional cleanup and failing status behavior
- [ ] 5.4 Run janitor report-only mode, review the selection, then test cleanup of a deliberately aged canary record
- [ ] 5.5 Document the hosted DNS-only boundary, manual local Tunnel test, secret rotation, residual cleanup, and workflow troubleshooting
- [ ] 5.6 Enable the initial nightly schedule and decide separately whether the live canary is required or informational for `main`
- [ ] 5.7 Run offline test suites, workflow linting, `openspec validate add-cloudflare-live-ci-canary --strict`, and `git diff --check`
