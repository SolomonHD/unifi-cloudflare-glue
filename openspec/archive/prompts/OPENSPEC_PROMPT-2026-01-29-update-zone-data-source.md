# OpenSpec Change Prompt: Update cloudflare_zone Data Source

## Context

The `cloudflare_zone` data source schema has changed in Cloudflare provider v5.x. The `name` attribute at the root level is deprecated in favor of using a `filter` block with a `name` attribute inside it.

Key schema changes:
- Direct `name` attribute → `filter { name = ... }`
- Still returns `id` for zone_id reference

## Goal

Update the `cloudflare_zone` data source in main.tf to use the new v5.x schema with filter block.

## Scope

**In scope:**
- Update `data "cloudflare_zone" "this"` to use filter block syntax
- Change from direct `name` attribute to `filter { name = ... }`

**Out of scope:**
- Resource migrations (handled in prompts 09-11)
- Provider version updates (handled in prompt 08)

## Desired Behavior

### Before (v4.x - Current)

```hcl
data "cloudflare_zone" "this" {
  name = local.effective_config.zone_name
}
```

### After (v5.x - Target)

```hcl
data "cloudflare_zone" "this" {
  filter {
    name = local.effective_config.zone_name
  }
}
```

## Constraints & Assumptions

- The data source still returns `id` which is used for `zone_id` in DNS records
- The filter block is the standard way to query zones in v5.x
- No changes needed to how the data source output is used

## Acceptance Criteria

- [ ] Data source updated to use `filter` block with nested `name` attribute
- [ ] Direct `name` attribute removed from root level
- [ ] References to `data.cloudflare_zone.this.id` continue to work
- [ ] Terraform validate passes after changes

## Reference

- Target file: `terraform/modules/cloudflare-tunnel/main.tf` (line 17-19)
- Provider docs: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/data-sources/zone

## Dependencies

- Depends on: Prompt 08 (provider version updated to ~> 5.0)
- Can be applied concurrently with prompts 09-11
