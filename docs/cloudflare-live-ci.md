# Cloudflare Live CI Canary

## Current Status

The normal Dagger lifecycle and thin workflow are implemented against the
qualified `1.0.0-beta.27` tuple in [runtime qualification](dagger-runtime-qualification.md).
Live qualification and pilot acceptance remain separate from implementation.
Recurring execution is disabled by default. See the change's
[verification receipt](../openspec/changes/add-cloudflare-live-ci-canary/verification.md).

## Credential Boundary

Create a dedicated Cloudflare token with only Zone Read and DNS Edit on the
existing `solomonhd.ai` zone. Do not include any account-level Tunnel permission,
zone creation permission, `sghd.io` permission or an all-zones resource selector.
The token can still edit any record in its authorized zone; application name
checks do not narrow the token's actual permissions. Review the token's actual
policy before live acceptance. The operator-supplied token was transferred to
GitHub under separate authorization. The operator subsequently confirmed its
restricted policy; no new token was created here and this is operator-reviewed,
not independently inspected API policy evidence.

Rotate this token independently of production credentials. Under separately
authorized setup, create the replacement with the same reviewed scope, update
the protected CI binding, verify a scoped canary with the replacement, then
revoke the old token. An uncertain run must first retain or regain the recovery
access needed for exact resource reconciliation. Never log either token or copy
one into source, Terraform variables, a plan or an ordinary Actions artifact.

The GitHub Environment is `cloudflare-live-ci` in
`SolomonHD/unifi-cloudflare-glue`. Authorized setup on 2026-11-15 verified a
custom deployment policy allowing only the `main` branch, with no tag rule.
A job-level condition must reject
untrusted events/repositories/refs before environment selection. Repeat the
admission check with GitHub-provided claims before executing secret-bearing code.
Manual dispatch inputs cannot override those claims. Trusted repository writers
remain inside the security boundary, even with an environment branch policy.

Cloudflare and sandbox Wasabi credentials must enter Dagger as runtime Secrets
using beta `env://` channels, never ordinary string arguments. The installed
environment bindings are:

| Name | GitHub storage |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | Environment secret |
| `AWS_ACCESS_KEY_ID` | Environment secret |
| `AWS_SECRET_ACCESS_KEY` | Environment secret |
| `WASABI_BUCKET` | Environment variable |

These are snapshots of operator-supplied 1Password fields, not live references;
rotation requires explicitly updating the GitHub copies. The zone ID is resolved
against exact `solomonhd.ai` metadata inside the runtime. The backend is
`sandbox-ghe-actions-ci`, `us-east-1`, endpoint
`https://s3.us-east-1.wasabisys.com`, prefix `cloudflare-live-ci/v1/`.
Versioning is enabled, with no configured lifecycle expiration; the canary does
not permanently delete historical versions. The operator reviewed both
credential policies. Actual backend qualification is measured before each run.
Do not repurpose the production backend configuration or its credentials.

## Protected Recovery Contract

Setup must identify one dedicated sandbox endpoint/region/bucket/prefix and
an identity restricted to that prefix. Agree on per-run Terraform state,
versioned encrypted checkpoints, intent/result ledger and maintenance-ownership
keys before implementation. Run identity includes revision, timestamp, GitHub
run ID and attempt; evidence binds exact zone identity, intended record names,
types, observed resource IDs and state/ledger generations.

Intent must be durable before effects. A failed intent write blocks mutation.
State advancement followed by a failed receipt write is uncertain, not a
successful or automatically retryable phase. Retain failed/unknown evidence
until explicit reconciliation; completed-run retention must not delete unresolved
material. Verify encryption, object/version identity, access restrictions and
retention on the exact sandbox, not by inferring AWS behavior from S3 compatibility.

All mutation paths must share qualified ownership checks, including local
callers, canary, janitor and reconciliation. A generation comparison cannot
cancel a Cloudflare request already in flight. Actions concurrency and elapsed
lease time do not prove prior writer termination or exclude external writers.
If exclusivity or prior termination cannot be established, stop effects and
retain recovery identity. Do not automatically steal an expired claim.

The approved protocol uses non-expiring conditional claims. Revalidation checks
the owner and expected generation; no clock-based expiry or automatic takeover
exists. A claim coordinates participating writers only. Operator-established
exclusion of external writers and prior termination are separate recovery
preconditions, not properties an object-store claim can prove.

## Lifecycle And Recovery

The normal `test-cloudflare-dns-canary` entry point owns create, API/public-DNS validation,
update, zero-drift plan, state-based destroy and exact-name API absence checks.
The workflow must not implement Terraform or API lifecycle logic, even in an
`always()` cleanup step. Existing offline workflow templates remain separate.

Return only reviewed run/resource/phase/outcome identifiers. Primary failure and
cleanup outcome remain distinct; cleanup failure, residuals and unknown effects
all fail the run. Public negative DNS is informational because caches can retain
records; exact Cloudflare API absence is the authoritative deletion check.
Hard cancellation may bypass cleanup entirely.

Recovery is separately authorized for one named run. Establish prior writer
termination and exclusivity, load protected state/ledger, reconcile exact names
and IDs, then perform reviewed cleanup or state repair. Missing state alone
does not prove that nothing was created. Do not blindly repeat an uncertain
apply. A janitor defaults to report-only; age plus namespace is insufficient
for deletion without verified ownership, inactivity and fresh fencing checks.

Rollback disables new runs, reconciles active/unknown runs, and verifies owned
record absence before retiring credentials or evidence. Disabling the workflow
does not clean up records. Nightly activation and required-versus-informational
status are separate decisions after measured pilot acceptance.

