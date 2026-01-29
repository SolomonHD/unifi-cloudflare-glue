# OpenSpec Change Prompt: Migrate cloudflare_tunnel to cloudflare_zero_trust_tunnel_cloudflared

## Context

The `cloudflare_tunnel` resource is deprecated in Cloudflare provider v4.x and removed in v5.x. It has been renamed to `cloudflare_zero_trust_tunnel_cloudflared` with schema changes.

Key schema changes:
- `secret` → `tunnel_secret` (name change)
- `cname` attribute removed (no longer available)

## Goal

Migrate the `cloudflare_tunnel` resource in main.tf to use the new `cloudflare_zero_trust_tunnel_cloudflared` resource name and updated schema.

## Scope

**In scope:**
- Rename resource from `cloudflare_tunnel` to `cloudflare_zero_trust_tunnel_cloudflared`
- Update attribute `secret` to `tunnel_secret`
- Update references in other resources (tunnel_config)

**Out of scope:**
- cloudflare_tunnel_config migration (separate prompt)
- cloudflare_record migration (separate prompt)

## Desired Behavior

### Before (v4.x - Current)

```hcl
resource "cloudflare_tunnel" "this" {
  for_each = local.effective_config.tunnels

  account_id = local.effective_config.account_id
  name       = each.value.tunnel_name
  secret     = base64encode(random_password.tunnel_secret[each.key].result)
}
```

### After (v5.x - Target)

```hcl
resource "cloudflare_zero_trust_tunnel_cloudflared" "this" {
  for_each = local.effective_config.tunnels

  account_id    = local.effective_config.account_id
  name          = each.value.tunnel_name
  tunnel_secret = base64encode(random_password.tunnel_secret[each.key].result)
}
```

### Reference Updates

Update the reference in `cloudflare_tunnel_config` resource:

```hcl
# Before:
tunnel_id = cloudflare_tunnel.this[each.key].id

# After:
tunnel_id = cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id
```

## Constraints & Assumptions

- The tunnel secret must still be base64 encoded
- Resource behavior remains the same (creates a Cloudflare tunnel)
- The `for_each` logic and loop structure remain unchanged
- References in `cloudflare_tunnel_config` must be updated

## Acceptance Criteria

- [ ] Resource renamed from `cloudflare_tunnel` to `cloudflare_zero_trust_tunnel_cloudflared`
- [ ] Attribute `secret` renamed to `tunnel_secret`
- [ ] References in `cloudflare_tunnel_config` resource updated
- [ ] All other attributes remain the same
- [ ] Terraform validate passes after changes

## Reference

- Target file: `terraform/modules/cloudflare-tunnel/main.tf` (line 22-28)
- Related reference: Line 43 (tunnel_id reference)
- Provider docs: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/resources/zero_trust_tunnel_cloudflared

## Dependencies

- Depends on: Prompt 08 (provider version updated to ~> 5.0)
- Must be applied BEFORE prompt 10 (tunnel_config migration)
