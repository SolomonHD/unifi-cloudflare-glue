# Dagger Module Integration - OpenSpec Prompt Index

This directory contains OpenSpec prompts for adding Dagger CLI functions to the `unifi-cloudflare-glue` repository. These prompts enable containerized, reproducible pipelines for KCL generation, Terraform deployment, and integration testing.

## Prerequisites

- Dagger must be initialized at the **repository base** (for git-related functions to work)
- All sensitive inputs (API keys, tokens) must use Dagger's `Secret` type
- Python SDK will be used for the Dagger module

## Prompt Sequence

| Order | Prompt | Purpose | Dependencies |
|-------|--------|---------|--------------|
| 01 | [dagger-module-scaffolding](./01-dagger-module-scaffolding.md) | Initialize Dagger module at repo base, create basic structure | None |
| 02 | [kcl-generation-functions](./02-kcl-generation-functions.md) | Functions to generate UniFi and Cloudflare JSON configs from KCL | 01 |
| 03 | [terraform-deployment-functions](./03-terraform-deployment-functions.md) | Functions to deploy via Terraform (UniFi, Cloudflare, full pipeline) | 02 |
| 04 | [integration-test-function](./04-integration-test-function.md) | Integration test with ephemeral resources and auto-cleanup | 03 |

## Usage

1. Process prompts in order using the OpenSpec workflow
2. Each prompt builds on the previous one
3. Run `dagger functions` after each change to verify

## Module Naming

- **Repository**: `unifi-cloudflare-glue`
- **Module name**: `unifi-cloudflare-glue` (in `dagger.json`)
- **Class name**: `UnifiCloudflareGlue` (Dagger generates from module name)

## Expected Directory Structure After Completion

```
unifi-cloudflare-glue/
├── dagger.json                 # Dagger module manifest (at repo base)
├── pyproject.toml              # Python project config
├── src/
│   └── unifi_cloudflare_glue/  # Python module
│       ├── __init__.py
│       └── main.py             # Dagger functions
├── sdk/                        # Auto-generated Dagger SDK
├── terraform/                  # Existing Terraform modules
├── kcl/                        # Existing KCL schemas
└── .gitignore                  # Updated for Dagger
```
