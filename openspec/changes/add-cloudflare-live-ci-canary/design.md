## Context

The repository currently runs duplicated offline Python/KCL jobs in `test.yml` and `status-check.yml`. Its existing `test_integration` function creates a Cloudflare Tunnel, Tunnel configuration, and proxied CNAME, which requires account-level Tunnel Edit permission and is therefore too privileged for an unattended hosted runner. `solomonhd.ai` is a separate public zone suitable for bounded DNS mutation without involving production `sghd.io` records.

This change follows `modernize-legacy-unit-test-contracts` and accepted `modernize-dagger-execution-contracts`, reusing existing hardening evidence. It is independent of `migrate-to-ubiquiti-community-unifi` and is not a prerequisite for consumer `adopt-modernized-dns-dagger-workspace`. GitHub-hosted runners cannot reach private UniFi controllers; local UniFi/Tunnel acceptance stays separately authorized.

## Goals / Non-Goals

**Goals:**

- Continuously prove Cloudflare provider authentication and DNS create/read/update/delete behavior against `solomonhd.ai`.
- Confine every mutation to a recognizable, unique `ci.solomonhd.ai` name.
- Keep the CI credential zone-scoped and unavailable to untrusted pull-request code.
- Fail on validation, cleanup, or residual-resource errors and provide a janitor for abandoned records.
- Preserve the local full-Tunnel integration path for higher-privilege manual testing.
- Keep lifecycle/recovery logic in Dagger with a thin Actions adapter and protected durable state/receipts that survive runner death.

**Non-Goals:**

- Create or delete Cloudflare zones or registered domains.
- Create Cloudflare Tunnels or use Account Cloudflare Tunnel Edit in GitHub Actions.
- Test private UniFi controllers from GitHub-hosted runners.
- Route a test hostname to a live internal or public application.
- Introduce Dagger Cloud, migrate other workflow templates, provision credentials/backends through this planning change, or claim hard-kill cleanup guarantees.

## Decisions

### 1. Test DNS resources directly, not the Tunnel module

A dedicated canary fixture uses `cloudflare_dns_record` to create a TXT marker and an unproxied CNAME below a unique run prefix. This exercises the provider and public DNS behavior with only Zone Read and DNS Edit. Full module testing remains local because the module also manages account-scoped Tunnels.

Alternative considered: create an inactive Tunnel and proxied CNAME in every CI run. Rejected because the required token could modify production account-level Tunnel resources if compromised.

### 2. Run only in trusted workflow contexts

The live workflow triggers on trusted `main` pushes, schedule, and `workflow_dispatch` restricted to the approved trusted ref. Reject untrusted manual refs before requesting secrets. It never executes secret-bearing PR, fork, or `pull_request_target` code. Use a `cloudflare-live-ci` GitHub Environment with verified available branch/access controls; do not assume environment naming alone enforces workflow identity. Verify the repository's actual controls before enabling live execution. Trusted repository writers remain part of the security boundary.

Alternative considered: run on every pull request from the base workflow. Rejected because repository write access or workflow changes could exfiltrate the zone token.

### 3. Use deterministic unique naming and metadata

Names follow `gha-<unix>-<run-id>-<attempt>.<record>.ci.solomonhd.ai`, bounded to DNS label limits. Values/comments and the ledger contain a non-secret run marker. Record exact zone ID/name, run/revision identity, intended names, allowed record types, and phase intent durably before any possible DNS effect. Register resulting resource IDs and phase results after authoritative observation; uncertain create must be reconciled by exact intended names and ownership before retrying. Timestamp and `created_on` are selection evidence, not a replacement for durable state or proof a writer stopped.

### 4. One Dagger entry point owns normal execution

One normal Dagger entry point owns preparation, create, API/DNS validation, update, zero-drift plan, state-based destroy, and authoritative exact-name residual checks. Its handled-failure path attempts bounded cleanup and retains both primary and cleanup outcomes; cleanup/residual failure cannot become success merely because the primary phase failed first. Hard cancellation, process death, and backend loss may bypass finalization, so report unknown rather than guaranteed cleanup.

GitHub Actions performs exact CLI setup using the parent's selected CLI/engine/Python SDK tuple, trusted triggers/ref checks, least permissions, runtime secret handoff, one normal Dagger invocation, and sanitized status reporting. It contains no Terraform init/plan/apply/destroy or API cleanup implementation, including in `if: always()` steps. Reporting steps may run on failure but cannot promise recovery from a killed runner. No Dagger Cloud is used and the existing offline templates are not migrated in this pilot. A single live status signal avoids duplicating a secret-bearing job.

Alternative considered: workflow CRUD plus an unconditional Terraform cleanup step. Rejected because lifecycle ownership would be split, cancellation could bypass cleanup, and local runner state would disappear.

### 5. Dedicated Wasabi recovery state and receipts

