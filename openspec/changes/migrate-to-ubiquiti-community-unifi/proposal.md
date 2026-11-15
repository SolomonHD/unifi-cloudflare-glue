## Why

The normalized `filipowm/unifi` baseline is functional, but `ubiquiti-community/unifi` is the intended long-term provider and has different client, DNS, and state schemas. A rehearsed import-based ownership handoff is needed to move providers without deleting production UniFi DNS records or disturbing the Cloudflare resources stored in the same Terraform state.

## What Changes

- Build on existing hardening and normalized-provider evidence, the repaired `modernize-legacy-unit-test-contracts` baseline, and accepted `modernize-dagger-execution-contracts` foundation; remain independent of the Cloudflare CI canary.
- **BREAKING**: Qualify and pin `ubiquiti-community/unifi` exactly `0.65.0` in the root/glue and UniFi DNS modules, replacing `filipowm/unifi` only after compatibility acceptance.
- **BREAKING**: Replace `unifi_user` resources/data sources with the community provider's `unifi_client`/client-information model and map current-IP behavior without losing the Network 10.x workaround.
- **BREAKING**: Convert UniFi DNS fields from `type`/`record` to `record_type`/`value`, preserving explicit duration TTLs and qualified zero/default-to-null semantics.
- Rehearse the exact legacy-create → state handoff/import → community zero-drift/update/destroy sequence on disposable `solomonhd.ai` resources.
- Generate a production migration manifest from the existing state: client MAC imports and DNS `site:id` imports, with no credential values.
- Transfer production ownership using state removal and import/adoption; never run production `terraform destroy` as a migration mechanism.
- Require zero-drift UniFi and Cloudflare plans after import before allowing any production apply.
- Retain API-key authentication as the primary path and inexpensive username/password compatibility.
- Treat import/refresh as potentially mutating: target-provider Read can call `CreateClient` for a missing client. Qualify existing-object, controller/site, offline `last_ip`, and missing-client guards before production execution.
- Serialize the maintenance handoff with per-command backend locks, writer exclusion, and state-generation fencing, not an invented continuous multi-CLI lock.

## Capabilities

### New Capabilities
- `unifi-provider-migration`: Defines provider/schema mapping, sandbox rehearsal, production import handoff, rollback, and zero-drift gates.

### Modified Capabilities
- `provider-upgrade`: Extends provider upgrade behavior to a source-address migration with explicit schema and state compatibility checks.
- `terraform-modules`: Changes the UniFi module's required provider and resource/data-source model while preserving generated DNS behavior.
- `state-management`: Adds secure state snapshot, manifest, removal, import, validation, and rollback requirements for cross-provider ownership transfer.

## Impact

- Affects UniFi Terraform provider constraints, provider configuration, client resources/data sources, DNS resources, outputs, module documentation, tests, Dagger fixtures, and release notes.
- Historical production scope is approximately 5 managed clients, 5 client reads, and 57 UniFi DNS records; rediscover exact targets at acceptance. Preserve Cloudflare resource identity and reviewed functional fields, not raw state bytes.
- The production migration changes Terraform ownership metadata but MUST make no remote DNS or client changes when desired and observed values already match.
- Requires separately authorized production acceptance covering state effects and qualified provider read/import risk; no apply or merge before qualified feature acceptance and post-import zero drift. A plan label alone is not a read-only guarantee.
- Downstream staged adoption is coordinated with `adopt-modernized-dns-dagger-workspace` in the consumer repository; adopting the execution-only foundation need not wait for this provider handoff.
- Unlocks the deferred Portainer `rotate-high-risk-credentials` UniFi account break-out after the community-provider revision is published and consumed.
