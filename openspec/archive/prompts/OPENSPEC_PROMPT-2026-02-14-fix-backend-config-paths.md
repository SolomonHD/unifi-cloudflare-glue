# OpenSpec Change Prompt

## Context

The `unifi-cloudflare-glue` Dagger module has inconsistent backend config file paths in `src/main/main.py`. When using remote Terraform backends (S3, etc.) from a consumer repository, Terraform init fails with:

```
Error: Failed to read file
The file "../root/.terraform/backend.tfbackend" could not be read.
```

This occurs because the backend config file is mounted at one path but referenced at a different path in the Terraform init command.

## Goal

Fix the file path mismatches in `src/main/main.py` so that backend config files are mounted and referenced at consistent paths across all functions.

## Scope

**In scope:**
- Fix path mismatch in `plan()` function (lines 1106 and 1201)
- Fix path mismatch in `get_tunnel_secrets()` function (line 2821)
- Ensure all backend config files are mounted at `/root/.terraform/backend.tfbackend`

**Out of scope:**
- Changes to backend config processing logic
- Changes to Terraform module content
- Changes to function signatures or behavior

## Desired Behavior

- Backend config files are consistently mounted at `/root/.terraform/backend.tfbackend`
- Terraform init commands reference the same path
- Remote backend deployments work correctly from consumer repositories

## Constraints & Assumptions

- Use `.tfbackend` extension consistently (not `.hcl`)
- The `deploy_unifi()` and `deploy_cloudflare()` functions already have correct paths
- The `_process_backend_config()` function already converts YAML to HCL when needed

## Acceptance Criteria

- [ ] Line 1106 in `plan()`: Change `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [ ] Line 1201 in `plan()`: Change `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [ ] Line 2821 in `get_tunnel_secrets()`: Change `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [ ] All backend config mounts use consistent `.tfbackend` extension
- [ ] Remote backend deployments work from consumer repositories
