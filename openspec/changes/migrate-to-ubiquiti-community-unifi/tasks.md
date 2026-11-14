## 1. Prerequisites and Compatibility Discovery

- [ ] 1.1 Record accepted hardening/normalized-provider evidence, repaired offline baseline, and execution-foundation runtime tuple; verify the existing consumer baseline has a secret-safe zero-drift plan under qualified read behavior
- [ ] 1.2 Pin and inspect exactly `ubiquiti-community/unifi` 0.65.0 schema and source for auth, `unifi_client`, IP attributes, DNS schema, import/site resolution, and Read calling `CreateClient` on missing clients; retain version-qualified evidence
- [ ] 1.3 Deliver a secret-free mapping table for every current resource, data source, attribute, output, and import identity and verify complete coverage against inventory
- [ ] 1.4 Qualify active/offline/null/stale `last_ip` in fixtures and separately authorized guarded production evidence, avoiding unsafe discovery imports; verify all production IPs are usable and match intended legacy semantics before removal
- [ ] 1.5 Record observed positive and zero/default DNS TTLs; verify exact-provider round trips for duration and null/omission mappings without blindly using `0s`
- [ ] 1.6 Implement controller/site/existing-object preflight guards and verify missing-client, wrong-site, and uncertain-inventory failures stop before import/refresh effects; document residual race and authorization boundaries

## 2. Community Provider Module Conversion

- [ ] 2.1 Replace provider requirements in glue and unifi-dns with `ubiquiti-community/unifi = 0.65.0` and verify init/schema resolution matches the reviewed exact release
- [ ] 2.2 Preserve primary API-key and compatibility username/password configuration through runtime secret channels and verify auth wiring tests and disclosure scans
- [ ] 2.3 Replace legacy users/data reads with normalized `unifi_client` resources using `allow_existing = true` and `skip_forget_on_destroy = true`; verify static keys and guarded existing-client adoption tests
- [ ] 2.4 Derive A-record IPs from qualified `last_ip` and verify strict-mode missing/null/stale diagnostics and active/offline regression tests
- [ ] 2.5 Convert A/CNAME `type`/`record` to `record_type`/`value` with qualified duration/null TTLs and verify record-semantic fixtures
- [ ] 2.6 Update outputs, README examples, migration documentation, changelog, and references; verify examples match exact provider, site guards, and read-side-effect limits
- [ ] 2.7 Add and pass offline tests for schema mapping, MAC normalization, static resource keys, IP derivation, DNS values, TTL, API-key auth wiring, and username/password compatibility

## 3. State Handoff Tooling

- [ ] 3.1 Add a qualified non-mutating inventory path for UniFi addresses/MACs/sites/IDs and reviewed Cloudflare identity/functional projections; verify it prints no raw state, plans, or credentials
- [ ] 3.2 Generate a secret-free import manifest and verify allowlist tests reject Cloudflare, unrelated, duplicate, and incomplete targets
- [ ] 3.3 Add guarded remove/import orchestration for client MACs and DNS `site:id`; verify maintenance writer exclusion, actual per-command locking, generation preconditions, phase receipts, and no production destroy
- [ ] 3.4 Add encrypted exact checkpoints, checksum verification, guarded restoration, interruption detection, and single-owner assertions; verify uncertain effects/newer generations block blind retry or rollback
- [ ] 3.5 Add dry-run/fixture tests for missing, duplicate, malformed, partial, and unexpected entries, external writers, lock gaps, wrong sites, and functional-vs-serialization differences; verify failure-closed behavior and document recovery

## 4. solomonhd.ai Migration Rehearsal

- [ ] 4.1 Under separate sandbox authorization, create a run-specific production-scale legacy A/CNAME set below `unifi-poc-<run>.solomonhd.ai` and isolated test client where supported; verify exact run-owned inventory
- [ ] 4.2 Validate the legacy fixture, protected checkpoint, and secret-free manifest and verify checkpoint identity/checksum
- [ ] 4.3 Execute the exact guarded remove/import handoff into the community-provider fixture and require a zero-change plan
- [ ] 4.4 Update one benign sandbox record through the community provider and verify the API-visible value
- [ ] 4.5 Destroy only the sandbox resources through the community provider and verify every run-prefixed record and removable test client is absent
- [ ] 4.6 Inject failures at each handoff phase and prove rollback restores legacy ownership without remote deletion
- [ ] 4.7 Qualify missing-client Read/creation and site mismatch only in fixtures or explicitly authorized isolated sandbox cases; verify remote effects are detected and not falsely reported as state-only rollback
- [ ] 4.8 Verify cleanup distinguishes removable sandbox clients from deliberately retained remembered clients and retain a sanitized cleanup receipt with no unexplained residual resources

## 5. Production Ownership Handoff

- [ ] 5.1 Present rediscovered production targets, intended ownership-only effect, and import/refresh mutation risk; record separate operator authorization before state or potentially mutating provider operations
- [ ] 5.2 Establish serialized maintenance ownership/writer exclusion and record encrypted checkpoint, version/checksum, counts, and Cloudflare functional projections; verify per-command lock and generation fencing evidence
- [ ] 5.3 Generate the production manifest twice, reconcile it with provider/API inventory, and require the expected client/DNS counts with zero unrelated addresses
- [ ] 5.4 Recheck controller/site/object identity, remove only allowlisted legacy UniFi bindings, and import under target addresses; verify each phase receipt and authoritative resulting generation
- [ ] 5.5 Compare pre/post Cloudflare addresses, IDs, provider ownership, and reviewed functional fields; verify no functional drift while recording explained metadata/serialization differences without raw byte-equality requirements
- [ ] 5.6 Run the full consumer Dagger plan and require UniFi 0 add/0 change/0 destroy and Cloudflare 0 add/0 change/0 destroy
- [ ] 5.7 On failed invariants, retain maintenance ownership, prove prior operation termination and reconcile state/remote effects; verify guarded checkpoint restoration and legacy zero drift only when safe, otherwise record explicit operator repair handover without claiming automatic remote rollback

## 6. Feature and Consumer Acceptance

- [ ] 6.1 Run Terraform formatting/validation, Python tests, KCL schema/generator tests, Dagger tests, integration rehearsal, and secret-disclosure scans
- [ ] 6.2 Coordinate matched immutable Dagger/KCL feature pins with consumer change `adopt-modernized-dns-dagger-workspace` and verify qualified feature acceptance before merge, separately from later production-pin promotion
- [ ] 6.3 Verify separately authorized downstream production zero drift from the accepted published pin under qualified read behavior and retain sanitized migration evidence; record this gate separately from pre-merge feature acceptance
- [ ] 6.5 Run `openspec validate migrate-to-ubiquiti-community-unifi --strict` and `git diff --check`

## Closeout

- After qualified feature acceptance, separately review commit/push/merge/release, publish the reviewed provider revision, and coordinate the atomic matched downstream Dagger/KCL production-pin update. Re-run acceptance in 6.3; do not count publication itself as implementation completion.
- After publication and consumer acceptance, update the Portainer `rotate-high-risk-credentials` dependency to unblock the two MCP sidecar account break-outs while keeping UniFi API-key rotation out of scope (remaining lifecycle work from former 6.4).
- Retain sanitized migration evidence; specification sync and OpenSpec archive require separate closeout review. Do not archive the completed normalized-provider baseline here.
