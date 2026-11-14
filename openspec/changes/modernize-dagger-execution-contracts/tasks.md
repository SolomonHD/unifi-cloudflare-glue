## 1. Qualify the Runtime First

- [ ] 1.1 Resolve one immutable Dagger 1.0 beta CLI/engine/Python SDK tuple from upstream releases and record provenance, exact versions and supported manifest/lock paths; verify isolated schema loading and basic Python execution without production credentials or global tool changes.
- [ ] 1.2 Qualify remote dependency loading from a separate consumer fixture, Secret input/output APIs, function caching and live-exec freshness on that tuple; verify repeated synthetic invocations and retain sanitized results. If blocked, stop dependent implementation until an explicitly accepted and tested v0.21.11 fallback is recorded.
- [ ] 1.3 Confirm `modernize-legacy-unit-test-contracts` has delivered its complete current-interface baseline before refactoring; verify the full collection and credential-free suite output, not merely the change's planning status. Qualification tasks 1.1-1.2 may run alongside that baseline.
- [ ] 1.4 Document the accepted compatibility matrix, breaking interfaces and consumer migration sequence; verify all examples use qualified release syntax and that stable-fallback instructions do not assume beta-only manifests.

## 2. Deterministic Tooling and Generation

- [ ] 2.1 Pin Terraform, KCL, required parser/tool images and Python dependencies with reviewed identities and ecosystem locks; verify clean frozen resolution and deliberate failure on missing pins without runtime latest downloads or automatic KCL updates.
- [ ] 2.2 Qualify native machine-readable KCL output and dependency-resolution behavior for the selected KCL release; implement a shared generation result for selected provider outputs and verify canonical equivalence against representative current UniFi and Cloudflare fixtures.
- [ ] 2.3 Replace unnecessary stdout-to-Python-to-file/yq round trips using qualified file APIs; verify real normalization, site, multi-NIC, distribution, DNS-loop, empty/missing-key/malformed-output and VALIDATION-string fixtures, plus selected-output-only generation.
- [ ] 2.4 Expose the baseline verification suite through the qualified credential-free Dagger entry point and explicit non-sensitive generation/export adapters; verify identical local/CI outcomes and no implicit checkout writes, raw state/plan inclusion or live canary execution. Document bootstrap versus offline execution requirements.

## 3. Fresh and Truthful Live Execution

- [ ] 3.1 Centralize scope/root/backend preparation without changing provider versions or existing resource addresses; verify full and selective plan/apply/destroy select matching roots and state identity, reject incompatible selections, and retain sibling module paths.
- [ ] 3.2 Implement qualified uncached orchestration and automatic non-secret freshness at live initialization/execution/verification boundaries; verify two identical synthetic calls dispatch live effects twice while deterministic generation remains reusable. Document replacement of manual cache-buster correctness requirements.
- [ ] 3.3 Remove command-string/comment cache injection and use direct argv/native redirection where supported; verify newline/metacharacter labels cannot execute commands and invalid labels fail before provider access.
- [ ] 3.4 Preserve post-init and post-effect container snapshots throughout integration and cleanup paths; verify execution-graph tests prove apply/destroy use successful initialization snapshots rather than discarded references.
- [ ] 3.5 Make failed/partial deployments, destruction and credential operations produce nonzero status with sanitized phase/exit/recovery information; verify injected failures do not become successful string results and do not dispatch dependent work.
- [ ] 3.6 Validate HTTP status, API success envelopes and response shape for live verification; verify transport/error/null responses fail closed rather than count as zero resources. Document that timeout/cancellation retains unknown effects until reconciliation, and test that no blind replay occurs.

## 4. Backend Secrets and State Custody

- [ ] 4.1 Introduce Secret-typed backend input with explicit YAML/HCL selection and an owner-only secret mount; verify backend address/key/workspace/locking equivalence on synthetic fixtures and rejection of malformed/empty input without plaintext File ingestion or local-state fallback.
- [ ] 4.2 Harden backend conversion with robust parsing/serialization of supported scalar/structure types; verify quote, backslash, newline, interpolation and invalid-key/type fixtures using a real HCL/config parser where applicable, retaining useful sanitized errors.
- [ ] 4.3 Implement explicit protected local-state output/recovery, retaining root layout and updated state after partial effects; verify a second invocation can consume the handed-off state and unsupported combinations fail before mutation. Document custody and recovery without describing Directory input as host write-through.
- [ ] 4.4 Keep supplied and newly generated credentials on protected channels with explicit disclosure boundaries; verify synthetic success, validation/provider error, timeout and cleanup error paths across logs, traces, exceptions, summaries and default artifacts contain no canary secrets.
- [ ] 4.5 Document and test uncertain-state recovery and authorization boundaries; verify an unknown custody/effect result preserves operation identity, blocks automatic retry and never suggests rolling state back as proof of remote rollback.

## 5. Plans and Durable Contracts

- [ ] 5.1 Correct structured action-array parsing and summary generation; verify create/update/delete/replacement/no-op fixtures and malformed data, plus resolved version and selected-scope metadata without transferring sensitive values into summaries.
- [ ] 5.2 Preserve reviewed text/summary defaults and explicit protected raw-plan opt-in; verify owner-only permissions and sentinel scans, and document that previews do not approve a later independently replanned apply.
- [ ] 5.3 Reconcile the exact legacy cache, plan, state and orchestration clauses with these deltas while preserving unaffected security and behavior scenarios; verify no supported guidance requires removed APIs, caller timestamps, default raw-plan exports or automatic Directory host write-back.
- [ ] 5.4 Repair the structural main-spec blockers in cache-control, config-generation and orchestration during the separately authorized implementation/spec-reconciliation scope, preserving active obligations and historical intent; verify strict main-spec validation and a non-writing archive/sync preflight no longer report invisible requirements or invalid delta headers. Do not archive as part of this task.

## 6. Cross-Repository Acceptance

- [ ] 6.1 Run the full offline suite, selected runtime/SDK schema checks, format/static checks and both provider generation contract suites; verify current provider constraints/lock selections and resource addresses remain unchanged.
- [ ] 6.2 Qualify the reviewed feature revision as a remote dependency with matching KCL source in the sibling consumer change; verify exact source identities, release tuple, Secret input invocation and deterministic output equivalence before merge or promotion.
- [ ] 6.3 With explicit authorization for production reads, verify a fresh zero-drift consumer plan against the unchanged Wasabi backend and existing providers; retain only sanitized identity/action-count evidence and confirm no apply was performed. Unexpected deltas block acceptance.
- [ ] 6.4 Record the accepted foundation contract and dependency evidence for the independent community-provider and thin-Actions canary branches; verify neither branch depends on the other's completion and downstream tasks reference the accepted runtime rather than a moving beta label.

## Workflow Follow-up

- Commit/push reviewed feature revisions only under explicit Git authorization, then review and merge only after required feature acceptance. Publishing a revision for acceptance does not itself authorize production mutation.
- Coordinate accepted module publication and consumer pins with `adopt-modernized-dns-dagger-workspace`; preserve the previous runtime/source tuple for rollback and never assume a provider-bearing revision can roll back state by repinning code alone.
- Review spec-sync/archive readiness after structural blockers and implementation acceptance are resolved. The completed baseline has its own archive review; no changes are archived by this proposal.
