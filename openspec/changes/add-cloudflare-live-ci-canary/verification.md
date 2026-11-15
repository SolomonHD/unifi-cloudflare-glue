# Canary Implementation Evidence

## Foundation Prerequisite, 2026-11-15

Task 1.1 consumes the existing repaired-baseline and execution-foundation
receipts, not new live checks. The selected upstream revision is
`614c6aea5e2c92417e4e7d08882ccdcb4113eb33`. Read-only source inspection confirmed
the pins in `scripts/dagger-qualified.sh`, `dagger.toml`, and
`src/main/toolchains.py` agree with the following identities.

| Component | Accepted identity |
| --- | --- |
| Dagger CLI | 1.0.0-beta.27, SHA-256 `d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075` |
| Engine | `registry.dagger.io/engine@sha256:ad121f720ed9bfb8e740f99dd783fa8472965a5e262fc64ff3ef2634cea1e6dd` |
| Python SDK | `9394f7454139f1ee2ca35be20e585b1e54f06cc2`, v1.8.0, generated beta24 API view |
| KCL | Native 0.12.4 archive, SHA-256 `01dc1d8914ed8fdfac7e8b34cc155227cf7f155ef8760f741f35b0f8529f08ca` |
| Terraform | 1.13.5, image digest `sha256:6bbb82d575aa7bd4f0a2c6e3a0838ab9590426c08a71d7a2783643f01004d356` |

`docs/dagger-runtime-qualification.md` records the repaired 263-test baseline
and subsequent 593-test local and qualified-Dagger foundation checks. Its
2026-11-15 consumer handoff supersedes the earlier pending technical-gate text
for this exact candidate: matched remote module/KCL resolution, 21 consumer
checks and the separately authorized production-read operation
`27fc831c-ed0c-43b8-be96-59970e55551e` with zero add/change/destroy/replace.
The handoff is attributed evidence, not an independently repeated preview.

Foundation tasks 6.2 and 6.3 are checked; consumer task 4.3 and promotion remain
separate holds. The canary does not depend on
`migrate-to-ubiquiti-community-unifi`. Stable Dagger 0.21.11 remains unaccepted.
Neither the production backend's disposable lock test nor its scoped identity
qualifies the new canary sandbox backend, credentials, maintenance fencing or
runner-loss recovery. No credentials were accessed or infrastructure changed
by this prerequisite inspection.

## Implementation Hold

Initial read-only `gh api --hostname github.com` inspection on 2026-11-15 confirmed
`SolomonHD/unifi-cloudflare-glue` is public, its default branch is `main`, and
its environments inventory is empty. No `cloudflare-live-ci` environment,
branch protection policy, runtime secret bindings or live credential scope
had been verified at that time. This environment-setup observation is superseded
by the authorized setup receipt below; credential scope is still unverified.
An initial command used the workstation's ambient GHES
host and timed out; the explicit GitHub.com query above resolved the intended
repository. Neither response establishes a GitHub.com outage.

Before the effectful lifecycle or its workflow can be completed, the
protected-store and writer-exclusion contracts need these remaining inputs:

- The exact sandbox endpoint, region, bucket/prefix, scoped identity,
  encryption and retention controls, separate from production.
- A pinned runtime receipt client and conditional generation/version protocol,
  including recovery when Terraform state advances but a receipt write fails.
- Authoritative exclusion/termination evidence for stalled prior writers and
  external callers, including in-flight request reconciliation before takeover.
- The binding between reviewed recovery/janitor authorization and exact run,
  state generation and resource identities.

The operator subsequently approved non-expiring conditional claims with
generation checks, no automatic takeover, and explicit operator-established
prior termination/exclusion for recovery. This resolves the ownership-policy
choice only. The concrete sandbox identity/security controls, transport
qualification and completed-claim history/successor contract remain open.

The existing Terraform backend adapter is not a ledger client. Production's
qualified disposable lockfile test does not qualify the new sandbox protocol.
Generation checks and Actions concurrency cannot fence an already-issued
Cloudflare request. No distributed-lock guarantee, automatic takeover, fake
live adapter or successful-cleanup claim is introduced while these choices
remain unresolved. Offline identity/policy components are preparation only;
there is no runnable live canary entry point or activated workflow yet.

## Offline Admission Policy

