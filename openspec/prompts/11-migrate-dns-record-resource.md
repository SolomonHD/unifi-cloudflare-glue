# OpenSpec Change Prompt: Migrate cloudflare_record to cloudflare_dns_record

## Context

The `cloudflare_record` resource is deprecated in Cloudflare provider v4.x and removed in v5.x. It has been renamed to `cloudflare_dns_record` with schema changes.

Key schema changes:
- `value` → `content` (for CNAME records)
- `type` remains the same
- `name` now requires full FQDN
- `zone_id` remains the same
- `proxied` remains the same
- `ttl` now required (use 1 for automatic)

## Goal

Migrate the `cloudflare_record` resource in main.tf to use the new `cloudflare_dns_record` resource name and updated schema.

## Scope

**In scope:**
- Rename resource from `cloudflare_record` to `cloudflare_dns_record`
- Update attribute `value` to `content`
- Add required `ttl` attribute
- Update references to tunnel ID for CNAME value

**Out of scope:**
- cloudflare_zone data source changes (separate prompt)
- Other resource migrations (handled in prompts 09, 10)

## Desired Behavior

### Before (v4.x - Current)

```hcl
resource "cloudflare_record" "tunnel" {
  for_each = {
    for pair in setproduct(
      keys(local.effective_config.tunnels),
      flatten([
        for mac, tunnel in local.effective_config.tunnels : [
          for idx, svc in tunnel.services : {
            mac      = mac
            index    = idx
            hostname = svc.public_hostname
          }
        ]
      ])
      ) : "${pair[0]}-${pair[1].index}" => {
      mac      = pair[0]
      hostname = pair[1].hostname
    }
  }

  zone_id = data.cloudflare_zone.this.id
  name    = each.value.hostname
  type    = "CNAME"
  value   = "${cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id}.cfargotunnel.com"
  proxied = true
}
```

### After (v5.x - Target)

```hcl
resource "cloudflare_dns_record" "tunnel" {
  for_each = {
    for pair in setproduct(
      keys(local.effective_config.tunnels),
      flatten([
        for mac, tunnel in local.effective_config.tunnels : [
          for idx, svc in tunnel.services : {
            mac      = mac
            index    = idx
            hostname = svc.public_hostname
          }
        ]
      ])
      ) : "${pair[0]}-${pair[1].index}" => {
      mac      = pair[0]
      hostname = pair[1].hostname
    }
  }

  zone_id = data.cloudflare_zone.this.id
  name    = each.value.hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id}.cfargotunnel.com"
  proxied = true
  ttl     = 1  # 1 = automatic
}
```

## Constraints & Assumptions

- The `for_each` logic remains unchanged
- Tunnel ID reference uses the new resource name from prompt 09
- `ttl = 1` means automatic TTL (Cloudflare-managed)
- `content` replaces `value` for all record types

## Acceptance Criteria

- [ ] Resource renamed from `cloudflare_record` to `cloudflare_dns_record`
- [ ] Attribute `value` renamed to `content`
- [ ] Attribute `ttl = 1` added (automatic TTL)
- [ ] All other attributes remain the same
- [ ] Terraform validate passes after changes

## Reference

- Target file: `terraform/modules/cloudflare-tunnel/main.tf` (line 70-95)
- Provider docs: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/dns_record

## Dependencies

- Depends on: Prompt 09 (cloudflare_tunnel resource migrated - for tunnel_id reference)
- Can be applied concurrently with prompt 10
