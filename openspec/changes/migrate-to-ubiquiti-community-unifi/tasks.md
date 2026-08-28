## 1. Prerequisites and Compatibility Discovery

- [ ] 1.1 Confirm both prerequisite changes are complete, published, consumed, and producing a secret-safe zero-drift production plan
- [ ] 1.2 Pin and inspect `ubiquiti-community/unifi` v0.55.x provider schemas for provider auth, `unifi_client`, client IP attributes, `unifi_dns_record`, and supported import identities
- [ ] 1.3 Capture a secret-free mapping table for every current managed resource, data source, attribute, output, and import identity
- [ ] 1.4 Verify `last_ip` is stable and non-null for every production client, including offline clients, without modifying state or remote resources
- [ ] 1.5 Determine the observed DNS TTL/default values that must be represented as community-provider duration strings

## 2. Community Provider Module Conversion

- [ ] 2.1 Replace `filipowm/unifi` with `ubiquiti-community/unifi ~> 0.55.0` in the glue and unifi-dns provider requirements
- [ ] 2.2 Preserve API-key provider configuration as primary and username/password configuration as compatibility using secret environment channels
- [ ] 2.3 Replace `unifi_user` and its data reads with `unifi_client` resources using normalized MACs, `allow_existing = true`, and `skip_forget_on_destroy = true`
- [ ] 2.4 Derive A-record IP values from the validated community-client `last_ip` behavior and preserve strict-mode missing-IP diagnostics
- [ ] 2.5 Convert A/CNAME DNS resources from `type`/`record` to `record_type`/`value` and add observed duration-form TTL values
- [ ] 2.6 Update outputs, README examples, migration documentation, changelog, and provider references
- [ ] 2.7 Add offline tests for schema mapping, MAC normalization, static resource keys, IP derivation, DNS values, TTL, API-key auth wiring, and username/password compatibility

## 3. State Handoff Tooling

- [ ] 3.1 Add a read-only inventory command that extracts expected UniFi managed addresses, normalized MACs, sites, DNS IDs, and Cloudflare fingerprints without printing state or credentials
- [ ] 3.2 Generate and validate a secret-free import manifest with an allowlist that rejects Cloudflare or unrelated addresses
- [ ] 3.3 Add guarded state-removal/import orchestration for clients by MAC and DNS records by `site:id`, with backend locking and no `terraform destroy`
- [ ] 3.4 Add exact checkpoint metadata, checksum verification, rollback restoration, interrupted-run detection, and single-owner assertions
- [ ] 3.5 Add dry-run and fixture tests for missing, duplicate, malformed, partially imported, and unexpected state entries

## 4. solomonhd.ai Migration Rehearsal

- [ ] 4.1 Use the normalized legacy provider to create an authorized run-specific, production-scale A/CNAME set under `unifi-poc-<run>.solomonhd.ai` plus an isolated test client where supported
- [ ] 4.2 Validate the legacy fixture and capture its protected state checkpoint and secret-free manifest
- [ ] 4.3 Execute the exact guarded remove/import handoff into the community-provider fixture and require a zero-change plan
- [ ] 4.4 Update one benign sandbox record through the community provider and verify the API-visible value
- [ ] 4.5 Destroy only the sandbox resources through the community provider and verify every run-prefixed record and removable test client is absent
- [ ] 4.6 Inject failures at each handoff phase and prove rollback restores legacy ownership without remote deletion

## 5. Production Ownership Handoff

- [ ] 5.1 Present the exact production state targets and expected state-only effect, then obtain explicit operator authorization before any state mutation
- [ ] 5.2 Acquire the backend lock and record an encrypted pre-handoff state snapshot, backend version identity, checksum, resource counts, and Cloudflare fingerprints
- [ ] 5.3 Generate the production manifest twice, reconcile it with provider/API inventory, and require the expected client/DNS counts with zero unrelated addresses
- [ ] 5.4 Remove only the allowlisted legacy UniFi managed-resource bindings and import clients/DNS records under the community-provider addresses
- [ ] 5.5 Compare pre/post inventories and require identical Cloudflare addresses, IDs, and fingerprints
- [ ] 5.6 Run the full consumer Dagger plan and require UniFi 0 add/0 change/0 destroy and Cloudflare 0 add/0 change/0 destroy
- [ ] 5.7 If any invariant fails, run the tested checkpoint rollback before releasing the lock and verify the normalized legacy revision returns to zero drift

## 6. Publication and Dependency Unlock

- [ ] 6.1 Run Terraform formatting/validation, Python tests, KCL schema/generator tests, Dagger tests, integration rehearsal, and secret-disclosure scans
- [ ] 6.2 Publish the reviewed community-provider revision and atomically update downstream Dagger/KCL pins
- [ ] 6.3 Re-run the downstream production read-only plan from the published pin and archive secret-free migration evidence
- [ ] 6.4 Update the Portainer credential-rotation task to unblock the two MCP sidecar account break-outs while keeping UniFi API-key rotation out of scope
- [ ] 6.5 Run `openspec validate migrate-to-ubiquiti-community-unifi --strict` and `git diff --check`