`src/main/canary_policy.py` admits only GitHub-provided context for the exact
repository, `refs/heads/main`, branch ref type, and push/schedule/manual events.
Twenty tests in `tests/unit/test_canary_policy.py` passed using
`uv run --offline --frozen --no-sync pytest tests/unit/test_canary_policy.py -q`.
They cover PR and `pull_request_target`, fork repositories, untrusted dispatch
refs, missing/malformed claims, rejection before a simulated credential
acquisition and diagnostic non-disclosure. This completes task 1.4's offline
policy tests, not tasks 3.1-3.3's actual workflow integration. The policy must
be paired with a job-level pre-environment condition and verified GitHub
environment controls; caller-supplied dispatch inputs are not trusted claims.

## Fixture And Naming Preparation

`src/main/canary_identity.py` validates canonical positive-decimal run labels,
DNS label limits, the two exact record names, trusted zone identity, TXT/CNAME
pairing, resource kind and unproxied settings. Its 88 offline tests also parse
the fixture at `terraform/cloudflare-canary` and restrict resource/data kinds.
The CNAME points to the sibling TXT owner, not to its own subtree.

This is partial work for tasks 2.1/2.2, not completed lifecycle integration.
Neither apply nor cleanup exists yet to exercise the validators at actual
effect boundaries. The fixture is not initialized/planned/applied and has no
selected recovery backend or newly acquired provider lock. It must not be
used as a local-state workaround for the missing qualified backend protocol.

## Lifecycle Core

`src/main/canary_lifecycle.py` defines a dependency-injected journal/driver
orchestrator without selecting any runtime transport. It commits phase intent
before effects, rechecks ownership, retains primary and cleanup outcomes, and
attempts destroy only after observed completed failures with available state.
Unknown effects, failed persistence or ownership loss stop without destroy or
automatic retry. Missing state requires reconciliation. Hard interruption is
not converted into a claimed finalizer result.

Twenty-four synthetic tests passed in `tests/unit/test_canary_lifecycle.py`, covering
normal create/update/zero-drift/destroy, partial completed failures,
validation-failure handling, missing state, drift, backend/ownership loss,
failed destroy/residual checks, combined primary/cleanup failure, unknown
effects, process interruption and failed cleanup-result/final receipt writes.
No native Terraform/provider call is exercised
by these tests. This is partial implementation of tasks 2.4-2.8, not proof that
the eventual runtime adapter persists state or enforces deadlines. A public
adapter must raise nonzero on every failed/unknown report; none is exposed yet.

## Non-Expiring Ownership Preparation

`src/main/canary_store.py` implements a synchronous injected conditional-store
protocol. The immutable run identity, owner, generation and phase receipts
share one maintenance object; phase intent/result writes use opaque expected
versions and confirmed readback. Failed CAS, unavailable ownership, uncertain
commits and unexpected state/ledger generations block the session without
automatic retry or takeover. The last confirmed ledger and last attempted
proposal remain available to the caller as distinct evidence.

The qualification gate binds the exact endpoint, region, bucket, prefix and
runtime identity plus mandatory security/semantic/exclusion attestations.
Setting flags is not backend qualification; separately authorized evidence
must substantiate every flag. Tests use an in-memory transport only; no live
Wasabi transport, checkpoint implementation or credential handling is selected.

Sixty-five synthetic store tests cover competing/stale writers, missing/lost
ownership, changed generations/identity/version, precondition races, backend
loss, uncertain writes/effects and qualification failure. This remains partial
work for tasks 2.7/2.8. The maintenance claim is deliberately retained: safe
verified-completion/history/successor handling is not implemented. It cannot
yet support recurring runs, recovery or a janitor, and is not wired to the
lifecycle's journal interface. No task is checked merely for an unbound protocol.

The proposed immutable-history plus completed-claim CAS/successor transition
was presented for operator review; that question was dismissed. Dismissal is
not approval, so the transition was not implemented and the integration hold
remains. The approved non-expiring/no-takeover policy itself is preserved.

## DNS Verification Preparation

`src/main/canary_dns.py` provides exact-zone/exact-name Cloudflare GET
verification and public DNS polling with injected timeout-aware resolvers.
The HTTP helper disables redirects/proxies, bounds response bytes and I/O
timeouts, checks operation deadlines, and validates envelopes/pagination before
accepting a result or absence. It does not query account/Tunnel endpoints.
Metadata excludes record content, credentials and raw provider diagnostics.

