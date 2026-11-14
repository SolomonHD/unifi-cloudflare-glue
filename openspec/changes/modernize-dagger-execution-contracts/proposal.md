## Why

The module's v0.19.8-era execution layer mixes deterministic KCL generation with live Terraform effects, optional caller-managed freshness, and inconsistent failure/state contracts. Qualifying Dagger 1.0 beta early lets the project adopt current module/workspace techniques without first rebuilding around an older release or combining runtime changes with a production provider migration.

## What Changes

- Qualify Dagger v1.0.0-beta.27 as the primary CLI/engine candidate and resolve its compatible exact Python SDK identity, including remote consumer loading; use v0.21.11 only as an explicitly accepted and separately tested fallback if beta qualification fails. Keep Python. Installed CLI/version checks do not constitute runtime acceptance; do not follow a moving latest/beta label or change global tool selection.
- Establish a small shared execution path for generation, Terraform root/backend preparation, fresh live operations, and sanitized outcomes while retaining current provider versions and resource addresses.
- Cache deterministic generation, automatically freshen live plan/apply/destroy and verification operations, and retire command-string/cache-source hacks only after repeated-call tests prove the replacement.
- Pin execution tools and dependency resolutions; replace duplicated YAML/stdout/yq round trips with one validated machine-readable generation result, subject to exact KCL qualification.
- **BREAKING**: Fail unsuccessful commands with sanitized exceptions/nonzero exit status instead of successful strings containing failure text. Correct selective plan/execution root agreement and structured plan counts.
- **BREAKING**: Replace credential-bearing backend File ingestion with Secret-typed transport and an explicit consumer migration. Preserve YAML/HCL semantics, backend address/key and locking; never silently fall back to local state.
- **BREAKING**: Restrict public deploy/destroy to explicit remote backends; reject local-state or missing durable-state selections before mutation. Read-only local previews never imply Directory host write-through. Per the operator's 2026-11-14 scope decision, durable local-state output/recovery is tracked separately as DLR-1 in the design, not claimed complete here.
- Expose credential-free offline verification through the accepted Dagger release; provide Changeset generation only for intentional checkout outputs, not raw plans/state.
- Reconcile contradictory legacy cache, plan, orchestration, and state requirements as part of this change, preserving security invariants and unfinished acceptance work.
- Add opt-in typed split-DNS origin exceptions without changing routes or Terraform JSON: `cloudflare.SplitDNSOrigin {protocol, hostname, port}` and default-empty `split_dns_origins` on explicit configuration, entity generation and direct transform helpers. Retain same-zone rejection by default; allow only exact protocol/normalized DNS hostname/effective-port matches, never suffix wildcards, inherited subdomains or global bypass. Invalid declarations fail closed. This records operator intent, not DNS verification; live acceptance must separately prove connector-internal resolution without a Cloudflare loop.

## Capabilities

### New Capabilities

- `dagger-runtime-compatibility`: Exact-release qualification, Python SDK/manifest compatibility, reproducible tools, and local/CI/consumer execution agreement.

### Modified Capabilities

- `cache-control`: Automatic live-operation freshness without invalidating deterministic inputs or relying on caller timestamps.
- `config-generation`: A shared deterministic KCL execution and validated output boundary, independent of yq implementation details, with narrowly scoped typed split-DNS origin exceptions. Current `generator-output-validation` and `kcl-validation-rules` clauses are reconciled to this contract without changing archived history.
- `orchestration`: Common execution preparation, truthful failure status, preserved post-execution snapshots, and explicit partial/unknown outcomes.
- `plan-generation`: Root agreement, reliable action summaries, and clear separation between preview and approved execution artifacts.
- `state-management`: Fail-closed remote-only effects, read-only preview custody, backend identity/locking preservation, and uncertain-effect reconciliation.
- `secret-safe-execution`: Secret-typed backend ingestion, protected sensitive outputs, and behavioral disclosure regression coverage.

## Impact

Implementation will affect `src/main/main.py`, `src/main/backend_config.py`, Dagger manifests/generated SDK, Python/tool dependency locks, tests, selected CI entry points, and operational documentation. This planning change writes none of those implementation files.

The approved split-DNS revision additionally affects `schemas/cloudflare.k`, `generators/cloudflare.k` and their offline validation/tests. It authorizes no consumer routing edit, production operation or Git mutation. Candidate `38daa8a8131080659acb5e4d59e4a2135eb7d92f` remains blocked for consumer acceptance; tasks 6.2 and 6.3 remain open and must be repeated against the revised exact published SHA after separately authorized commit/push. No replacement SHA is assigned by this documentation revision.

`modernize-legacy-unit-test-contracts` provides the current-contract offline baseline before this refactor; qualification may proceed alongside it, but execution changes depend on that baseline. `migrate-to-ubiquiti-community-unifi` and `add-cloudflare-live-ci-canary` consume the resulting foundation independently. The sibling `portainer-docker-compose` change `adopt-modernized-dns-dagger-workspace` owns consumer pins, workspace configuration, and acceptance. Global mise/chezmoi adoption requires its own authorized host-scoped work. Provider upgrades, production state handoff, Cloudflare canary deployment, Dagger Cloud activation, and migration of other Actions templates are excluded.
