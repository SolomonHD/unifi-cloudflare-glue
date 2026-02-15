# OpenSpec Change Prompt

## Context
The unifi-cloudflare-glue Dagger module has a bug where backend configuration files are not properly converted from YAML to HCL format in the `plan` and `get_tunnel_secrets` functions. This causes Terraform to fail when parsing the backend config file because it receives YAML syntax (`bucket: value`) instead of HCL syntax (`bucket = "value"`).

## Goal
Fix the backend config file handling in `plan` and `get_tunnel_secrets` functions to properly convert YAML backend config files to HCL format before mounting them for Terraform consumption.

## Scope

**In scope:**
- Fix `plan` function (lines 1105-1106) - UniFi container backend config mounting
- Fix `plan` function (lines 1199-1201) - Cloudflare container backend config mounting
- Fix `get_tunnel_secrets` function (lines 2818-2821) - Terraform container backend config mounting
- Use existing `_process_backend_config()` helper for YAML→HCL conversion
- Ensure consistency with `deploy_unifi`, `deploy_cloudflare`, `destroy_unifi`, `destroy_cloudflare` functions which already handle this correctly

**Out of scope:**
- Changes to `backend_config.py` conversion logic (already works correctly)
- Changes to other functions that already handle backend config properly
- New features or functionality beyond the bugfix

## Desired Behavior
- When a user passes a YAML backend config file to `plan` function, it should be automatically converted to HCL format before being mounted at `/root/.terraform/backend.tfbackend`
- When a user passes a YAML backend config file to `get_tunnel_secrets` function, it should be automatically converted to HCL format before being mounted
- HCL backend config files should continue to work unchanged (pass-through)
- The fix should follow the same pattern used in `deploy_unifi`, `deploy_cloudflare`, `destroy_unifi`, and `destroy_cloudflare` functions

## Constraints & Assumptions
- The `_process_backend_config()` helper function already exists and works correctly (used by deploy/destroy functions)
- The fix must use `with_new_file()` instead of `with_file()` to mount the converted content
- Lines referenced are based on current main.py as of commit with this prompt
- The `backend_config.py` module provides `yaml_to_hcl()` and `process_backend_config_content()` functions

## Acceptance Criteria
- [ ] `plan` function converts YAML backend config to HCL before mounting for UniFi container
- [ ] `plan` function converts YAML backend config to HCL before mounting for Cloudflare container
- [ ] `get_tunnel_secrets` function converts YAML backend config to HCL before mounting
- [ ] HCL backend config files continue to work (pass-through conversion)
- [ ] Error handling is preserved (try/except blocks with meaningful error messages)
- [ ] Pattern matches existing implementations in deploy/destroy functions
## Acceptance Criteria

- [ ] Line 1106 in `plan()`: Change `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [ ] Line 1201 in `plan()`: Change `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [ ] Line 2821 in `get_tunnel_secrets()`: Change `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [ ] All backend config mounts use consistent `.tfbackend` extension
- [ ] Remote backend deployments work from consumer repositories