The selected recovery store is a dedicated Wasabi sandbox prefix isolated from production. Each run has separate state, protected checkpoints, and durable ledger/phase receipts; no shared production state, credentials, or backend key is reused. Separately scoped CI credentials reach Dagger only through runtime secret channels. Validate exact endpoint, region, bucket/prefix scope, encryption, access restrictions, version/checkpoint identity, and retention before use. Protect snapshots with verified encryption and restricted access; never publish state, plans, credentials, backend secret config, or raw provider logs as generic Actions artifacts. Return only allowlisted non-secret run/resource/phase/outcome metadata.

Intent must be durably committed before effects; inability to persist/reconcile intent stops mutation. Completed cleanup is recorded only after API absence and state reconciliation. Retain unknown/failed run evidence until reconciliation, and apply reviewed retention to completed runs without deleting unresolved recovery material. Planning chooses this strategy but neither provisions storage nor authorizes access; later setup and live qualification need their own scoped authorization.

### 6. Qualify locking and fence every writer

Qualification must establish the exact Wasabi/backend behavior for conditional writes, object/version identity, state locks, renewal, release, and stale ownership. Do not infer AWS S3 conditional-write or lock-file guarantees from S3 compatibility. Record supported semantics and test them with the exact selected Terraform/backend/runtime tuple before live DNS mutation. Use per-command state locking plus a qualified maintenance ownership/fencing protocol across canary, janitor, reconciliation, local callers, and external writers. Revalidate ownership at phase/effect boundaries; a lost lease or unexpected state/ledger generation stops further effects.

Actions concurrency with `cancel-in-progress: false` limits that workflow only. It does not fence a manual CLI, another workflow, or a previously stalled process. Age/lease expiry alone cannot prove an old writer stopped or prevent its later request reaching Cloudflare. Recovery must establish prior writer termination and reconcile in-flight effects before takeover; if writer exclusion or required conditional-write semantics cannot be proven, fail closed and retain the run for explicit operator reconciliation, not an invented distributed lock guarantee.

Operator decision, 2026-11-15: use non-expiring conditional Wasabi ownership
claims with expected-generation checks. There is no automatic claim expiry or
takeover. Revalidation is the ownership-renewal boundary; an unavailable or
changed claim stops effects rather than extending assumed authority. Recovery
requires explicit operator-established prior writer termination and exclusion
of other writers, followed by authoritative effect reconciliation. A claim is
cooperative coordination, not an API fence against an external writer bypassing
the protocol. Without established exclusion, mutation stays blocked. This
decision authorizes offline design/implementation, not storage provisioning,
credential access, backend qualification or live execution.

Subsequent operator approval, 2026-11-15: after verified DNS/state cleanup,
conditionally create and read back an immutable per-run completed receipt;
CAS the active claim to completed, binding the archive key, opaque version and
original claim version. A successor verifies the exact completed ledger/archive
body before CAS replacement and retains its predecessor pointer. Pending,
unknown, stale or unverifiable outcomes remain blocked without takeover.
Completed failures may hand off only after independently successful destroy
and authoritative absence; the failed primary outcome is retained.

The selected backend is `sandbox-ghe-actions-ci`, `us-east-1`,
`https://s3.us-east-1.wasabisys.com`, prefix `cloudflare-live-ci/v1/`.
State uses `runs/<run>/terraform.tfstate` with native `.tflock`; generation-
specific immutable checkpoints and completed receipts stay under that run.
`maintenance.json` is the cooperative global claim. Boto3/botocore 1.44.3
are frozen in `uv.lock`; the fixture locks Cloudflare 5.16.0 using the
foundation's reviewed hashes. All checkpoint/ledger puts require AES256 SSE
and durable object versions, and all reads/writes are bounded without SDK
retries. Historical versions are not permanently deleted. The operator enabled
bucket versioning and reviewed both credential policy boundaries; those access
and retention assertions remain attributed operator evidence, not an API fence
against administrators or uncoordinated external writers.

S3 qualification proves conditional acquisition, stale/competing refusal,
versioned readback, encryption metadata and retained versions after delete-marker
cleanup. A separate provider-free native Terraform root then proves refusal
while its exact owned lock is held, owned release/absence and a zero-change
plan. `operation=qualify` stops there and labels its result distinctly; it never
enters the DNS lifecycle. Normal execution requires both measured gates first.

The operator also authorized a feature-only initial Actions pilot. Its reviewed
full SHA and exact branch are admitted using temporary repository-scoped
variables before environment selection plus a temporary exact environment
branch rule. PRs/forks/`pull_request_target` never become trusted. Normal main
and schedule execution remain disabled by default; feature admission is removed
after a known terminal pilot. No merge or recurring activation is authorized.

