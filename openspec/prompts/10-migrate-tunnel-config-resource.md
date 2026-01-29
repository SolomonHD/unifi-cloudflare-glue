# OpenSpec Change Prompt: Migrate cloudflare_tunnel_config to cloudflare_zero_trust_tunnel_cloudflared_config

## Context

The `cloudflare_tunnel_config` resource is deprecated in Cloudflare provider v4.x and removed in v5.x. It has been renamed to `cloudflare_zero_trust_tunnel_cloudflared_config` with significant schema changes.

Key schema changes:
- `config` block → `config` attribute (block to nested object)
- `ingress_rule` blocks → `ingress` list within config
- `origin_request` block → `origin_request` nested object
- Structure changes from HCL blocks to nested objects

## Goal

Migrate the `cloudflare_tunnel_config` resource in main.tf to use the new `cloudflare_zero_trust_tunnel_cloudflared_config` resource name and updated schema.

## Scope

**In scope:**
- Rename resource from `cloudflare_tunnel_config` to `cloudflare_zero_trust_tunnel_cloudflared_config`
- Convert `config` from block syntax to nested object attribute
- Convert `ingress_rule` blocks to `ingress` list
- Convert `origin_request` blocks to nested objects
- Update dynamic block logic for `origin_request`

**Out of scope:**
- cloudflare_tunnel resource migration (handled in prompt 09)
- cloudflare_record migration (handled in prompt 11)

## Desired Behavior

### Before (v4.x - Current)

```hcl
resource "cloudflare_tunnel_config" "this" {
  for_each = local.effective_config.tunnels

  account_id = local.effective_config.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id

  config {
    dynamic "ingress_rule" {
      for_each = each.value.services
      content {
        hostname = ingress_rule.value.public_hostname
        service  = ingress_rule.value.local_service_url

        dynamic "origin_request" {
          for_each = ingress_rule.value.no_tls_verify ? [true] : []
          content {
            no_tls_verify = true
          }
        }
      }
    }

    ingress_rule {
      service = "http_status:404"
    }
  }
}
```

### After (v5.x - Target)

```hcl
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "this" {
  for_each = local.effective_config.tunnels

  account_id = local.effective_config.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id

  config = {
    ingress = concat(
      # Service ingress rules
      [
        for svc in each.value.services : {
          hostname = svc.public_hostname
          service  = svc.local_service_url
          origin_request = svc.no_tls_verify ? {
            no_tls_verify = true
          } : null
        }
      ],
      # Catch-all rule
      [{
        service = "http_status:404"
      }]
    )
  }
}
```

## Constraints & Assumptions

- The tunnel_id reference must use the new resource name from prompt 09
- Dynamic blocks must be converted to for expressions
- The `origin_request` conditional logic must be preserved
- The concat pattern ensures the catch-all rule is last

## Acceptance Criteria

- [ ] Resource renamed from `cloudflare_tunnel_config` to `cloudflare_zero_trust_tunnel_cloudflared_config`
- [ ] `config` changed from block to attribute syntax (`config = { ... }`)
- [ ] `ingress_rule` dynamic blocks converted to `ingress` list with for expressions
- [ ] `origin_request` dynamic blocks converted to conditional nested objects
- [ ] Catch-all 404 rule preserved at end of ingress list
- [ ] Terraform validate passes after changes

## Reference

- Target file: `terraform/modules/cloudflare-tunnel/main.tf` (line 39-67)
- Provider docs: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/zero_trust_tunnel_cloudflared_config

## Dependencies

- Depends on: Prompt 09 (cloudflare_tunnel resource migrated)
- Must be applied BEFORE prompt 11 (DNS record migration)
