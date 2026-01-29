# OpenSpec Change Prompt: Add Missing cloudflare_token Variable

## Context

The `terraform/modules/cloudflare-tunnel` module references `var.cloudflare_token` in the Dagger code (`src/main/main.py` line 280) but does not declare this variable in `variables.tf`. The module also needs an explicit provider configuration to use this token.

## Goal

Add the missing `cloudflare_token` variable declaration to the cloudflare-tunnel module's variables.tf file.

## Scope

**In scope:**
- Add `cloudflare_token` variable to `terraform/modules/cloudflare-tunnel/variables.tf`
- Add proper type annotation (string) and sensitive flag
- Add documentation for the variable

**Out of scope:**
- Adding provider configuration block (handled in separate prompt)
- Changes to main.tf
- Changes to versions.tf

## Desired Behavior

### Variable Declaration

Add the following variable to `variables.tf`:

```hcl
variable "cloudflare_token" {
  description = "Cloudflare API token for authentication. Must have permissions for Zone:Read, DNS:Edit, and Cloudflare Tunnel:Edit."
  type        = string
  sensitive   = true
}
```

The variable should:
- Be required (no default value)
- Be marked as sensitive to prevent logging
- Have clear documentation about required permissions

## Constraints & Assumptions

- The Dagger code already passes this via `TF_VAR_cloudflare_token` environment variable
- This is a prerequisite for adding the provider configuration block
- The variable name must match what the Dagger code expects

## Acceptance Criteria

- [ ] `cloudflare_token` variable added to `terraform/modules/cloudflare-tunnel/variables.tf`
- [ ] Variable has `sensitive = true` flag
- [ ] Variable has clear description with required permissions
- [ ] Variable has no default (required input)
- [ ] Variable is properly formatted with HCL conventions

## Reference

- Target file: `terraform/modules/cloudflare-tunnel/variables.tf`
- Related Dagger code: `src/main/main.py` line 280

## Dependencies

None - this is an independent change.
