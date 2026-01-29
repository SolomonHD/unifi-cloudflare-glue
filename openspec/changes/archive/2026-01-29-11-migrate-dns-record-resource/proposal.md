# Proposal: Migrate cloudflare_record to cloudflare_dns_record

## Overview

Migrate the deprecated `cloudflare_record` resource to the new `cloudflare_dns_record` resource name and updated schema for Cloudflare provider v5.x compatibility.

## Background

The `cloudflare_record` resource was deprecated in Cloudflare provider v4.x and removed in v5.x. It has been renamed to `cloudflare_dns_record` with key schema changes:

- `value` → `content` (for CNAME records)
- `type` remains the same
- `name` now requires full FQDN
- `zone_id` remains the same
- `proxied` remains the same
- `ttl` now required (use 1 for automatic)

## Change Description

### Current State (v4.x - Deprecated)

The `terraform/modules/cloudflare-tunnel/main.tf` file uses the deprecated `cloudflare_record` resource:

```hcl
resource "cloudflare_record" "tunnel" {
  # Create a unique key for each MAC + service combination
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

### Target State (v5.x)

The resource will be renamed and converted to use the new `content` attribute and required `ttl`:

```hcl
resource "cloudflare_dns_record" "tunnel" {
  # Create a unique key for each MAC + service combination
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

## Scope

**In scope:**
- Rename resource from `cloudflare_record` to `cloudflare_dns_record`
- Update attribute `value` to `content`
- Add required `ttl` attribute (set to 1 for automatic)
- Update references to tunnel ID for CNAME content

**Out of scope:**
- cloudflare_zone data source changes (handled in prompt 12)
- Other resource migrations (handled in prompts 09, 10)

## Dependencies

- **Depends on:** Prompt 09 (cloudflare_tunnel resource migration) - COMPLETED
- **Can be applied concurrently with:** Prompt 10 (tunnel config migration)

## Related Specifications

- `terraform-module` - Core Terraform module requirements
- `provider-upgrade` - Cloudflare provider v5.x upgrade requirements

## Target File

- `terraform/modules/cloudflare-tunnel/main.tf` (lines 66-91)

## Acceptance Criteria

1. Resource renamed from `cloudflare_record` to `cloudflare_dns_record`
2. Attribute `value` renamed to `content`
3. Attribute `ttl = 1` added (automatic TTL)
4. All other attributes remain the same
5. Terraform validate passes after changes

## Risk Assessment

**Low Risk** - This is a straightforward resource renaming and schema update:
- No state file migrations required (Terraform handles resource type changes)
- The logic remains functionally identical
- Only attribute name changes and adding required ttl
- Well-documented migration path from Cloudflare provider

## References

- Cloudflare Provider Migration Guide: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/guides/version-5-upgrade
- Provider docs: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/dns_record
