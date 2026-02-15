# OpenSpec Prompt Index: Simplified Combined Module

## Overview

Simplify the Dagger module by consolidating deployment functions. Instead of separate `deploy`, `deploy_unifi`, and `deploy_cloudflare` functions, use a single `deploy` function that deploys both components by default, with optional flags for single-component deployment.

## Current Problem

The `deploy()` function calls `deploy_unifi()` then `deploy_cloudflare()` sequentially. When using persistent local state (`--state-dir`), both share the same state file, causing the Cloudflare deployment to fail with:
```
Provider "registry.terraform.io/filipowm/unifi" requires explicit configuration
```

## Solution

1. Create a combined Terraform module at `terraform/modules/glue/`
2. Update `deploy()` to use the combined module by default
3. Add `--unifi-only` and `--cloudflare-only` flags for selective deployment
4. Remove `deploy_unifi()` and `deploy_cloudflare()` functions
5. Apply same pattern to `plan()` and `destroy()`

## Final Function Matrix

| Function | Behavior | Flags |
|----------|----------|-------|
| `deploy()` | Deploys both UniFi + Cloudflare | `--unifi-only`, `--cloudflare-only` |
| `plan()` | Plans both UniFi + Cloudflare | `--unifi-only`, `--cloudflare-only` |
| `destroy()` | Destroys both UniFi + Cloudflare | `--unifi-only`, `--cloudflare-only` |

**Removed:** `deploy_unifi()`, `deploy_cloudflare()`

## Prompts

| # | ID | Description | Dependencies |
|---|-----|-------------|--------------|
| 10 | create-combined-terraform-module | Create `terraform/modules/glue/` wrapper module | None |
| 11 | simplify-deploy-function | Update `deploy()`: use combined module, add flags, remove separate functions | 10 |
| 12 | simplify-plan-function | Update `plan()`: use combined module, add flags | 10 |
| 13 | simplify-destroy-function | Update `destroy()`: use combined module, add flags | 10 |
| 14 | update-documentation | Update README and docs for simplified API | 11-13 |

## Files to Modify

### New Files
- `terraform/modules/glue/main.tf`
- `terraform/modules/glue/variables.tf`
- `terraform/modules/glue/outputs.tf`
- `terraform/modules/glue/versions.tf`
- `terraform/modules/glue/README.md`

### Modified Files
- `src/main/main.py`:
  - Update `deploy()` (line ~842)
  - Remove `deploy_unifi()` (line ~356)
  - Remove `deploy_cloudflare()` (line ~542)
  - Update `plan()` (line ~1116)
  - Update `destroy()` (line ~1524)

### Documentation
- `README.md`
- `docs/dagger-reference.md`
- `docs/deployment-patterns.md`
