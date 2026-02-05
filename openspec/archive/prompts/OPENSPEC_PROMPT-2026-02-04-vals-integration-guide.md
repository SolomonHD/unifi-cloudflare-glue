# OpenSpec Prompt: vals + 1Password Integration Documentation

## Context

The project supports YAML backend configuration files for Terraform state management, but lacks documentation on integrating with secret management tools like vals and 1Password. Users need to inject secrets securely into backend configurations without committing credentials to version control.

## Goal

Create comprehensive documentation for using vals with 1Password (and other secret backends) to generate YAML backend configuration files with secrets injected at runtime.

## Scope

### In Scope

1. Create [`docs/vals-integration.md`](../../docs/vals-integration.md) with complete workflows
2. Add 1Password integration examples
3. Add examples for other vals backends:
   - AWS Secrets Manager
   - Azure Key Vault
   - GCP Secret Manager
   - HashiCorp Vault
4. Create example template files in [`examples/backend-configs/`](../../examples/backend-configs/):
   - `s3-backend-1password.yaml.tmpl`
   - `azurerm-backend-1password.yaml.tmpl`
   - `s3-backend-aws-secrets.yaml.tmpl`
5. Add Makefile example for automated workflow
6. Document security best practices for vals
7. Update main docs index to link to vals guide

### Out of Scope

- Implementation of vals in Dagger module (already supported via YAML)
- Custom vals backends beyond documented ones
- Alternative secret management tools (beyond vals)
- CI/CD-specific vals integration (separate from general usage)

## Desired Behavior

### Documentation Structure: docs/vals-integration.md

```markdown
# vals Integration Guide

## Overview

vals enables secret injection from multiple backends into YAML configuration files.

## Prerequisites

- vals installed
- 1Password CLI (or other backend CLIs)
- Project backend configuration template

## 1Password Integration

### Setup

1. Install tools
2. Authenticate
3. Create 1Password items

### Create Template

```yaml
# backend.yaml.tmpl
bucket: ref+op://Infrastructure/TerraformState/s3-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: ref+op://Infrastructure/TerraformState/aws-region
encrypt: true
use_lockfile: true
```

### Render and Deploy

```bash
vals eval -f backend.yaml.tmpl > backend.yaml
dagger call deploy --backend-config-file=./backend.yaml ...
rm backend.yaml  # Clean up secrets
```

### Automated Workflow

Makefile with automatic cleanup

## Other vals Backends

### AWS Secrets Manager
### Azure Key Vault
### GCP Secret Manager
### HashiCorp Vault

## Security Best Practices

1. Never commit rendered files
2. Add to .gitignore
3. Rotate secrets regularly
4. Use least privilege access
5. Clean up rendered files after use

## Troubleshooting

Common vals errors and solutions
```

### Example Template Files

Create in `examples/backend-configs/`:

#### s3-backend-1password.yaml.tmpl

```yaml
# S3 Backend with 1Password Secret Injection
# Usage: vals eval -f s3-backend-1password.yaml.tmpl > backend.yaml
#
# Required 1Password items:
#   - op://Infrastructure/TerraformState/s3-bucket
#   - op://Infrastructure/TerraformState/aws-region
#   - op://Infrastructure/AWS-Terraform/access-key-id
#   - op://Infrastructure/AWS-Terraform/secret-access-key

bucket: ref+op://Infrastructure/TerraformState/s3-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: ref+op://Infrastructure/TerraformState/aws-region
encrypt: true
use_lockfile: true

# Optional: Static backend access credentials (if not using environment vars)
# access_key: ref+op://Infrastructure/AWS-Terraform/access-key-id
# secret_key: ref+op://Infrastructure/AWS-Terraform/secret-access-key
```

#### s3-backend-aws-secrets.yaml.tmpl

```yaml
# S3 Backend with AWS Secrets Manager Injection
# Usage: vals eval -f s3-backend-aws-secrets.yaml.tmpl > backend.yaml
#
# Requires: AWS CLI configured with appropriate access

bucket: ref+awssecretsmanager://terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: ref+awssecretsmanager://terraform-state-region
encrypt: true
use_lockfile: true
```

