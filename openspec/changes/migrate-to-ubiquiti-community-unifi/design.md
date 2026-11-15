## Context

The historical production inventory contains approximately 5 `filipowm/unifi` managed clients, 5 client reads, and 57 UniFi DNS records alongside Cloudflare resources; rediscover exact counts before acceptance. The exact qualification target is `ubiquiti-community/unifi` 0.65.0, not 0.55.x, and provider-address replacement alone cannot translate its schemas:

| Current | Target |
|---|---|
| `filipowm/unifi` v1.1.x | `ubiquiti-community/unifi` = 0.65.0 |
| `unifi_user` | `unifi_client` |
| `data.unifi_user.ip` | `unifi_client.last_ip` |
| `unifi_dns_record.type` | `unifi_dns_record.record_type` |
| `unifi_dns_record.record` | `unifi_dns_record.value` |
| positive numeric TTL | Qualified Go-duration TTL such as `300s` |
| zero/default TTL | Qualified null/omission semantics, not automatically `0s` |

The community provider can import DNS records by `id` or `site:id` and clients by MAC address. Because the provider source, resource type, and schemas change, `terraform state replace-provider` alone is insufficient. Deleting production records merely to simplify state is unacceptable.

Implementation follows the repaired current-contract test baseline and accepted `modernize-dagger-execution-contracts` foundation. The parent first qualifies an exact Dagger 1.0 beta CLI/engine/Python SDK tuple and records any fallback to 0.21.11; this change consumes its selected tuple rather than guessing a beta version. The canary branch is independent.

## Goals / Non-Goals

**Goals:**

- Migrate module configuration and production state ownership to exactly qualified `ubiquiti-community/unifi` 0.65.0.
- Preserve API-key authentication, Network 10.x client adoption, MAC normalization, DNS names/values, and strict-mode behavior.
- Rehearse the exact state handoff on disposable resources before touching production state.
- Preserve Cloudflare addresses, IDs, provider ownership, and reviewed functional state fields with no remote Cloudflare change; explain benign metadata/serialization differences instead of requiring byte equality.
- Produce a deterministic, secret-free import manifest and rollback checkpoint.

**Non-Goals:**

- Destroy or recreate production UniFi DNS records or clients.
- Rotate the UniFi API key or the two MCP sidecar accounts.
- Change KCL service/domain semantics or Cloudflare resources.
- Use `solomonhd.ai` sandbox results as a substitute for the final production zero-drift plan.

## Decisions

### 1. Use explicit remove-and-import instead of provider-address replacement

The migration removes only legacy UniFi resource bindings from state and imports the same remote objects under community-provider resource addresses. Data-source state is disposable and refreshes from configuration. `terraform state replace-provider` is not used because it cannot translate `unifi_user` to `unifi_client` or rename DNS attributes.

Import and refresh are not intrinsically read-only: target-provider Read may call `CreateClient` when an expected client is missing. Before provider execution, independently verify exact controller/site identity and object existence using a bounded inventory path qualified not to create clients. Qualify explicit provider-site configuration, MAC import site resolution, and DNS `site:id` behavior. A missing object, wrong site, or uncertain check stops the handoff, not automatic adoption/creation. Recheck near each effect and preserve the race/side-effect risk in production authorization; an earlier preflight does not make provider Read safe by definition.

Alternative considered: targeted destroy followed by apply. Rejected because it creates DNS downtime and turns a provider/schema defect into a production outage.

### 2. Read current client IP from the managed community client

Each normalized MAC maps to `unifi_client.device` with `allow_existing = true` and `skip_forget_on_destroy = true`. DNS A-record values use qualified `last_ip`; static `for_each` keys avoid computed-key expansion. Qualification covers active, remembered offline, missing, null, and stale-IP cases against the legacy behavior. Do not assume last known IP is current or acceptable for every offline device. Strict mode retains actionable missing-IP diagnostics, and production transfer stops on null, unexpected, or unexplained changed values rather than applying to discover them.

Alternative considered: replace the legacy data source with active-only `unifi_client_info`. Rejected as the sole source because inactive but remembered clients may not appear in the active-client surface. The sandbox and production plan must confirm `last_ip` behavior before migration proceeds.

### 3. Preserve logical DNS addresses while re-importing physical IDs

The Terraform logical keys for A and CNAME maps remain stable. Their HCL schema changes to `record_type` and `value`; positive explicit TTLs use qualified duration syntax, while zero/default is mapped to null/omission if the exact provider/controller contract requires it. Verify both null and explicit values round-trip without default drift. The manifest maps each logical address to its observed site and remote ID, permitting import into the same logical address after its old binding is removed.

### 4. Rehearse the actual handoff, not two independent CRUD tests

The normalized legacy provider creates a unique `unifi-poc-<run>.solomonhd.ai` record set and an isolated test client where supported, under explicit sandbox authorization. Rehearse a production-scale A/CNAME set, exact guarded handoff, zero drift, one benign update, and community cleanup. Exercise missing-client Read/creation and wrong-site behavior only in isolated fixtures or specifically authorized sandbox cases; never deliberately test these failures against production. Document how retained remembered clients under `skip_forget_on_destroy` are distinguished from removable test clients; cleanup acceptance includes absence of all run-owned records and any removable test clients, not a false promise of automatic forgetting.

