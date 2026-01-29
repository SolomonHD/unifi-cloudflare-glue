# Proposal: Migrate cloudflare_tunnel_config to cloudflare_zero_trust_tunnel_cloudflared_config

## Overview

Migrate the deprecated `cloudflare_tunnel_config` resource to the new `cloudflare_zero_trust_tunnel_cloudflared_config` resource name and updated schema for Cloudflare provider v5.x compatibility.

## Background

The `cloudflare_tunnel_config` resource was deprecated in Cloudflare provider v4.x and removed in v5.x. It has been renamed to `cloudflare_zero_trust_tunnel_cloudflared_config` with significant schema changes:

- `config` block → `config` attribute (block to nested object)
- `ingress_rule` blocks → `ingress` list within config
- `origin_request` block → `origin_request` nested object
- Structure changes from HCL blocks to nested objects

## Change Description

### Current State (v4.x - Deprecated)

The `terraform/modules/cloudflare-tunnel/main.tf` file uses the deprecated `cloudflare_tunnel_config` resource with block syntax:

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

### Target State (v5.x)

The resource will be renamed and converted to use attribute syntax with nested objects:

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

## Scope

**In scope:**
- Rename resource from `cloudflare_tunnel_config` to `cloudflare_zero_trust_tunnel_cloudflared_config`
- Convert `config` from block syntax to nested object attribute
- Convert `ingress_rule` blocks to `ingress` list
- Convert `origin_request` blocks to nested objects
- Update dynamic block logic for `origin_request`

**Out of scope:**
- cloudflare_tunnel resource migration (handled in prompt 09 - already completed)
- cloudflare_record migration (handled in prompt 11)
- cloudflare_zone data source updates (handled in prompt 12)

## Dependencies

- **Depends on:** Prompt 09 (cloudflare_tunnel resource migration) - COMPLETED
- **Must be applied BEFORE:** Prompt 11 (DNS record migration)

## Related Specifications

- `terraform-module` - Core Terraform module requirements
- `provider-upgrade` - Cloudflare provider v5.x upgrade requirements

## Target File

- `terraform/modules/cloudflare-tunnel/main.tf` (lines 39-67)

## Acceptance Criteria

1. Resource renamed from `cloudflare_tunnel_config` to `cloudflare_zero_trust_tunnel_cloudflared_config`
2. `config` changed from block to attribute syntax (`config = { ... }`)
3. `ingress_rule` dynamic blocks converted to `ingress` list with for expressions
4. `origin_request` dynamic blocks converted to conditional nested objects
5. Catch-all 404 rule preserved at end of ingress list
6. Terraform validate passes after changes

## Risk Assessment

**Low Risk** - This is a straightforward resource renaming and schema conversion:
- No state file migrations required (Terraform handles resource type changes)
- The logic remains functionally identical
- Only syntax changes from blocks to attributes
- Well-documented migration path from Cloudflare provider

## References

- Cloudflare Provider Migration Guide: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/guides/version-5-upgrade
- Provider docs: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/zero_trust_tunnel_cloudflared_config
