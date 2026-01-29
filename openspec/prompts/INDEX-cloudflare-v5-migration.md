# OpenSpec Prompt Index: Cloudflare Provider v5 Migration

This directory contains OpenSpec prompts to migrate the `terraform/modules/cloudflare-tunnel` module from Cloudflare provider v4.x to v5.x, addressing deprecated resources and missing provider configuration.

## Issues Being Resolved

1. **Missing Provider Configuration** - No explicit `provider "cloudflare"` block to configure API token
2. **Missing Variable Declaration** - `cloudflare_token` variable used but not declared
3. **Deprecated Resources** - Using v4.x resources that are removed in v5.x:
   - `cloudflare_tunnel` → `cloudflare_zero_trust_tunnel_cloudflared`
   - `cloudflare_tunnel_config` → `cloudflare_zero_trust_tunnel_cloudflared_config`
   - `cloudflare_record` → `cloudflare_dns_record`
   - `cloudflare_zone` data source schema changes

## Prompt Sequence

| Order | Prompt | Description |
|-------|--------|-------------|
| 06 | [06-upgrade-dagger-engine.md](./06-upgrade-dagger-engine.md) | Upgrade Dagger engine version to latest stable |
| 07 | [07-add-cloudflare-token-variable.md](./07-add-cloudflare-token-variable.md) | Add missing `cloudflare_token` variable to variables.tf |
| 08 | [08-update-provider-version.md](./08-update-provider-version.md) | Update Cloudflare provider version to ~> 5.0 |
| 09 | [09-migrate-cloudflare-tunnel-resource.md](./09-migrate-cloudflare-tunnel-resource.md) | Migrate `cloudflare_tunnel` to `cloudflare_zero_trust_tunnel_cloudflared` |
| 10 | [10-migrate-tunnel-config-resource.md](./10-migrate-tunnel-config-resource.md) | Migrate `cloudflare_tunnel_config` to `cloudflare_zero_trust_tunnel_cloudflared_config` |
| 11 | [11-migrate-dns-record-resource.md](./11-migrate-dns-record-resource.md) | Migrate `cloudflare_record` to `cloudflare_dns_record` |
| 12 | [12-update-zone-data-source.md](./12-update-zone-data-source.md) | Update `cloudflare_zone` data source to v5.x schema |

## Execution Order

Prompts should be executed in order (06 → 12) where dependencies exist:

1. **Prompt 06** - Dagger engine upgrade (independent)
2. **Prompt 07** - Add token variable (independent, but needed for provider config)
3. **Prompt 08** - Update provider version (MUST be before 09-12)
4. **Prompt 09** - Migrate tunnel resource (MUST be before 10, 11)
5. **Prompt 10** - Migrate tunnel config (depends on 09)
6. **Prompt 11** - Migrate DNS record (depends on 09)
7. **Prompt 12** - Update zone data source (depends on 08)

## Parallel Execution Groups

- **Group 1 (Independent):** 06, 07
- **Group 2 (Provider Update):** 08
- **Group 3 (Resource Migrations):** 09, then 10 & 11 in parallel, then 12

## Target Files

- `dagger.json` - Dagger engine version
- `terraform/modules/cloudflare-tunnel/variables.tf` - Variable declarations
- `terraform/modules/cloudflare-tunnel/versions.tf` - Provider version constraints
- `terraform/modules/cloudflare-tunnel/main.tf` - Resource definitions

## Expected Outcome

After all prompts are implemented:
- ✅ Dagger engine upgraded to latest stable version
- ✅ `cloudflare_token` variable properly declared
- ✅ Cloudflare provider updated to v5.x
- ✅ All deprecated resources migrated to new names
- ✅ All resource schemas updated to v5.x format
- ✅ No deprecation warnings or errors
- ✅ Terraform validate passes successfully

## Related Documentation

- Cloudflare Provider v5 Migration Guide: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/guides/version-5-upgrade
- Latest Provider Version: 5.16.0
- Dagger Releases: https://github.com/dagger/dagger/releases