Ninety-four offline DNS tests passed, including strict zone/resource/response
identity, malformed/incomplete pagination, API residuals, bounded TXT/CNAME
propagation and sentinel non-disclosure. No real HTTP/DNS lookup was made.
The production public-resolver adapter, lifecycle error translation and runtime
Secret mounting remain unbound. These helpers do not complete the public
Dagger lifecycle or claim any live propagation measurement.

## Verification, 2026-11-15

- Final full `bash scripts/verify-offline.sh`: 904 passed, no skipped tests;
  Black/isort, mypy across 13 source files, compilation and all seven native
  KCL entry points passed. Existing pytest/plugin deprecations remain warnings.
  This verifies the current working tree, including preserved concurrent
  split-DNS changes; it does not attribute every test addition to this canary.
- An initial full-suite collection found an import collision between the
  repository's existing top-level `main` imports and the new policy test's
  package import. Aligning that test with the existing direct-module import
  convention fixed it; the complete suite above then passed.
- `openspec validate add-cloudflare-live-ci-canary --strict --store
  unifi-cloudflare-glue`: passed.
- `git diff --check`: passed.

No workflow was added, so no new workflow lint result is claimed. Task 5.7
remains unchecked while the implementation/workflow is incomplete. Existing
acceptance-document edits were preserved. No credentials, DNS effects, backend
qualification, environment setup, schedule activation, commit, push, merge or
archive occurred.

## Authorized GitHub Environment Setup, 2026-11-15

The operator supplied four 1Password references and explicitly authorized the
`Configure environment` action: create/configure `cloudflare-live-ci` in
`SolomonHD/unifi-cloudflare-glue`, restrict deployments to `main`, set three
credential secrets and a bucket-name variable. This did not authorize workflow
execution, schedule activation, bucket-content access or DNS mutation.

MCP metadata confirmed the Cloudflare field and the three Wasabi fields. Its
reference checker does not parse section-qualified paths correctly; no field
was renamed or credential value revealed to work around that limitation.
The healthy MCP execution container had Python but no `gh` CLI or workstation
authentication context, so the workstation CLI path was used for the transfer.

Actual workstation: `SOL-3D-MIDSEASON`, account `solomong`, CLI
`/usr/local/bin/op`, GitHub CLI `/usr/bin/gh`. Desktop `op signin` succeeded
(exit 0, 5024 ms, 180-second deadline), then `op whoami` succeeded
(exit 0, 396 ms, 30-second deadline). Metadata confirmed the intended
`Service_Credentials` vault ID. Sign-in/session output was captured privately,
not printed or saved to a file.

The exact section-qualified references all resolved successfully through the
workstation CLI. Values stayed in child-process memory and credential bytes
were piped into `gh secret set` via stdin. They were not placed in command
arguments, source files, temporary plaintext files or tool output. The bucket
name is non-secret and was stored as an environment variable.

| GitHub binding | Source reference | Readback |
| --- | --- | --- |
| Secret `CLOUDFLARE_API_TOKEN` | `op://Service_Credentials/cloudflare/GitHub Actions API Token` | Present, updated `2026-11-15T02:26:40Z` |
| Secret `AWS_ACCESS_KEY_ID` | `op://Service_Credentials/GitHub Automation PATs/Wasabi ci user/Access Key` | Present, updated `2026-11-15T02:26:41Z` |
| Secret `AWS_SECRET_ACCESS_KEY` | `op://Service_Credentials/GitHub Automation PATs/Wasabi ci user/Secret Key` | Present, updated `2026-11-15T02:26:41Z` |
| Variable `WASABI_BUCKET` | `op://Service_Credentials/GitHub Automation PATs/Wasabi ci user/Sandbox Bucket Name` | Present, matched supplied source in memory |

Before credential upload, authoritative API reads confirmed custom branch
policies enabled and exactly one policy: `name=main`, `type=branch`. Independent
post-transfer reads confirmed the same environment/rule and all three secret
names/timestamps. No tag rule or required-reviewer rule was configured. These
controls do not substitute for the future workflow's trusted-event/job checks.
GitHub secret values cannot be read back; name/timestamp verification proves
installation metadata, not successful provider authentication or policy scope.

Task 1.3 remains partial because sandbox zone metadata and workflow integration
are not complete. No Wasabi/Cloudflare API validation, backend qualification,
new workflow, activation, publication or Git closeout occurred. Credential
availability does not resolve the completed-claim history/succession hold.

## Canary Worktree Isolation, 2026-11-15

