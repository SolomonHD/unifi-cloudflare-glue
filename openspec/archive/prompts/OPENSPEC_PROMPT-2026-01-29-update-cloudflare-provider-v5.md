# OpenSpec Change Prompt: Update Cloudflare Provider Version to v5.x

## Context

The cloudflare-tunnel module currently uses Cloudflare provider version `~> 4.0` in `versions.tf`. The latest version is `5.16.0`, which includes the new `cloudflare_zero_trust_tunnel_cloudflared` resources and deprecates the old `cloudflare_tunnel` resources.

## Goal

Update the Cloudflare provider version constraint from `~> 4.0` to `~> 5.0` in the cloudflare-tunnel module.

## Scope

**In scope:**
- Update `required_providers.cloudflare.version` in `terraform/modules/cloudflare-tunnel/versions.tf`
- Update from `"~> 4.0"` to `"~> 5.0"`

**Out of scope:**
- Resource name migrations (handled in separate prompts)
- Schema updates for resources
- Provider configuration block

## Desired Behavior

### Version Update

Update `terraform/modules/cloudflare-tunnel/versions.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"  # Updated from ~> 4.0
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}
```

## Constraints & Assumptions

- Terraform >= 1.5.0 is still the minimum required version
- The random provider version can remain unchanged
- This change alone will cause deprecation warnings to become errors until resource names are updated

## Acceptance Criteria

- [ ] Cloudflare provider version updated to `"~> 5.0"` in versions.tf
- [ ] Source remains `"cloudflare/cloudflare"`
- [ ] Random provider unchanged
- [ ] Terraform required_version unchanged

## Reference

- Target file: `terraform/modules/cloudflare-tunnel/versions.tf` (line 7)
- Latest provider version: `5.16.0`
- Provider documentation: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs

## Dependencies

- Must be applied BEFORE resource migration prompts (09, 10, 11)
- Can be applied AFTER or concurrent with prompts 06 and 07