### Makefile Example

```makefile
.PHONY: deploy destroy clean-secrets

# Deploy with vals secret injection
deploy:
	@echo "Rendering secrets with vals..."
	@vals eval -f backend.yaml.tmpl > backend.yaml
	@echo "Deploying infrastructure..."
	@dagger call deploy \
		--backend-type=s3 \
		--backend-config-file=./backend.yaml \
		--kcl-source=./kcl \
		--unifi-url=$${UNIFI_URL} \
		--unifi-api-key=env:UNIFI_API_KEY \
		--cloudflare-token=env:CF_TOKEN \
		--cloudflare-account-id=$$(op read "op://Infrastructure/Cloudflare/account-id") \
		--zone-name=$${CF_ZONE}
	@$(MAKE) clean-secrets

# Destroy with vals secret injection
destroy:
	@echo "Rendering secrets with vals..."
	@vals eval -f backend.yaml.tmpl > backend.yaml
	@echo "Destroying infrastructure..."
	@dagger call destroy \
		--backend-type=s3 \
		--backend-config-file=./backend.yaml \
		--kcl-source=./kcl \
		--unifi-url=$${UNIFI_URL} \
		--unifi-api-key=env:UNIFI_API_KEY \
		--cloudflare-token=env:CF_TOKEN \
		--cloudflare-account-id=$$(op read "op://Infrastructure/Cloudflare/account-id") \
		--zone-name=$${CF_ZONE}
	@$(MAKE) clean-secrets

# Clean up rendered secrets
clean-secrets:
	@rm -f backend.yaml
	@echo "Cleaned up rendered secrets"
```

## Constraints & Assumptions

### Constraints

- Focus on vals tool (most popular multi-backend solution)
- Document only officially supported vals backends
- Security examples must follow best practices
- All examples must be tested and working

### Assumptions

- Users have appropriate CLI tools installed
- Users understand their chosen secret backend (1Password, AWS, etc.)
- Users follow principle of least privilege for secret access
- Template files should be committed, rendered files should not

## Acceptance Criteria

- [ ] [`docs/vals-integration.md`](../../docs/vals-integration.md) created with comprehensive guide
- [ ] 1Password workflow fully documented with complete examples
- [ ] AWS Secrets Manager integration documented
- [ ] Azure Key Vault integration documented
- [ ] GCP Secret Manager integration documented
- [ ] HashiCorp Vault integration documented
- [ ] Example template files created in [`examples/backend-configs/`](../../examples/backend-configs/)
- [ ] Makefile example provided with automatic secret cleanup
- [ ] Security best practices section included
- [ ] Troubleshooting section with common vals errors
- [ ] Links added to main README and docs index
- [ ] `.gitignore` updated to exclude rendered files

## Expected Files/Areas Touched

- `docs/vals-integration.md` (new)
- `examples/backend-configs/s3-backend-1password.yaml.tmpl` (new)
- `examples/backend-configs/azurerm-backend-1password.yaml.tmpl` (new)
- `examples/backend-configs/s3-backend-aws-secrets.yaml.tmpl` (new)
- `examples/backend-configs/azurerm-backend-azure-kv.yaml.tmpl` (new)
- `examples/backend-configs/gcs-backend-gcp-secrets.yaml.tmpl` (new)
- `examples/backend-configs/Makefile.example` (new)
- `examples/backend-configs/README.md` (update to reference vals)
- `docs/README.md` (update index)
- `README.md` (add link)
- `.gitignore` (add `*.yaml` in backend-configs if not already present)

## Dependencies

- Prompt 01 (docs structure must exist)

## Notes

- The project already supports YAML backend configs, this adds secret injection workflow
- vals is the de-facto standard for multi-backend secret injection
- Focus on practical, copy-paste examples
- Emphasize security: rendered files contain plaintext secrets
- Makefile pattern is popular for automation with automatic cleanup
