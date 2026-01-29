# Proposal: Update Cloudflare Provider Version to v5.x

## Summary

Update the Cloudflare Terraform provider version constraint from `~> 4.0` to `~> 5.0` in the cloudflare-tunnel module to access the latest provider features and prepare for resource migration.

## Context

The cloudflare-tunnel module currently uses Cloudflare provider version `~> 4.0`. The latest version is `5.16.0`, which includes the new `cloudflare_zero_trust_tunnel_cloudflared` resources and deprecates the old `cloudflare_tunnel` resources.

This change is part of the Cloudflare Provider v5 Migration initiative (see INDEX-cloudflare-v5-migration.md).

## Goals

1. Update Cloudflare provider version constraint to `~> 5.0`
2. Maintain compatibility with existing Terraform minimum version (>= 1.5.0)
3. Leave random provider version unchanged
4. Prepare codebase for subsequent resource name migrations

## Non-Goals

- Resource name migrations (handled in separate changes)
- Schema updates for resources
- Provider configuration block changes

## Success Criteria

- Cloudflare provider version updated to `"~> 5.0"` in versions.tf
- Source remains `"cloudflare/cloudflare"`
- Random provider unchanged
- Terraform required_version unchanged