At the operator's request, canary work moved to branch
`change/add-cloudflare-live-ci-canary` in
`/home/solomong/Code/Misc/.worktrees/unifi-cloudflare-glue/add-cloudflare-live-ci-canary`,
based on committed revision `614c6aea5e2c92417e4e7d08882ccdcb4113eb33`.
Only canary source/tests, fixture, documentation and change-artifact edits moved.
The primary checkout remains on `modernize-legacy-unit-test-contracts`; its
unrelated tracked diff matched byte-for-byte before/after the move. The separate
closeout worktree was untouched. No changes were committed, pushed or merged.

The machine-local OpenSpec store `unifi-cloudflare-canary` points to this
worktree; the original `unifi-cloudflare-glue` registration remains unchanged.
Use `--store unifi-cloudflare-canary` for this checkout's change operations.
Store metadata and the independently bootstrapped `.venv` remain Git-ignored.

`uv sync --offline --frozen` succeeded in the new worktree. Its full
`bash scripts/verify-offline.sh` passed 884 tests without skips, Black/isort,
mypy across 13 source files, compilation and all seven KCL entry points.
The earlier 904-test mixed-checkout result included 20 concurrent split-DNS
tests belonging to modernization; those unrelated changes were intentionally
not moved into this branch. Strict validation with the new store passed.
The worktree move changes no live authorization, credential binding, workflow
activation or outstanding implementation/acceptance gate.

## Rebase Onto Merged Main, 2026-11-15

The operator requested waiting for modernization to merge, then rebasing the
canary onto main and continuing. GitHub.com PR #54 merged at
`2026-11-15T02:47:27Z` as
`342f75b9df102f8758686bb1472693cf77b3f761`. Fetch and authoritative PR metadata
confirmed the merge; the temporary recurring merge check was cancelled.

A named, path-scoped stash preserved only the known canary files. Because
the canary had no unique commits beyond its former modernization base
`614c6aea5e2c92417e4e7d08882ccdcb4113eb33`, rebase used that base as the
upstream boundary and the exact merged main SHA as the new base, without
replaying the squashed modernization commits. The saved canary changes applied
without conflicts; aggregate Git blob fingerprints matched before/after.
Other worktrees and their edits were not changed.

After restoration, full `bash scripts/verify-offline.sh` passed 904 tests,
Black/isort, mypy across 13 source files, compilation and seven KCL entry
points. The 20 additional split-DNS tests now come from committed main.
Strict OpenSpec validation and `git diff --check` passed. Canary changes
remain uncommitted. This rebase does not resolve or approve the outstanding
completed-claim history/succession design, nor publish a canary workflow.

## Approved Implementation And Live-Pilot Scope

On 2026-11-15 the operator explicitly approved the immutable-archive then CAS
completed-claim handoff, sandbox versioning enablement, both reviewed credential
policy boundaries, and a canary-only commit/push plus exact-SHA hosted pilot.
Merge, production changes and recurring activation remain excluded. The initial
feature-push pilot is explicitly authorized because a new workflow cannot be
manually dispatched before default-branch registration; later manual acceptance
is still outstanding. The prior dismissed design questions remain historical,
not current holds.

Metadata resolved the exact bucket `sandbox-ghe-actions-ci` and `us-east-1`.
The authorized versioning PUT returned 200; GET then confirmed `Enabled`.
The selected prefix is `cloudflare-live-ci/v1/`; no production state is used.
The bucket lifecycle query returned `NoSuchLifecycleConfiguration`, rather than
an expiration policy. The operator confirmed no broad user/group grants and
only Zone Read/DNS Edit for `solomonhd.ai`, without Tunnel/production scope.
These are attributed policy-review assertions, not an independently retrieved
Cloudflare token policy or new CI-user IAM policy inspection.

Implementation now includes strict completed-ledger history/succession, bounded
version-aware AES256-SSE S3 transport with no retries, exact native Terraform
fixture/plan/state allowlists, immutable encrypted checkpoints after completed
effects, DNS-only API/DoH verification, the normal/qualification-only Dagger
entry point, and the thin gated workflow. Secrets remain runtime Secret inputs.
The selected boto3/botocore 1.44.3 are frozen with transitive dependencies in
`uv.lock`; only the foundation Cloudflare 5.16.0 lock block is reused, without
Tunnel/random providers. No broad API-delete fallback or claim stealing exists.

