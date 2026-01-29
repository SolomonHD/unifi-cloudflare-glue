# Proposal: Add Missing cloudflare_token Variable

## Summary

Add the missing `cloudflare_token` variable declaration to the `terraform/modules/cloudflare-tunnel/variables.tf` file. This variable is referenced by the Dagger code but not declared in the module.

## Context

The cloudflare-tunnel Terraform module manages Cloudflare Zero Trust Tunnels and DNS records. The Dagger code (`src/main/main.py`) already passes `TF_VAR_cloudflare_token` environment variable to Terraform, but the module lacks the corresponding variable declaration.

## Goals

1. Declare the `cloudflare_token` variable in `variables.tf`
2. Mark the variable as sensitive to prevent logging
3. Document the required API token permissions

## Non-Goals

- Adding provider configuration block (handled separately)
- Changes to `main.tf` or `versions.tf`
- Changes to Dagger code (already references this variable)

## Related Changes

- Depends on: None (independent change)
- Required by: Provider configuration block addition (future change)
