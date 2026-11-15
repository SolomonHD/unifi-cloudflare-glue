## Context

See `proposal.md` for motivation. The repository is clean `main` at `6d87ec0`; `dagger.json` declares v0.19.8 and the consuming repository declares v0.20.8. `src/main/main.py` has 4,196 lines and duplicates generation, backend setup, live execution and cleanup. Inspection found discarded initialized container snapshots in integration cleanup, failure strings returned as successful calls, incorrect plan action parsing, and a persistent-local-state promise not implemented by Directory input copies.

The existing cache and plan specs contain contradictory historical instructions, including removed no-cache flags, source-wide cache busting, separate versus combined roots, and default raw-plan exports. Security requirements from the hardening baseline take precedence as invariants; this change must explicitly replace conflicting legacy requirements, not leave a second contradictory execution contract. The existing legacy-test change owns current-interface repair, not this redesign's new behavior.

Strict change validation also reports pre-existing structural archive blockers in the main `cache-control`, `config-generation`, and `orchestration` specs: delta headers appear outside a canonical main `## Requirements` section. Planning validation success is not archive readiness. Repair and review those structures without dropping unaffected behavior during the future authorized spec-reconciliation work; do not edit main specs or archives in this proposal run.

Upstream evidence checked on 2026-11-14: [latest stable v0.21.11](https://github.com/dagger/dagger/releases/tag/v0.21.11), [1.0 beta compatibility announcement](https://dagger.io/blog/dagger-10-beta/), and [v0.21.0 release/locking changes](https://github.com/dagger/dagger/releases/tag/v0.21.0). Website examples can describe beta-only behavior; release qualification, not a marketing page, determines accepted syntax and APIs.

## Goals / Non-Goals

**Goals:** Qualify current Dagger techniques before choosing the implementation target; keep a reusable Python module; preserve KCL semantics and remote-state/resource identity; separate pure and effectful stages; produce testable failure, freshness and recovery contracts.

**Non-Goals:** Change Terraform to OpenTofu, rewrite Python in Dang, upgrade providers, move production state, deploy Compose services, enable Dagger Cloud, or build a generalized pipeline framework. Full saved-plan promotion is not introduced here: preview plans remain previews and execution explicitly replans.

## Decisions

### 1. Qualify 1.0 first; do not upgrade production first

The primary qualification candidate is Dagger v1.0.0-beta.27 for the CLI and engine; resolve and record the compatible exact Python SDK identity rather than assuming its package version matches the CLI. The first implementation stage verifies release assets, CLI/engine/Python SDK agreement, manifest migration, dependency loading from another repository, and cache/Secret APIs. Use isolated local test inputs and no production credentials. Capture the selected release tuple and reproducible qualification evidence. Do not guess beta syntax from v0.21 examples or assume `dagger.toml`, `dagger-module.toml`, and lock paths across release tracks. Do not replace this candidate with a moving latest/beta label.

On 2026-11-14, workstation SOL-3D-MIDSEASON (account solomong) installed the candidate through the [official installer](https://docs.dagger.io/getting-started/install/) at `/home/solomong/.local/opt/dagger/1.0.0-beta.27/bin/dagger`, with the installer's SHA-256 archive check. Its version output reports v1.0.0-beta.27, commit `400b82d6`, linux/amd64, and engine reference `registry.dagger.io/engine:v1.0.0-beta.27`. The fallback CLI v0.21.11 is installed through `aqua:dagger/dagger` and can be invoked with `mise exec aqua:dagger/dagger@0.21.11 -- dagger`. The active mise selection remains v0.20.5. These observations establish CLI installation/version checks only, not engine execution, SDK compatibility, manifest migration, project tests or consumer acceptance. Invoke the beta by its explicit path and the fallback by its exact mise version; preserve global selection. Retain full immutable release identities during qualification; the displayed short commit and engine tag alone are not that receipt.

If beta qualification fails, retain its evidence and stop target-dependent implementation until a deliberate v0.21.11 fallback is recorded and accepted. Do not silently switch tracks. The stable track keeps only supported APIs/manifests. Keep host-global mise declarations unchanged; the consumer coordinates external host/toolchain ownership separately.

Alternative rejected: complete a stable-only redesign before evaluating beta, which risks doing the manifest/interface work twice.

### 2. One deterministic generation boundary

Build a pinned tooling environment and execute the KCL entry point once to produce both output objects. Qualify the pinned KCL release's native JSON output and dependency-resolution command using fixtures. Prefer native JSON and direct Dagger file operations; if a parser remains necessary, pin it and keep it internal. Do not run dependency updates as part of normal verification. Preserve committed KCL and provider lock semantics and deliberate update procedures; Dagger locks complement rather than replace ecosystem locks.

Both public generation paths select from the same result and preserve current JSON contracts, normalization, site propagation, service filtering and DNS-loop validation. Invalid source/missing keys/empty output fail structurally, not by searching stdout for the word VALIDATION. Use Changesets only for explicitly requested, non-sensitive checkout output; ephemeral Terraform inputs remain typed Files/Directories.

#### Scoped split-DNS origin policy

The approved revision replaces blanket same-zone rejection with default rejection plus exact opt-in declarations. Public-zone membership is a conservative validation signal, not proof that the connector's resolver will loop. Split-horizon DNS can resolve a public-zone name internally. An exception expresses operator intent only; it performs no DNS lookup or verification.

Define `cloudflare.SplitDNSOrigin` as a typed record with `protocol: "http" | "https" | "tcp"`, `hostname: str` and `port: int` in 1..65535. Add `CloudflareConfig.split_dns_origins: [SplitDNSOrigin] = []`. `generate_cloudflare_from_entities`, `transform_service` and `transform_tunnel_services` accept the same typed list as an optional trailing `split_dns_origins` argument defaulting to empty; explicit tunnel-service validation receives the configuration policy. Existing callers without declarations retain default same-zone apex/subdomain rejection.

Match only the exact lowercase URL scheme, DNS hostname (case-insensitive, normalizing one terminal root dot) and effective port. HTTP and HTTPS default to 80 and 443; TCP requires an explicit URL port. Paths, queries and fragments do not affect origin identity. A declaration hostname must be a concrete DNS name, not a URL, wildcard, IP address or address range. Invalid declarations fail closed even if unused. Userinfo and ambiguous authorities cannot qualify. Do not introduce suffix wildcards, subdomain inheritance or a global bypass, and do not let one protocol/port authorize another.

The policy applies consistently to explicit services, entity-derived services, internal hostname overrides, resolved fallbacks and direct transform helpers. It does not rewrite output URLs or alter service ordering, TLS/path metadata, Terraform input shapes or provider/resource addresses. Do not emit the policy into Terraform JSON. Offline fixtures must cover default rejection, exact acceptance, normalized equivalents, nonmatching tuples, invalid declarations, unsafe authorities and output preservation through real supported entry points. Existing archived strict-blanket language remains historical, not the current policy.

The required consumer example is `cloudflare.SplitDNSOrigin {protocol = "https", hostname = "traefik-mid.sghd.io", port = 443}` for an already-intended HTTPS origin. It changes validation policy, not routing. No consumer repository is edited under this revision. Separately authorized live acceptance must prove that the connector resolves this origin internally and reaches it without a Cloudflare loop.

### 3. Automatic freshness at the effect boundary

Mark live orchestration uncached under the qualified SDK, then introduce a unique non-secret invocation identity into the live container execution graph. Function-level cache control alone cannot prevent underlying exec cache reuse. Keep tool setup and deterministic generation above that boundary. Refresh backend initialization when its cached metadata or credentials would otherwise be stale; initialization that contacts a backend is not assumed pure.

Every fresh verification after an effect has a fresh identity and ordering dependency on that effect. Remove caller timestamps, output-timestamp cache claims and shell-comment injection as correctness mechanisms. A retained manual run label is metadata only, with bounded validation and no shell interpolation. Test identical calls twice and verify both effect dispatches and reused deterministic stages.

### 4. Shared preparation, same root, truthful results

Factor only repeated orchestration into focused helpers: scope/root selection, generation, backend/credential binding, execution, and bounded result extraction. Plan, apply and destroy use the same root, resource address layout and backend for the selected mode. Preserve current production combined-root addresses; never make a root/address move incidental to the refactor. Explicitly select standalone roots only for already independently managed standalone state.

Preserve the post-exec container on every init/plan/apply/destroy path. Use native argv, output redirection, completion and expected-exit APIs where qualified. Sanitize exceptions at their source and preserve phase/exit status. Partial success and cleanup failure are distinct outcomes; a failure cannot become successful CLI output merely because a string was returned.

Parse Terraform action arrays as strings. Replacement counts contribute create and delete, with separate replacement metadata if exposed. Test create/update/delete/replacement/no-op and malformed data. Default artifacts contain a bounded summary and reviewed human-readable plan; raw JSON/binary plans remain opt-in and protected. A preview must disclose that deploy replans, not falsely claim approval of the exact executed plan.

### 5. Secret input migration and explicit state recovery

Provider credentials remain Secret environment variables. Change backend ingestion to a Secret input with explicit YAML/HCL format selection; do any necessary transformation inside a non-logged secret-aware path and mount the result owner-only. Avoid exposing plaintext through Python File reads, ordinary files, exec arguments or returned values. Use a robust constrained serializer/parser with synthetic escaping failures rather than silently interpreting malformed YAML as HCL. Consumer callers must migrate explicitly; there is no automatic secret-to-plain fallback.

Remote backend acceptance preserves bucket/address, key, workspace, locking and state lineage. Backend/config failure stops before mutation instead of selecting ephemeral state. On 2026-11-14 the operator explicitly chose remote-only public effects: deploy/destroy reject local-state inputs and missing remote-backend selection before generation, initialization or effects. Read-only local previews may consume protected input but promise neither host write-back nor updated effectful state. Durable local-state handoff is moved to separately tracked follow-up DLR-1 below; it is not implemented or waived as completed by this change. Ephemeral state remains appropriate only for the separately explicit disposable integration lifecycle with cleanup/recovery evidence, not general deployment.

Newly generated tunnel credentials need secret-oriented output/explicit disclosure, not ordinary default reports. A raw plan/state is sensitive regardless of whether provider credentials were supplied via environment variables. Scan normal and failure output with synthetic canaries, including returned exceptions, traces and default artifacts.

### 6. Test ownership and downstream branches

`modernize-legacy-unit-test-contracts` first makes existing tests honest about the current interface. Beta qualification can run alongside it, but the refactor waits for baseline evidence. This change adds behavioral execution-graph, failure, freshness, state recovery, secret and consumer contract tests as behavior changes; it does not defer those tests to a later cleanup.

The accepted foundation then independently unblocks `add-cloudflare-live-ci-canary` (Dagger lifecycle, thin Actions runner) and `migrate-to-ubiquiti-community-unifi` (provider/state qualification). Neither branch is a prerequisite of the other. `portainer-docker-compose` change `adopt-modernized-dns-dagger-workspace` first accepts modernization with the existing provider and later accepts the provider-bearing revision only after its handoff gates. Published Dagger and KCL revisions must match; source pointers are not runtime acceptance.

Expose the early runtime-qualification/candidate-contract receipt before final acceptance so the consumer can start its feature checks. Module tasks 6.2-6.3 and consumer feature checks produce shared final evidence; neither repository requires the other's entire change to be complete before beginning those checks. A modernization-only consumer delivery can finish independently of later provider-bearing adoption, whose explicit follow-up retains its own handoff and repeated acceptance gates.

Candidate `38daa8a8131080659acb5e4d59e4a2135eb7d92f` was blocked by the strict same-zone guard and remains superseded. The 2026-11-15 downstream handoff records technical acceptance of revised published SHA `614c6aea5e2c92417e4e7d08882ccdcb4113eb33` against a fingerprinted consumer working tree, with matched remote module/KCL resolution, connector-private connectivity and a fresh zero-drift preview. The sole separately approved backend setting change was enabling `use_lockfile: true`; backend/state identity, credentials and other fields were preserved, so this is not a claim of byte-identical configuration. Upstream tasks 6.2/6.3 can complete on this bounded technical evidence. Consumer task 4.3, uncommitted source/base/custody reconciliation and separately authorized promotion remain outstanding. This reconciliation authorizes no new live operation, publication or routing change.

## Risks / Trade-offs

- Beta CLI/schema drift: exact release qualification and a recorded hold/fallback decision before dependent refactoring.
- Cached live effects: repeat-call behavioral evidence for function and exec boundaries, including fresh post-effect reads.
- State loss after a failed apply: require a remote backend for public effects, preserve inspectable execution snapshots and non-secret recovery identity, and keep unknown effects unresolved until backend reconciliation.
- Incorrect partial-scope root: assert root/backend/address equality and stop before applying to another state.
- Security regressions during simplification: use sentinel credentials through real success/failure/timeout/cleanup paths; never rely only on source-substring assertions.
- Backend format conversion changes: synthetic YAML/HCL equivalence and escaping tests, plus authorized same-backend zero-drift acceptance.
- Existing stale tests/specs: inventory exact obsolete clauses and transfer behavior into these deltas; do not restore removed deployment APIs or weaken cleanup assertions.

## Migration Plan

1. Qualify the exact runtime and finish the current-contract offline baseline.
2. Refactor with current providers and unchanged resource addresses; prove deterministic output equivalence and new failure/freshness/security contracts.
3. Publish a feature revision only under separate Git authorization, then qualify remote dependency consumption and matching KCL inputs in the sibling consumer.
4. With explicit production-read authorization, obtain a fresh zero-drift plan using unchanged remote backend and provider identity. Any unexpected delta stops adoption; no apply is authorized by this plan.
5. Preserve original pins and accepted runtime tuple for rollback. Restore code/tool selection only when state schema/identity is unchanged; a future provider rollback has its own migration procedure.

## Follow-up DLR-1: Durable Local State Custody

Status: deferred by explicit operator decision on 2026-11-14, not implemented
or accepted. This follow-up is distinct from the current implementation task
count. Public local-state effects remain rejected until its acceptance passes.

- Define an explicitly authorized, owner-only durable custody destination and
  operation identity before any local-state provider effect.
- Preserve the selected Terraform root/sibling layout and updated state after
  successful or partial apply/destroy; never model Directory input as host
  write-through or cache retention alone as durable handoff.
- Prove a second invocation consumes the handed-off state with unchanged
  backend/resource identity and no raw-state disclosure.
- Inject cancellation, disconnect, failed handoff and partial cleanup; preserve
  unknown installation/custody/effect identity and block replay until reconciled.
- Review the destination, privileges, retention, encryption and recovery API
  before implementation. No destination or new service is provisioned here.

## Closeout

Implementation/acceptance tasks must be complete before routine merge, tagging, consumer promotion, spec sync and archive. Those lifecycle steps require their normal authorization and are not checked implementation tasks. The completed `normalize-current-unifi-provider-baseline` can undergo its separate archive review; no archive is performed by this proposal. Record accepted full revisions and runtime evidence before promotion.

The downstream subsequently completed task 4.3 and archived all 12 tasks before
consumer publication. Its implementation and external backend-template edit are
still separately owned and uncommitted. User-authorized upstream closeout found
and fixed literal-IP declaration rejection, published as
`e8777e968f83fb7b8de82ccbd245b7f918ca20fa`, with 613/613 upstream tests and
21 renewed exact-SHA remote consumer checks in an isolated public-input fixture.
The operator explicitly accepted bounded reuse of the earlier live evidence only
for unchanged execution inputs; no new live preview is claimed for the guard
fix. The runtime receipt retains the proof, limits and decision. Preserve the
real consumer's accepted `614c6aea...` source at `accepted/dagger-614c6ae` through
squash; do not infer consumer repinning or production authority. Unrelated active
canary work remains untouched in the retained primary checkout. Upstream archive
and squash/merge are authorized with no release/tag.