An independent safety review found the initial public-DNS budget shorter than
the fixture's 60-second TTL. The driver now permits a bounded 180-second window
per record; a synthetic warmed-cache test proves acceptance after TTL expiry.
Review confirmed no other concrete disclosure/takeover/false-success issue.
Native nonzero apply is additionally treated as unknown after protected
checkpointing: process exit does not prove a timed-out Cloudflare request ended.

The first beta27 verification failed collection because the existing offline
input allowlist omitted the new bootstrap script/workflow. Adding only those
two exact non-secret inputs fixed it. Full qualified beta27 verification then
passed 1,137 tests, typing across 17 source files, formatting, compilation and
all seven KCL entry points. The subsequent qualification-only admission change
is tested/reverified separately before publication. `actionlint v1.7.12` passed
the workflow, with external shellcheck disabled; no broad migration of existing
offline workflows occurred.

The hosted bootstrap downloaded the exact beta27 archive without executing the
remote installer and verified the executable's accepted SHA-256. SDK generation
used the pinned beta27 engine and immutable SDK source; `api functions` exposed
`test-cloudflare-dns-canary`, and actual CLI help matched the workflow arguments.
Secrets/backend qualification/DNS live acceptance were not inferred from these
credential-free checks. Reconciliation/janitor entry points remain unfinished.

The final pre-publication candidate passed 1,138 tests both locally and inside
the qualified beta27 runtime, including a local-qualification-only context that
cannot admit the normal DNS operation. `operation=qualify` reports its mode and
stops before claim/DNS lifecycle creation. Formatting, typing (17 source files),
seven KCL entries, pinned actionlint, strict specification validation and diff
whitespace checks passed. Completed implementation tasks are checked separately
from the still-pending backend/live/recovery acceptance tasks. The next effect
is the separately authorized local sandbox backend qualification, not DNS CRUD.

## Backend Qualification And Initial Hosted Failure

Committed candidate `233c71c865c98940342c0858e9e428a7820ffe2e` passed authorized
local backend-only qualification on 2026-11-15. The first desktop sign-in exited
1 after 60,508 ms within a 180-second wrapper deadline; no credential reads or
backend effects followed it. Its cause remains unclassified, not a claimed
wrong PIN or wrapper timeout. After explicit operator unlock/retry, signin
succeeded in 7,053 ms, whoami in 403 ms, and the intended vault matched.
The three supplied fields resolved privately into the Dagger child environment.

Qualification run `gha-1794714752-1-1` completed in 15,984 ms with
`operation=qualify`, qualified/primary/cleanup all verified. This measured the
exact scoped CI identity, endpoint/bucket/prefix, AES256 SSE/versioned reads,
conditional-create/update refusal, native Terraform held-lock refusal, exact
owned release/absence and a successful provider-free plan. It performed no
DNS CRUD. The service-side policy scope remains operator-reviewed evidence.

Temporary repository admission variables selected only the canary branch and
full candidate SHA. Environment rule 66765247 added that exact branch alongside
unchanged main rule 66759358; the operator-review variable was verified before
the push. Main/schedule enable variables remained unset. The new branch push
started the only hosted pilot:
`https://github.com/SolomonHD/unifi-cloudflare-glue/actions/runs/43674454065`.
Attempt 1/job 132691420572 completed with failure at `2026-11-15T03:55:53Z`,
47 seconds elapsed. Bootstrap/checkout succeeded; the Dagger step exited 2.
That result is failed acceptance, not verified cleanup.

Read-only projected inspection of `gha-1794714939-43674454065-1` confirmed an
uncompleted claim pending at create, valid protected state and exactly one TXT
and one CNAME whose API IDs match that state. The only difference between native
state pull and the stored state was ordering of `check_results`/nested objects;
a second projected comparison confirmed order-only equivalence. No raw state,
record content, credentials or provider logs were disclosed. The strict equality
check had therefore blocked checkpointing before any cleanup. The fix sorts
only those unordered check collections, retains all statuses/values, writes
authoritative S3 state bytes, and binds effect receipts to the exact successfully
checkpointed generation. Other state changes and missing checkpoints fail closed.

The separate Node20 checkout warning was non-fatal. The new workflow alone now
pins checkout v5 commit `fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09`, whose
official action declares `runs.using: node24`; persistence remains disabled.
No Dagger Cloud configuration is needed. The old run keeps its original warning.

