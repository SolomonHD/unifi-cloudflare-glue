# Proposal: Migrate cloudflare_tunnel to cloudflare_zero_trust_tunnel_cloudflared

## Overview

Migrate the deprecated `cloudflare_tunnel` resource to the new `cloudflare_zero_trust_tunnel_cloudflared` resource for Cloudflare provider v5.x compatibility.

## Background

The `cloudflare_tunnel` resource is deprecated in Cloudflare provider v4.x and removed in v5.x. It has been renamed to `cloudflare_zero_trust_tunnel_cloudflared` with schema changes:

- `secret` → `tunnel_secret` (attribute renamed)
- `cname` attribute removed (no longer available)

## Goals

1. Rename resource from `cloudflare_tunnel` to `cloudflare_zero_trust_tunnel_cloudflared`
2. Update attribute `secret` to `tunnel_secret`
3. Update all references to the resource in other resources (tunnel_config, cloudflare_record)
4. Maintain identical behavior for tunnel creation

## Non-Goals

- Migration of `cloudflare_tunnel_config` resource (handled in separate prompt 10)
- Migration of `cloudflare_record` resource (handled in separate prompt 11)
- Changes to tunnel secret generation logic
- Changes to tunnel configuration structure

## Affected Components

- `terraform/modules/cloudflare-tunnel/main.tf`
  - Resource definition (lines 22-28)
  - Reference in `cloudflare_tunnel_config` (line 43)
  - Reference in `cloudflare_record` (line 93)

## Dependencies

- **Depends on:** Prompt 08 (provider version updated to ~> 5.0)
- **Blocks:** Prompt 10 (tunnel_config migration), Prompt 11 (DNS record migration)

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| State migration required | High | Terraform state mv commands documented in apply workflow |
| Reference updates missed | Medium | Comprehensive grep search for all references |
| Secret attribute name confusion | Low | Clear documentation of attribute mapping |

## Success Criteria

- Resource renamed from `cloudflare_tunnel` to `cloudflare_zero_trust_tunnel_cloudflared`
- Attribute `secret` renamed to `tunnel_secret`
- All references updated in dependent resources
- `terraform validate` passes after changes
- No functional changes to tunnel behavior
