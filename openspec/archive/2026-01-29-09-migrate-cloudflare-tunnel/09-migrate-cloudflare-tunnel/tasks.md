# Tasks: Migrate cloudflare_tunnel to cloudflare_zero_trust_tunnel_cloudflared

## Implementation Tasks

- [x] 1. Update resource type in main.tf
  - Change `resource "cloudflare_tunnel" "this"` to `resource "cloudflare_zero_trust_tunnel_cloudflared" "this"`
  - Updated lines 22-28 in terraform/modules/cloudflare-tunnel/main.tf

- [x] 2. Update secret attribute name
  - Change `secret = base64encode(...)` to `tunnel_secret = base64encode(...)`
  - Updated at line 27 in terraform/modules/cloudflare-tunnel/main.tf

- [x] 3. Update reference in cloudflare_tunnel_config
  - Change `tunnel_id = cloudflare_tunnel.this[each.key].id` to `tunnel_id = cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id`
  - Updated at line 43 in terraform/modules/cloudflare-tunnel/main.tf

- [x] 4. Update reference in cloudflare_record
  - Change `value = "${cloudflare_tunnel.this[each.value.mac].id}.cfargotunnel.com"` to `value = "${cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id}.cfargotunnel.com"`
  - Updated at line 93 in terraform/modules/cloudflare-tunnel/main.tf

- [x] 5. Run terraform validate
  - ✅ Tunnel resource validates correctly (no errors for `cloudflare_zero_trust_tunnel_cloudflared`)
  - Other validation errors are for resources in separate migration prompts

## Validation Tasks

- [x] 6. Verify all references updated
  - Ran `grep -n "cloudflare_tunnel" terraform/modules/cloudflare-tunnel/*.tf`
  - Only `cloudflare_tunnel_config` remains (separate resource type, handled in Prompt 10)
  - All `cloudflare_tunnel` references successfully migrated to `cloudflare_zero_trust_tunnel_cloudflared`

- [ ] 7. Documentation update
  - Add state migration commands to apply workflow
  - Document the resource renaming in CHANGELOG.md

## State Migration (Apply Phase)

When applying this change to existing infrastructure:

```bash
# For each tunnel in the configuration:
terraform state mv 'module.cloudflare_tunnel.cloudflare_tunnel.this["<mac_address>"]' 'module.cloudflare_tunnel.cloudflare_zero_trust_tunnel_cloudflared.this["<mac_address>"]'
```

Or use the scripted approach:

```bash
# List all tunnel resources in state
terraform state list | grep cloudflare_tunnel.this

# Generate mv commands for each
for resource in $(terraform state list | grep 'cloudflare_tunnel.this\['); do
  new_resource=$(echo "$resource" | sed 's/cloudflare_tunnel/cloudflare_zero_trust_tunnel_cloudflared/')
  echo "terraform state mv '$resource' '$new_resource'"
done
```

## Dependencies

- Must be applied AFTER: Prompt 08 (provider v5 update)
- Must be applied BEFORE: Prompt 10 (tunnel_config migration), Prompt 11 (DNS record migration)

## Files Modified

- `terraform/modules/cloudflare-tunnel/main.tf`