The owned acceptance-SHA variable was removed to prevent a blind normal rerun;
the original claim and feature environment access were retained pending recovery.
The operator separately authorized exclusive reconciliation/cleanup of only this
failed run. Exact Actions attempt metadata and all jobs are terminal and bound
to the original SHA/repository/workflow. Recovery requires immutable claim/state
VersionId preconditions, an immutable untouched prior-ledger snapshot, CAS owner
transfer, only destroy/absence phases and fresh state/API verification. The old
unknown outcome remains in its snapshot and never becomes a passing pilot.
Missing/partial state, stale versions, lost proof/ownership and uncertain writes
block effects. Read-only inspection uses a transport that cannot put, delete or
qualify. Existing schema-1 ledgers without recovery fields remain readable
specifically because the original persisted failed run uses that schema.

The recovery/fix candidate passed 1,239 tests locally and inside beta27, mypy
across 19 source files, formatting, seven KCL entries and pinned workflow lint.
At this receipt point the authorized recovery has not yet been executed.

## Verified Recovery And Corrected Hosted Pilot

Reconciliation source `934351bb0d5905000e4015ae3baa59dcffa1cfa8` was committed
before execution. A desktop confirmation/sign-in attempt failed before any
credential read or backend action (exit 1, 61,052 ms, 180-second deadline,
unclassified CLI failure). After the operator explicitly selected another
desktop authorization attempt, signin succeeded in 7,077 ms and whoami in
414 ms; the intended vault matched and the three fields resolved privately.
No repeated prompt loop or alternate credential route was used.

The authorized recovery of `gha-1794714939-43674454065-1` completed in
30,752 ms with `operation=reconcile`, original outcome unknown, ownership
transferred and cleanup verified at absence. Immutable preconditions were
claim VersionId `001794714949779472316-CZTUzpwBsu` and state VersionId
`001794714951587232183-DCED7n_8Gm`. The preserved original ledger and recovery
authorization precede CAS transfer; native state-based destroy and exact-name
API/state absence precede completion. The original hosted attempt remains failed.

First-pilot admission was restored to only unchanged main rule 66759358 and
zero repository variables. A new temporary feature rule 66809185 plus exact
branch/SHA selectors then admitted only the tested corrected commit. The push
started `https://github.com/SolomonHD/unifi-cloudflare-glue/actions/runs/43719329517`.
Attempt 1/job 132827691284 ran from `2026-11-15T13:30:25Z` to
`2026-11-15T13:32:20Z` and succeeded, 115 seconds overall. A privately filtered
log read verified the strict metadata result:

```json
{"cleanup":"verified","operation":"normal","phase":"plan","primary":"verified","qualified":true,"revision":"934351bb0d5905000e4015ae3baa59dcffa1cfa8","run_prefix":"gha-1794749470-43719329517-1"}
```

This proves the hosted create/API/public-DNS/update/zero-drift/destroy/absence
path and successful successor verification of recovered history on that exact
source/runtime. All checkout/bootstrap/lifecycle steps succeeded; the checkout
used the Node24 v5 pin and the check run has zero annotations. The run produced
zero generic Actions artifacts. The 115-second figure is total job time, not
an invented per-phase propagation measurement.

After verified success, only owned temporary rule 66809185 and the two owned
repository admission variables were removed. Readback confirmed only main rule
66759358 and zero repository variables. Main/schedule enable flags remain unset;
secrets, bucket variable and operator-review prerequisite remain available.
No merge, archive, required-status policy or recurring activation occurred.

Pilot sample: one failed implementation revision followed by one passing fixed
revision, not evidence of a statistically reliable recurring service. Recommend
informational/manual opt-in initially, with the proposed nightly cadence still
disabled pending explicit rollout approval and further measurements. Remaining
live local-normal/controlled-failure/aged-janitor acceptance is not inferred from
these results; janitor implementation and its reviewed selection tests remain.

Four additional boundary cases explicitly verify nonzero failure for primary
failure, failed destroy, residual/absence failure and unknown outcomes. These
are synthetic boundary tests, not claimed live controlled-failure or hard-kill
acceptance. The follow-up audit checkpoint changes documentation/checklists and
tests only; the hosted implementation actually exercised remains exact commit
`934351bb0d5905000e4015ae3baa59dcffa1cfa8`. Tracked progress is 23/33; unperformed
manual/local-normal, forced-failure and aged-janitor acceptance stays unchecked.
