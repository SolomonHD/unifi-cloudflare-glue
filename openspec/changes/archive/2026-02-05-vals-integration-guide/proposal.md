## Why

The project supports YAML backend configuration files for Terraform state management but lacks documentation on securely injecting secrets from secret management tools. Users currently must commit sensitive credentials (bucket names, access keys, API tokens) to version control or manually manage environment variables, creating security risks and operational inefficiencies. This change adds comprehensive documentation for using vals to inject secrets from 1Password and other backends at runtime, enabling secure, version-control-safe backend configurations.

## What Changes

- Create `docs/vals-integration.md` with complete vals integration workflows
- Add 1Password CLI integration examples with step-by-step setup
- Document integration patterns for AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, and HashiCorp Vault
- Create template files in `examples/backend-configs/` for vals-driven secret injection:
  - `s3-backend-1password.yaml.tmpl`
  - `azurerm-backend-1password.yaml.tmpl`
  - `s3-backend-aws-secrets.yaml.tmpl`
  - `azurerm-backend-azure-kv.yaml.tmpl`
  - `gcs-backend-gcp-secrets.yaml.tmpl`
- Add Makefile example demonstrating automated secret rendering with cleanup
- Document security best practices for vals usage (gitignore patterns, secret rotation, cleanup)
- Update `docs/README.md` and main `README.md` to link to vals guide
- Update `.gitignore` to prevent committing rendered secret files

## Capabilities

### New Capabilities

- `vals-integration`: Documentation for using vals to inject secrets into YAML backend configurations
- `secret-backend-examples`: Template files demonstrating vals usage with multiple secret management backends
- `automated-secret-workflow`: Makefile and script examples for vals secret rendering with automatic cleanup

### Modified Capabilities

- `documentation`: Add vals integration guide to existing documentation structure
- `example-configuration`: Extend backend configuration examples with vals templates

## Impact

**Documentation:**
- New vals integration guide becomes the standard reference for secret management in the project
- Backend configuration examples expanded to cover secure secret injection patterns

**User Workflow:**
- Users can now securely manage backend configurations without committing secrets
- Reduced risk of credential leaks in version control
- Simplified multi-environment deployments with centralized secret management

**Dependencies:**
- Users must install vals CLI tool
- Users must configure their chosen secret backend (1Password CLI, AWS CLI, Azure CLI, gcloud, etc.)
- No changes to project code or Dagger module required (YAML parsing already supported)

**Files Affected:**
- `docs/vals-integration.md` (new)
- `docs/README.md` (link addition)
- `README.md` (link addition)
- `examples/backend-configs/*.yaml.tmpl` (5 new template files)
- `examples/backend-configs/Makefile.example` (new)
- `examples/backend-configs/README.md` (update)
- `.gitignore` (add rendered file exclusions)