## Invocation And Hosted Admission

The new adapter is `.github/workflows/cloudflare-live-ci.gha.yaml`. It installs
only the checksum-qualified beta27 binary, then invokes one Dagger entry point
using runtime Secret channels. Generated `sdk/entrypoint/types.dang` accompanies
the source so hosted runners need no generation step. Boto3/botocore 1.44.3 and
the Cloudflare 5.16.0 provider selection are frozen; the provider lock contains
no Tunnel/random providers.

`operation=normal` performs backend qualification followed by DNS CRUD.
`operation=qualify` stops after backend/native-lock qualification and labels
its report distinctly. Authorized local qualification uses the exact reviewed
source SHA and `event-name=local_qualification`; that context cannot admit DNS
effects. For credentials already supplied to the child environment through
the approved secret-resolution path:

```bash
bash scripts/dagger-qualified.sh api call -m . test-cloudflare-dns-canary \
  --operation=qualify --bucket=sandbox-ghe-actions-ci \
  --revision="$REVIEWED_SHA" --run-id=1 --attempt=1 \
  --repository=SolomonHD/unifi-cloudflare-glue \
  --ref=refs/heads/change/add-cloudflare-live-ci-canary \
  --event-name=local_qualification --policy-reviewed=true \
  --acceptance-sha="$REVIEWED_SHA" \
  --acceptance-branch=change/add-cloudflare-live-ci-canary \
  --cloudflare-api-token=env://CLOUDFLARE_API_TOKEN \
  --wasabi-access-key=env://AWS_ACCESS_KEY_ID \
  --wasabi-secret-key=env://AWS_SECRET_ACCESS_KEY
```

Initial feature acceptance requires explicit authorization, repository-scoped
`CANARY_ACCEPTANCE_BRANCH`/`CANARY_ACCEPTANCE_SHA` variables selecting the exact
branch and reviewed full SHA, and a matching temporary environment branch rule.
These variables must be repository-scoped because admission precedes environment
selection. The initial pilot is push-triggered: GitHub cannot manually dispatch
a workflow not yet registered on the default branch. Remove temporary admission
after a known terminal pilot.

Main pushes/manual runs require repository variable
`CLOUDFLARE_CANARY_ENABLED=true`. Scheduled effects additionally require
`CLOUDFLARE_CANARY_SCHEDULE_ENABLED=true`. Neither is enabled for this pilot.
The proposed schedule is 03:17 UTC; activation and required-versus-informational
status remain separate rollout decisions. The job ceiling is 30 minutes, with
a 25-minute Dagger deadline. DNS polling allows 180 seconds per record, beyond
the 60-second previous-answer TTL. Failed/unknown results are nonzero. No generic
Actions artifact stores state, plans, credentials or raw diagnostics.

Each run creates only two DNS records. Protected storage retains multiple small
ledger/state/lock/checkpoint versions, including failed qualifications. Budget
tens of small versions and at most 30 runner minutes per run until measured
pilot costs/latency are available. Versioning is not free storage; the CI user
cannot configure expiration or permanently erase historical versions.

## Scope And Troubleshooting

Hosted CI covers TXT and unproxied CNAME records only under `ci.solomonhd.ai`.
It must not use the existing Tunnel-count verifier, which queries account-level
Tunnel resources. Full Tunnel tests remain on the existing hardened local
Dagger integration path with separately authorized account-level credentials,
not the hosted DNS token.

- Authentication failure: verify the named runtime binding and actual token
  zone/permission policy without printing its value; do not broaden permissions.
- Propagation timeout: retain primary failure, attempt cleanup only while
  ownership/effects are known, and distinguish API correctness from DNS caches.
- Backend or ownership loss: stop effects and retain run identity; do not fall
  back to local state, Dagger cache or generic Actions artifacts.
- Partial apply or lost runner: explicitly reconcile protected evidence and
  exact API identities after proving termination; do not infer cleanup.
- Failed destroy or residual record: preserve both outcomes and recovery access
  for separately authorized cleanup, rather than report the primary error alone.

This document authorizes no credential access, provisioning, backend test, DNS
mutation, janitor deletion, workflow activation or production operation.

`inspect-cloudflare-dns-canary` is read-only: it projects the retained phase,
state-shape checks, state/check metadata consistency and exact-name API identity
matches. Its transport cannot qualify, put or delete. It never exports raw state.

`reconcile-cloudflare-dns-canary` is a separate explicitly authorized operation.
It requires the exact run prefix, expected immutable claim/state VersionIds and
both `prior-writer-terminated=true` and `exclusive-writer=true`. It independently
checks the public GitHub.com run/attempt, original source SHA, repository/workflow
and terminal jobs, then checks current state and exact API identities. An
immutable recovery snapshot preserves the entire original unknown ledger before
CAS transfer. Only destroy/absence phases can follow. Completion retains the
snapshot reference; it does not turn the original failed run into a passing one.
Missing/partial state, changed versions, missing proof and uncertain transfers
remain blocked without apply replay, imports, broad API deletion or force unlock.

State comparison preserves all values/statuses, normalizing only Terraform's
unordered check-result/object lists. Checkpoints store authoritative remote bytes
and effect receipts require their exact durable checkpoint generation. A harmless
`check_results` ordering difference is not interpreted as drift or silently
discarded; resource/output/serial/status differences remain failures.

The report-only janitor entry point remains unfinished. Never delete a maintenance
object merely to make the next run pass, and never retry an unknown cleanup
without reconciling its snapshot/owner/state first.
