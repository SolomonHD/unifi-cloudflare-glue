## Context

The production state currently binds approximately 5 `filipowm/unifi` managed clients, 5 client reads, and 57 UniFi DNS records alongside Cloudflare resources. The target `ubiquiti-community/unifi` v0.55.x provider supports API keys but is not state-schema compatible by provider address alone:

| Current | Target |
|---|---|
| `filipowm/unifi` v1.1.x | `ubiquiti-community/unifi` v0.55.x |
| `unifi_user` | `unifi_client` |
| `data.unifi_user.ip` | `unifi_client.last_ip` |
| `unifi_dns_record.type` | `unifi_dns_record.record_type` |
| `unifi_dns_record.record` | `unifi_dns_record.value` |
| numeric/default TTL representation | Go-duration TTL such as `300s` |

The community provider can import DNS records by `id` or `site:id` and clients by MAC address. Because the provider source, resource type, and schemas change, `terraform state replace-provider` alone is insufficient. Deleting production records merely to simplify state is unacceptable.

## Goals / Non-Goals

**Goals:**

- Migrate module configuration and production state ownership to `ubiquiti-community/unifi` v0.55.x.
- Preserve API-key authentication, Network 10.x client adoption, MAC normalization, DNS names/values, and strict-mode behavior.
- Rehearse the exact state handoff on disposable resources before touching production state.
- Leave every Cloudflare state entry and remote resource byte-for-byte outside the migration scope.
- Produce a deterministic, secret-free import manifest and rollback checkpoint.

**Non-Goals:**

- Destroy or recreate production UniFi DNS records or clients.
- Rotate the UniFi API key or the two MCP sidecar accounts.
- Change KCL service/domain semantics or Cloudflare resources.
- Use `solomonhd.ai` sandbox results as a substitute for the final production zero-drift plan.

## Decisions

### 1. Use explicit remove-and-import instead of provider-address replacement

The migration removes only legacy UniFi resource bindings from state and imports the same remote objects under community-provider resource addresses. Data-source state is disposable and refreshes from configuration. `terraform state replace-provider` is not used because it cannot translate `unifi_user` to `unifi_client` or rename DNS attributes.

Alternative considered: targeted destroy followed by apply. Rejected because it creates DNS downtime and turns a provider/schema defect into a production outage.

### 2. Read current client IP from the managed community client

Each normalized MAC maps to `unifi_client.device` with `allow_existing = true` and `skip_forget_on_destroy = true`. DNS A-record values use the resource's read-only `last_ip`; static `for_each` keys allow Terraform to defer the value until apply. Strict mode continues to report MACs for which no usable current/last IP exists.

Alternative considered: replace the legacy data source with active-only `unifi_client_info`. Rejected as the sole source because inactive but remembered clients may not appear in the active-client surface. The sandbox and production plan must confirm `last_ip` behavior before migration proceeds.

### 3. Preserve logical DNS addresses while re-importing physical IDs

The Terraform logical keys for A and CNAME maps remain stable. Their HCL schema changes to `record_type` and `value`, and explicit TTL values use duration syntax. The manifest maps each logical address to its observed site and remote ID, permitting import into the same logical address after its old binding is removed.

### 4. Rehearse the actual handoff, not two independent CRUD tests

The normalized legacy provider creates a unique `unifi-poc-<run>.solomonhd.ai` record set and an isolated test client where supported. The same state handoff procedure then removes legacy bindings, imports the live objects through the community provider, requires zero drift, performs one benign update, and destroys/verifies the sandbox with the community provider.

### 5. Treat the production state snapshot and manifest as sensitive operational data

The full state snapshot is encrypted and access-restricted because Terraform state can contain secrets. The generated migration manifest contains only resource addresses, normalized MACs, sites, and remote IDs; it is scanned before being retained. Backend version identity/checksum is recorded so rollback targets the exact pre-handoff generation.

### 6. Gate every state phase on invariants

Before handoff, the manifest must account for all expected UniFi managed resources and no Cloudflare addresses. After import, the plan must show 0 add, 0 change, and 0 destroy for both components. Any mismatch stops before apply. No production `terraform apply` is needed merely to complete an import-only ownership migration.

## Risks / Trade-offs

- [Community `last_ip` differs from legacy lookup behavior] → Prove it with fixture and production refresh before any state removal; stop if any value is null or different.
- [Import ID or address generation is wrong] → Generate and validate the manifest twice from state and provider API inventory, then rehearse the same tooling in the sandbox.
- [Two states temporarily claim an object] → Use one locked backend handoff transaction and do not leave parallel persistent states.
- [State commands accidentally include Cloudflare] → Enforce an address allowlist and compare Cloudflare state fingerprints before and after.
- [Import refresh proposes defaults] → Normalize HCL values and require a zero-drift plan; do not apply to silence unexplained changes.
- [Rollback after remote mutation is complex] → Permit no production mutation until import is complete and zero drift is established.

## Migration Plan

1. Confirm both prerequisite changes are merged, consumed, and verified.
2. Implement the community provider/resource mapping and offline tests on a feature branch.
3. Run the complete legacy-to-community sandbox handoff below `solomonhd.ai`; verify cleanup.
4. Acquire the production backend lock and capture an encrypted snapshot, backend version/checksum, state inventory, and secret-free import manifest.
5. Validate expected counts and prove the manifest contains only UniFi addresses.
6. Remove the legacy UniFi managed-resource bindings from state; allow obsolete data-source entries to refresh away.
7. Initialize the community provider and import clients by MAC plus DNS records by `site:id` into their target logical addresses.
8. Compare state inventories and Cloudflare fingerprints, then run the full Dagger plan.
9. Proceed only if UniFi and Cloudflare both show 0 add, 0 change, and 0 destroy.
10. Publish the provider-migration revision, update the consumer pin, and repeat the read-only plan from the consumer.

If any step before remote mutation fails, restore the exact pre-handoff backend version/checksum and repin the normalized legacy revision. Because the production procedure performs state operations and read-only plans only, rollback must not require remote DNS changes.

## Open Questions

- Confirm the controller returns stable `last_ip` for every production client, including any currently offline device, during implementation discovery.
- Confirm whether v0.55.x import refresh applies an explicit default TTL; if so, select the observed duration in HCL rather than accepting unexplained drift.
