# Execution Contract Spec Reconciliation

## Scope

On 2026-11-14, tasks 5.3-5.4 of `modernize-dagger-execution-contracts`
were reconciled in main specs only: `cache-control`, `config-generation`,
`orchestration`, `plan-generation`, `state-management`, and the necessary
`secret-safe-execution` clauses. Proposal, design and all seven current deltas
were read. The refreshed state/plan deltas and design's deferred DLR-1 govern
remote-only public effects and read-only local previews.

This is specification evidence, not implementation, runtime or deployment
acceptance. No task checkboxes, change artifacts, configuration or application
code were edited by this reconciliation. No commit, spec-sync lifecycle command
or archive operation was performed.

## Clause Disposition

| Area | Replaced contract | Retained intent and obligations |
| --- | --- | --- |
| Cache | Removed boolean `no_cache` tombstone and its timestamp migration recipe; replaced caller cache-busters, source-wide invalidation and command injection with automatic function/exec freshness. | Repeated deploy, plan, destroy and integration calls must observe/dispatch fresh work; deterministic generation remains reusable. Manual labels are bounded non-secret data, not correctness guarantees. |
| Generation | Repaired delta-only main headers; replaced mandatory yq extraction with parser-independent JSON contracts and one deterministic snapshot. | All seven original requirement identities and every scenario identity remain: method rename/signature/call-site migration, MAC normalization/consistency, default test MAC, test IDs, JSON formatting and docstrings. Terraform schema cross-references remain. The redundant migration checklist is now a historical note, not completion evidence. |
| Orchestration | Replaced duplicated generation calls and successful failure strings with shared validated generation, ordered effects and unsuccessful status on failure. | All three original requirement identities and scenario identities remain. Secret-typed authentication parameters, KCL source, pre-execution validation, UniFi prerequisite ordering, bounded success counts and partial-failure visibility remain. Completed snapshots and unknown-effect reconciliation are explicit. |
| Plan | Removed latest defaults, no-cache/timestamp recipes, separate full-plan roots, fragile text-count fallback, backend File ingestion and default raw-plan files. | All 18 original requirement identities and scenario identities remain. Selective credentials/flags, authentication exclusivity/completeness, explicit insecure-TLS opt-in, safe output formats/directories, owner-only raw-artifact opt-in/warnings, provider-secret environment variables (not Terraform plan inputs), post-exec references, documentation and sentinel scans remain. A preview is not approval of independently replanned execution. |
| State | Replaced host Directory write-through, root flattening, removed standalone deployment API calls and unconditional ephemeral/local public effects. | All 11 original requirement identities and scenario identities remain. Remote-only public deploy/destroy rejects invalid selection before generation/init/effects; local previews are read-only. Root/sibling paths, state identity, mutual exclusion, useful mode guidance, backend secret mounts, YAML/HCL address/key/workspace/lineage/locking and no fallback remain. Unknown remote custody requires reconciliation, not retry or rollback claims. Durable local handoff remains unfinished DLR-1. |
| Secrets | Extended ingestion to explicitly formatted Secret-typed backend input and generated-credential disclosure boundaries; repaired placeholder Purpose. | All three original requirement identities and scenario identities remain, including the untouched sensitive-artifact acknowledgement, owner-readable permissions, secure storage/disposal guidance, and non-disclosure through cleanup, errors and defaults. Behavioral tests must exercise real paths. |

Historical S3 locking documentation (including its existing Terraform-version
wording), Azure/GCS diagram choices, and trade-off documentation remain rather
than silently disappearing during state reconciliation. Their retention is not
a new compatibility qualification or implementation claim. Legacy scenario
titles mentioning removed flags/APIs remain as matching identities where the
delta retains them; their bodies now reject or migrate those interfaces, never
require them. The obsolete Boolean no_cache tombstone is intentionally omitted
from normative requirements; its historical failure was a static boolean cache
key that did not guarantee fresh execution.

## Validation Evidence

Installed OpenSpec package: `@fission-ai/openspec` 1.16.1. Commands used the
registered `unifi-cloudflare-glue` store and selected checkout
`/home/solomong/Code/Misc/unifi-cloudflare-glue`.

```bash
openspec validate --specs --strict --json --store unifi-cloudflare-glue
openspec validate modernize-dagger-execution-contracts --strict --json --store unifi-cloudflare-glue
```

- Baseline main-spec validation: 62 specs, 5 passed, 57 failed.
- After reconciliation: 62 specs, 9 passed, 53 failed. All six edited specs
  pass with empty issue lists. Repository-wide exit remains nonzero.
- Strict change validation: 1 passed, 0 failed, empty issue list. The prior
  cache/config/orchestration invisible-requirement and delta-header applicability
  diagnostics are absent.
- `git diff --check` on the six edited specs passes.
- A non-writing identity audit against `git show HEAD:openspec/specs/...`
  found no lost requirement/scenario identities except the intentionally retired
  Boolean no_cache tombstone and four cache scenarios replaced by their exact
  delta scenarios. Rebuilt requirement counts are cache 5, generation 10,
  orchestration 5, plan 19, secrets 4 and state 12.

## Non-Writing Preflight

Inspected `openspec --help`, `archive --help`, `spec --help`, `change --help`,
`validate --help` and `instructions --help`. No standalone full archive/sync
dry-run command or archive `--dry-run` flag is advertised. `archive --help`
was help inspection only, not an archive attempt. Strict change validation
does provide advisory applicability checks, but its success alone is not full
lifecycle readiness.

Additionally invoked only the installed CLI's read/build APIs in Node memory:
`findSpecUpdates(changeDir, mainSpecsDir)`, then
`buildUpdatedSpec(update, changeName, {silent: true})`, then
`new Validator(true).validateSpecContent(update.id, built.rebuilt)` for each
of all seven deltas. No `writeUpdatedSpec`, archive command implementation,
filesystem writer, rename or retirement API was invoked. The rebuilt strings
were discarded, including the proposed new runtime capability.

All seven simulated results validate strictly with no warnings or issues.
Native effective operation counts (`added/modified/removed/renamed`) were:
cache `0/0/0/0`, generation `0/2/0/0`, runtime compatibility `4/0/0/0`,
orchestration `0/2/0/0`, plan `0/6/0/0`, secrets `0/0/0/0`, state `0/5/0/0`.
Nonzero modifications can include retained block separators/formatting; these
are prospective builder counts, not executed sync operations.

This simulation checks delta applicability and rebuilt spec structure, not
task completion, archive destination/locking/write permissions, transactional
filesystem behavior or concurrent future edits. It grants no archive approval.

## Residual Limits

The 53 other failing main specs remain outside the authorized edit set. They
include missing canonical sections, invisible requirements, placeholder purposes
and legacy scenario formatting warnings promoted by strict mode. Examples are
`documentation`, `example-configuration`, `terraform-module`,
`deploy-function-cache-busting`, `documentation-cache-buster`,
`test-integration`, `unifi-deployment` and `cloudflare-deployment`. Those separate
historical specs may still describe removed APIs or caller freshness recipes;
this bounded reconciliation does not claim repository-wide guidance agreement.

The initial apply-instructions command also reported existing `rules.general`
YAML mappings where strings were expected; that configuration warning was not
repaired. No architecture or configuration recovery was attempted. Broader spec
cleanup and all runtime/consumer acceptance require their own scope and evidence.