Recovery approval, 2026-11-15: preserve the entire original unresolved ledger
and opaque claim version in an immutable recovery snapshot before conditional
owner transfer. The recovery pointer retains the original generation, actor,
run and explicit authorization evidence. Existing persisted schema-1 ledgers
without that optional pointer remain readable; unknown fields remain rejected.
Only cleanup-state/destroy/absence receipts may follow recovery. Completion and
successor verification include that snapshot, so successful cleanup cannot
rewrite the original unknown pilot as successful. Expected immutable claim/state
VersionIds, independently terminal exact Actions attempt/jobs and explicit
operator external-writer exclusion precede transfer. Missing/partial state,
unverified API identities, stale versions and uncertain transfer stay blocked.
Read-only observation is available without a mutation-qualified transport, but
that transport cannot qualify, put or delete. There is no force unlock, blind
apply replay, broad API delete or automated claim takeover.

### 7. Separate explicit reconciliation and bounded janitor

Expose a separate Dagger reconciliation entry point taking a non-secret run identity; runtime credentials remain separately supplied and scoped. A hard-cancelled/unknown run is not automatically replayed by the next normal canary. Obtain explicit reconciliation authorization, establish exclusive ownership and prior termination, load protected evidence, query exact intended names/known IDs, and reconcile partial or missing state before guarded cleanup. Unknown ownership or uncertain prior effects blocks deletion/retry. Do not infer success from a missing runner or missing state alone.

A scheduled/manual Dagger janitor lists only exact `gha-*.*.ci.solomonhd.ai` candidates older than the timeout-plus-propagation reserve. It defaults to report-only; deletion requires reviewed explicit authorization and verified run ownership, inactivity/termination, and shared fencing. Unresolved/active runs are reported for explicit reconciliation rather than age-only deletion. Every deletion is exact-name/ID verified and reported with non-secret identifiers, without logging unrelated zone inventory or tokens.

### 8. Validate public DNS with bounded retries

After create and update, the job polls public resolvers until the expected value appears or a bounded deadline expires. After destroy, Cloudflare API absence is authoritative; public negative lookup is informational because recursive caches may retain the record until TTL expiry.

## Risks / Trade-offs

- [Zone-scoped DNS token can still alter any `solomonhd.ai` record] → Restrict workflow contexts/environment, keep permissions minimal, mask secrets, and rotate the dedicated token independently.
- [Runner termination bypasses cleanup] -> Preserve Wasabi intent/state/receipts, report unknown, and require separate authorized reconciliation; janitor age alone is insufficient.
- [Public DNS propagation is variable] → Use low supported TTL, multiple bounded retries, and separate API verification from recursive-DNS verification.
- [Janitor or recovery races an active writer] -> Qualify backend semantics and shared fencing, verify termination before takeover, and fail closed on unknown ownership.
- [Two existing workflows duplicate offline checks] -> Add one thin live workflow and one status integration point without migrating other templates or duplicating secret-bearing jobs.
- [Backend credentials broaden exposure] -> Scope Wasabi credentials to the dedicated sandbox prefix, verify encryption/access controls, and keep both Cloudflare and backend credentials in runtime Dagger secret channels.

## Migration Plan

1. Accept the repaired test baseline and execution foundation, consuming the parent's exact beta-first qualified tuple or explicit recorded 0.21.11 fallback; exact release discovery is an early parent acceptance task, not a blocker to completing this plan.
2. Implement the DNS-only fixture and one normal lifecycle entry point with offline boundary, failure-injection, disclosure, and documentation tests.
3. Under separate setup authorization, establish the Wasabi sandbox prefix and scoped credentials; qualify encryption, conditional-write/lock behavior, phase receipts, interrupted-state recovery, and all-writer fencing before DNS mutation.
4. Implement the separate reconciliation entry point and report-only janitor; prove unknown outcomes, prior termination, exact ownership, and deletion authorization gates.
5. Under scoped live authorization, run the Dagger fixture locally with zone-scoped credentials and verify no Tunnel calls, then configure verified GitHub environment/ref controls and the thin Actions adapter.
6. Run authorized manual Actions CRUD/cleanup acceptance and controlled validation/termination/reconciliation cases. Review janitor report-only output before separately authorizing guarded deletion of an aged test record.
7. Record qualified feature acceptance before merge. After acceptance, separately authorize initial nightly activation and decide required versus informational status from observed reliability.

Rollback disables new scheduled runs, reconciles all active/unknown runs under scoped authorization, and verifies no owned DNS residuals before retiring credentials or protected recovery material. Preserve the access needed to finish unresolved cleanup; do not delete evidence merely because a workflow is disabled. It does not affect records outside the namespace.

## Open Questions

- Choose the final schedule frequency after measuring Cloudflare propagation and workflow duration; nightly is the initial recommendation.
- Decide whether the live canary is a required `main` status signal or an informational scheduled signal after observing reliability.

## Closeout

- Commit/push, review, merge, publication, specification sync, and archive are separate lifecycle actions; qualified feature acceptance precedes merge. No provisioning, credential access, schedule enablement, or live reconciliation is authorized by artifact approval alone.
- The initial nightly schedule and status decision remain explicit rollout work after pilot acceptance. Keep other workflow-template migrations and Dagger Cloud excluded.
