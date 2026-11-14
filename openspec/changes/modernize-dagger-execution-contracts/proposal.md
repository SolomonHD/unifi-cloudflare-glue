## Why

The module's v0.19.8-era execution layer mixes deterministic KCL generation with live Terraform effects, optional caller-managed freshness, and inconsistent failure/state contracts. Qualifying Dagger 1.0 beta early lets the project adopt current module/workspace techniques without first rebuilding around an older release or combining runtime changes with a production provider migration.

## What Changes

- Qualify one exact Dagger 1.0 beta CLI/engine/Python SDK combination first, including remote consumer loading; record v0.21.11 only as an explicit fallback if beta qualification fails. Keep Python.
- Establish a small shared execution path for generation, Terraform root/backend preparation, fresh live operations, and sanitized outcomes while retaining current provider versions and resource addresses.
- Cache deterministic generation, automatically freshen live plan/apply/destroy and verification operations, and retire command-string/cache-source hacks only after repeated-call tests prove the replacement.
- Pin execution tools and dependency resolutions; replace duplicated YAML/stdout/yq round trips with one validated machine-readable generation result, subject to exact KCL qualification.
- **BREAKING**: Fail unsuccessful commands with sanitized exceptions/nonzero exit status instead of successful strings containing failure text. Correct selective plan/execution root agreement and structured plan counts.
- **BREAKING**: Replace credential-bearing backend File ingestion with Secret-typed transport and an explicit consumer migration. Preserve YAML/HCL semantics, backend address/key and locking; never silently fall back to local state.
- Correct local-state persistence through explicit protected state output/recovery rather than implying that a Dagger Directory writes back to the host; reject unsupported persistent-local calls before mutation.
- Expose credential-free offline verification through the accepted Dagger release; provide Changeset generation only for intentional checkout outputs, not raw plans/state.
- Reconcile contradictory legacy cache, plan, orchestration, and state requirements as part of this change, preserving security invariants and unfinished acceptance work.

## Capabilities

### New Capabilities

- `dagger-runtime-compatibility`: Exact-release qualification, Python SDK/manifest compatibility, reproducible tools, and local/CI/consumer execution agreement.

### Modified Capabilities

- `cache-control`: Automatic live-operation freshness without invalidating deterministic inputs or relying on caller timestamps.
- `config-generation`: A shared deterministic KCL execution and validated output boundary, independent of yq implementation details.
- `orchestration`: Common execution preparation, truthful failure status, preserved post-execution snapshots, and explicit partial/unknown outcomes.
- `plan-generation`: Root agreement, reliable action summaries, and clear separation between preview and approved execution artifacts.
- `state-management`: Explicit local-state recovery and backend identity/locking preservation.
- `secret-safe-execution`: Secret-typed backend ingestion, protected sensitive outputs, and behavioral disclosure regression coverage.

## Impact

Implementation will affect `src/main/main.py`, `src/main/backend_config.py`, Dagger manifests/generated SDK, Python/tool dependency locks, tests, selected CI entry points, and operational documentation. This planning change writes none of those implementation files.

`modernize-legacy-unit-test-contracts` provides the current-contract offline baseline before this refactor; qualification may proceed alongside it, but execution changes depend on that baseline. `migrate-to-ubiquiti-community-unifi` and `add-cloudflare-live-ci-canary` consume the resulting foundation independently. The sibling `portainer-docker-compose` change `adopt-modernized-dns-dagger-workspace` owns consumer pins, workspace configuration, and acceptance. Global mise/chezmoi adoption requires its own authorized host-scoped work. Provider upgrades, production state handoff, Cloudflare canary deployment, Dagger Cloud activation, and migration of other Actions templates are excluded.
