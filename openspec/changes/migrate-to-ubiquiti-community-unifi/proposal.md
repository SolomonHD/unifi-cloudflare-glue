## Why

The normalized `filipowm/unifi` baseline is functional, but `ubiquiti-community/unifi` is the intended long-term provider and has different client, DNS, and state schemas. A rehearsed import-based ownership handoff is needed to move providers without deleting production UniFi DNS records or disturbing the Cloudflare resources stored in the same Terraform state.

## What Changes

- Depend on completion of `harden-dagger-secret-and-state-handling` and `normalize-current-unifi-provider-baseline`.
- **BREAKING**: Replace `filipowm/unifi` with `ubiquiti-community/unifi` v0.55.x in the root and UniFi DNS modules.
- **BREAKING**: Replace `unifi_user` resources/data sources with the community provider's `unifi_client`/client-information model and map current-IP behavior without losing the Network 10.x workaround.
- **BREAKING**: Convert UniFi DNS fields from `type`/`record` to `record_type`/`value` and normalize TTL values to duration syntax.
- Rehearse the exact legacy-create → state handoff/import → community zero-drift/update/destroy sequence on disposable `solomonhd.ai` resources.
- Generate a production migration manifest from the existing state: client MAC imports and DNS `site:id` imports, with no credential values.
- Transfer production ownership using state removal and import/adoption; never run production `terraform destroy` as a migration mechanism.
- Require zero-drift UniFi and Cloudflare plans after import before allowing any production apply.
- Retain API-key authentication as the primary path and inexpensive username/password compatibility.

## Capabilities

### New Capabilities
- `unifi-provider-migration`: Defines provider/schema mapping, sandbox rehearsal, production import handoff, rollback, and zero-drift gates.

### Modified Capabilities
- `provider-upgrade`: Extends provider upgrade behavior to a source-address migration with explicit schema and state compatibility checks.
- `terraform-modules`: Changes the UniFi module's required provider and resource/data-source model while preserving generated DNS behavior.
- `state-management`: Adds secure state snapshot, manifest, removal, import, validation, and rollback requirements for cross-provider ownership transfer.

## Impact

- Affects UniFi Terraform provider constraints, provider configuration, client resources/data sources, DNS resources, outputs, module documentation, tests, Dagger fixtures, and release notes.
- Production scope includes approximately 5 managed clients, 5 client reads, and 57 UniFi DNS records; Cloudflare state entries must remain untouched.
- The production migration changes Terraform ownership metadata but MUST make no remote DNS or client changes when desired and observed values already match.
- Requires an authorized maintenance window for state operations and real read-only plans; no production deploy is permitted until the post-import plan is zero drift.
- Unlocks the deferred Portainer `rotate-high-risk-credentials` UniFi account break-out after the community-provider revision is published and consumed.
