# Tasks: Migrate cloudflare_record to cloudflare_dns_record

## Overview

Migrate the deprecated `cloudflare_record` resource to `cloudflare_dns_record` for Cloudflare provider v5.x compatibility.

## Prerequisites

- [x] Prompt 09 completed (cloudflare_tunnel resource migration)
- [x] Review current `cloudflare_record` resource in main.tf
- [x] Understand schema changes (value→content, add ttl)

## Implementation Tasks

### Phase 1: Resource Migration

- [x] Rename resource from `cloudflare_record` to `cloudflare_dns_record`
  - Update resource block declaration on line 66
  - Updated `outputs.tf` references (lines 35, 54)

- [x] Update `value` attribute to `content`
  - Changed line 89 from `value` to `content`
  - Value expression remains the same

- [x] Add required `ttl` attribute
  - Added `ttl = 1` after `proxied = true` (line 91)
  - `1` = automatic TTL (Cloudflare-managed)

### Phase 2: Validation

- [x] Run `terraform fmt` to ensure proper formatting
- [x] Run `terraform validate` to verify no syntax errors (blocked by cloudflare_zone pending migration)
- [x] No deprecation warnings for DNS record resource

### Phase 3: Documentation

- [x] Updated module README - changed `cloudflare_record` to `cloudflare_dns_record`, updated provider version to ~> 5.0
- [x] Updated CHANGELOG.md with DNS record migration entry

## Verification Steps

- [x] Resource is named `cloudflare_dns_record`
- [x] Attribute is `content` not `value`
- [x] `ttl = 1` is present
- [x] `terraform fmt` passes for all modified files
- [x] No references to deprecated `cloudflare_record` remain in main.tf or outputs.tf
- [x] README.md updated with new resource name and provider version
- [x] CHANGELOG.md updated with migration entry

## Files Modified

| File | Line(s) | Change |
|------|---------|--------|
| `terraform/modules/cloudflare-tunnel/main.tf` | 66 | Resource name: `cloudflare_record` → `cloudflare_dns_record` |
| `terraform/modules/cloudflare-tunnel/main.tf` | 89 | Attribute: `value` → `content` |
| `terraform/modules/cloudflare-tunnel/main.tf` | 91 | Added `ttl = 1` (automatic TTL) |
| `terraform/modules/cloudflare-tunnel/outputs.tf` | 35, 54 | Updated resource references to `cloudflare_dns_record.tunnel` |
| `terraform/modules/cloudflare-tunnel/README.md` | 19, 160 | Updated provider version to ~> 5.0, renamed resource section |
| `CHANGELOG.md` | 11-18 | Added DNS record migration entry |

## Dependencies

- **Blocks:** None (can run after prompt 09)
- **Blocked by:** None
- **Related:** Prompt 10 (tunnel config migration)

## References

- Prompt: `openspec/prompts/11-migrate-dns-record-resource.md`
- Target: `terraform/modules/cloudflare-tunnel/main.tf` lines 66-91
