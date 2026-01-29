# Proposal: Update cloudflare_zone Data Source to v5.x Schema

## Summary

Update the `cloudflare_zone` data source in the cloudflare-tunnel module to use the new Cloudflare provider v5.x schema with filter block syntax.

## Background

The Cloudflare provider v5.x introduced breaking changes to the `cloudflare_zone` data source. The direct `name` attribute at the root level is deprecated in favor of a `filter` block containing the `name` attribute.

### Current State (v4.x)
```hcl
data "cloudflare_zone" "this" {
  name = local.effective_config.zone_name
}
```

### Target State (v5.x)
```hcl
data "cloudflare_zone" "this" {
  filter {
    name = local.effective_config.zone_name
  }
}
```

## Scope

### In Scope
- Update `data.cloudflare_zone.this` to use filter block syntax
- Ensure `data.cloudflare_zone.this.id` references continue to work

### Out of Scope
- Resource migrations (handled in prompts 09-11)
- Provider version updates (handled in prompt 08)
- Changes to how the zone_id is consumed

## Impact

- **Breaking Change**: None - the data source output remains the same
- **Dependencies**: Requires Cloudflare provider v5.x (handled in prompt 08)
- **Consumers**: No changes needed to resources that reference `data.cloudflare_zone.this.id`

## Acceptance Criteria

- [ ] Data source uses `filter` block with nested `name` attribute
- [ ] Direct `name` attribute removed from root level
- [ ] `data.cloudflare_zone.this.id` continues to return zone ID
- [ ] Terraform validate passes

## Related

- Depends on: Prompt 08 (provider v5.x upgrade)
- Can be applied concurrently with: Prompts 09-11 (resource migrations)
- Target file: `terraform/modules/cloudflare-tunnel/main.tf` (lines 17-19)