### 5. Treat the production state snapshot and manifest as sensitive operational data

The full state snapshot is encrypted and access-restricted because Terraform state can contain secrets. The generated migration manifest contains only resource addresses, normalized MACs, sites, and remote IDs; it is scanned before being retained. Backend version identity/checksum is recorded so rollback targets the exact pre-handoff generation.

### 6. Gate every state phase on invariants

Before handoff, the manifest must account for all expected UniFi managed resources and no Cloudflare addresses. After import, the plan must show 0 add, 0 change, and 0 destroy for both components. Any mismatch stops before apply. No production `terraform apply` is needed merely to complete an import-only ownership migration.

### 7. Serialize the maintenance handoff without claiming a continuous CLI lock

Establish one authorized maintenance owner and exclude all other state writers across the whole handoff. Each state command acquires its actual supported backend lock; record its lifetime and reconcile the resulting state generation before the next phase. A backend lock released when one CLI command exits is not held across later commands. Qualify writer exclusion/fencing and backend version preconditions, retain phase intent/results and the last known generation, and fail closed if ownership or generation changes. Do not leave parallel active states claiming the same objects. After interruption, prove prior work stopped and reconcile authoritative state and remote identity before resuming or restoring; never blindly retry an uncertain import or overwrite a newer state generation.

Alternative considered: describe many Terraform invocations as one locked transaction. Rejected because ordinary CLI locks do not establish that guarantee. If maintenance writer exclusion cannot be established, production handoff remains blocked.

## Risks / Trade-offs

- [Community `last_ip` differs from legacy lookup behavior] -> Qualify active/offline behavior with fixtures and guarded authorized production evidence before state removal; stop on unusable or unexplained differences.
- [Import ID or address generation is wrong] → Generate and validate the manifest twice from state and provider API inventory, then rehearse the same tooling in the sandbox.
- [Two writers or states claim an object] -> Enforce one maintenance owner, actual per-command locks, phase receipts, and generation checks; fail closed on drift.
- [State commands accidentally include Cloudflare] -> Enforce a UniFi address allowlist and compare reviewed Cloudflare functional projections and identity before and after, not raw serialized state.
- [Import refresh proposes defaults] → Normalize HCL values and require a zero-drift plan; do not apply to silence unexplained changes.
- [Read/import unexpectedly mutates a client] -> Treat this as a possible remote effect, stop and reconcile; state restoration alone cannot undo it or prove rollback. No unapproved remote repair.

## Migration Plan

1. Confirm hardening, normalized-provider evidence, the repaired offline baseline, and accepted execution foundation; record the selected exact runtime tuple.
2. Implement the community provider/resource mapping and offline tests on a feature branch.
3. Run the complete legacy-to-community sandbox handoff below `solomonhd.ai`; verify cleanup.
4. Obtain separate production authorization, establish maintenance writer exclusion, and capture an encrypted snapshot, backend version/checksum, state inventory, and secret-free import manifest using qualified lock boundaries.
5. Rediscover counts, verify controller/site/object existence, and prove the manifest contains only UniFi addresses before any provider read/import or state removal.
6. Remove the legacy UniFi managed-resource bindings from state; allow obsolete data-source entries to refresh away.
7. Initialize the community provider and import clients by MAC plus DNS records by `site:id` into their target logical addresses.
8. Reconcile each phase's state generation and compare Cloudflare identity/functional projections, then run the full authorized Dagger plan under the qualified read-risk contract.
9. Proceed only if UniFi and Cloudflare both show 0 add, 0 change, and 0 destroy.
10. Record qualified feature acceptance from the consumer's matched Dagger/KCL feature pins before merge, coordinated with `adopt-modernized-dns-dagger-workspace`.

If authoritative evidence confirms no remote mutation and no conflicting state writer, restore the exact pre-handoff checkpoint through the tested guarded procedure and repin the immutable normalized legacy revision, then verify zero drift. An unknown or observed remote effect requires explicit reconciliation and, if necessary, separately authorized repair; do not claim state restoration rolls back remote changes. Retain maintenance ownership until reconciled or explicitly handed over to the operator, without pretending a CLI lock survives process death.

## Closeout

- Exact 0.65.0 source/schema, missing-client side effects, TTL zero/null, site resolution, and offline `last_ip` qualification are acceptance tasks, not waived assumptions.
- After qualified feature acceptance, separately review commit/push/merge/release, publish the accepted revision, and coordinate matched downstream Dagger/KCL production pins. Repeat guarded production plan acceptance from the published pin and retain sanitized evidence; do not merge unverified code.
- Update the Portainer `rotate-high-risk-credentials` dependency only after the published provider revision is accepted by its consumer; preserve the two MCP sidecar break-outs and keep UniFi API-key rotation out of scope. Specification sync and archive remain separate lifecycle actions.
