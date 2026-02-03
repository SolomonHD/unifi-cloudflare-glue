# OpenSpec Prompt: Add Remote Backend Configuration Support

## Context

The Dagger deployment functions (`deploy_unifi`, `deploy_cloudflare`, `deploy`) currently use ephemeral local Terraform state that is lost when containers exit. This works well for testing and CI/CD but doesn't support production workflows requiring persistent state management via remote backends (S3, Azure Blob, GCS, Terraform Cloud, etc.).

Users who need persistent state currently must:
1. Use Terraform directly (bypassing Dagger functions)
2. Manually configure backend blocks
3. Lose the benefits of containerized, reproducible deployments

The Dagger functions should support remote backends while maintaining their zero-local-installation philosophy.

## Goal

Add optional remote backend configuration support to all Terraform deployment functions, allowing users to specify a backend type and mount a configuration file containing backend settings and credentials.

## Scope

### In Scope

- Add `backend_type` parameter to deployment functions (default: "local")
- Add `backend_config_file` parameter for mounting HCL configuration files
- Generate Terraform backend blocks dynamically based on backend_type
- Use `terraform init -backend-config=FILE` pattern for configuration
- Add validation to ensure backend_config_file is required when backend_type != "local"
- Update these functions:
  - `deploy_unifi` in src/main/main.py
  - `deploy_cloudflare` in src/main/main.py
  - `deploy` in src/main/main.py (orchestration function)
  - `destroy` in src/main/main.py (cleanup function)
- Add documentation in README.md with examples for S3, Azure, GCS, Terraform Cloud
- Add examples of backend configuration files

### Out of Scope

- Direct parameter-based backend configuration (too many backend-specific options)
- Built-in credential management for backends (use env vars/IAM roles)
- State migration tooling (users can run `terraform init -migrate-state` if needed)
- Persistent local state directory (covered in separate prompt)
- Changes to test_integration function (uses ephemeral state by design)
- Changes to Terraform modules (backend-agnostic)

## Desired Behavior

### Function Signatures

Add two new parameters to deployment functions:

```python
@function
async def deploy_cloudflare(
    self,
    source: Annotated[Directory, Doc("Source directory containing cloudflare.json")],
    cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token")],
    cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
    zone_name: Annotated[str, Doc("DNS zone name (e.g., example.com)")],
    terraform_version: Annotated[str, Doc("Terraform version to use")] = "latest",
    
    # NEW: Backend configuration parameters
    backend_type: Annotated[str, Doc(
        "Terraform backend type: local, s3, azurerm, gcs, http, remote, etc. "
        "Default 'local' uses ephemeral container-local state. "
        "See https://developer.hashicorp.com/terraform/language/settings/backends/configuration"
    )] = "local",
    backend_config_file: Annotated[Optional[File], Doc(
        "Path to HCL file containing backend configuration (required when backend_type != 'local'). "
        "File should contain backend settings but NOT the backend block itself. "
        "Example for S3: bucket, key, region, encrypt, dynamodb_table. "
        "Credentials should be provided via environment variables or IAM roles."
    )] = None,
) -> str:
```

### Validation Logic

```python
# Validate backend configuration
if backend_type != "local" and backend_config_file is None:
    return (
        f"✗ Failed: Backend type '{backend_type}' requires --backend-config-file.\n"
        "Provide an HCL file with backend configuration.\n"
        "Example: --backend-config-file=./s3-backend.hcl"
    )

if backend_type == "local" and backend_config_file is not None:
    return (
        "✗ Failed: --backend-config-file specified but backend_type is 'local'.\n"
        "Either:\n"
        "  1. Remove --backend-config-file (use ephemeral local state)\n"
        "  2. Set --backend-type=s3 (or another remote backend type)"
    )
```

### Implementation Pattern

```python
# After creating Terraform container and mounting module...

# 1. Generate backend block if using remote backend
if backend_type != "local":
    backend_hcl = f"""
terraform {{
  backend "{backend_type}" {{}}
}}
"""
    ctr = ctr.with_new_file("/module/backend.tf", backend_hcl)
    report_lines.append(f"  ✓ Configured {backend_type} backend")

# 2. Mount backend config file
if backend_config_file:
    ctr = ctr.with_file("/root/.terraform/backend.hcl", backend_config_file)
    init_cmd = ["terraform", "init", "-backend-config=/root/.terraform/backend.hcl"]
    report_lines.append("  ✓ Mounted backend configuration")
else:
    init_cmd = ["terraform", "init"]

# 3. Run terraform init with backend config
try:
    init_result = await ctr.with_exec(init_cmd).stdout()
    report_lines.append("  ✓ Terraform init completed")
except dagger.ExecError as e:
    return f"✗ Failed: Terraform init failed\n{str(e)}"
```

### Example Backend Configuration Files

Users create these locally and mount them:

**s3-backend.hcl:**
```hcl
bucket         = "my-terraform-state"
key            = "unifi-cloudflare/cloudflare.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "terraform-locks"

# Credentials via environment variables:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# Or use IAM role attached to execution environment
```

**azurerm-backend.hcl:**
```hcl
resource_group_name  = "terraform-state-rg"
storage_account_name = "tfstate"
container_name       = "tfstate"
key                  = "unifi-cloudflare.tfstate"

# Credentials via environment variables:
# ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_TENANT_ID, ARM_SUBSCRIPTION_ID
```

**gcs-backend.hcl:**
```hcl
bucket  = "my-terraform-state"
prefix  = "unifi-cloudflare"

# Credentials via environment variable:
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

**remote-backend.hcl (Terraform Cloud):**
```hcl
organization = "my-org"

workspaces {
  name = "unifi-cloudflare-prod"
}

# Credentials via environment variable:
# TF_TOKEN_app_terraform_io=<token>
```

### Usage Examples

**Ephemeral local state (default - no change):**
```bash
dagger call deploy-cloudflare \
    --source=. \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

**S3 backend:**
```bash
# Create s3-backend.hcl with bucket/key/region
# Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

dagger call deploy-cloudflare \
    --source=. \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

**Azure Blob Storage backend:**
```bash
# Create azurerm-backend.hcl with storage account details
# Set ARM_CLIENT_ID, ARM_CLIENT_SECRET, ARM_TENANT_ID, ARM_SUBSCRIPTION_ID

dagger call deploy-cloudflare \
    --source=. \
    --backend-type=azurerm \
    --backend-config-file=./azurerm-backend.hcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

**Terraform Cloud backend:**
```bash
# Create remote-backend.hcl with organization/workspace
# Set TF_TOKEN_app_terraform_io=<token>

dagger call deploy-cloudflare \
    --source=. \
    --backend-type=remote \
    --backend-config-file=./remote-backend.hcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

## Constraints & Assumptions

- Backend configuration files do NOT include the `backend {}` block itself - only the settings
- Credentials are provided via environment variables or cloud provider IAM/managed identity
- The implementation is backend-agnostic - Terraform CLI handles all backend-specific logic
- Users upgrading from ephemeral to remote backend may need to run `terraform init -migrate-state` manually
- Remote backends typically provide automatic state locking
- The destroy function must use the same backend configuration as deploy
- Backend configuration files should not contain sensitive credentials directly (use env var references)

## Acceptance Criteria

- [ ] `backend_type` parameter added to `deploy_unifi`, `deploy_cloudflare`, `deploy`, `destroy`
- [ ] `backend_config_file` parameter added to same functions
- [ ] Validation ensures `backend_config_file` required when `backend_type != "local"`
- [ ] Validation prevents `backend_config_file` when `backend_type == "local"`
- [ ] Backend block dynamically generated as `backend.tf` when `backend_type != "local"`
- [ ] Backend config file mounted at `/root/.terraform/backend.hcl` when provided
- [ ] `terraform init` uses `-backend-config` flag when backend config file provided
- [ ] Error messages clearly explain validation failures and provide examples
- [ ] README.md updated with:
  - State management section explaining three modes (ephemeral, remote)
  - Example backend configuration files for S3, Azure, GCS, Terraform Cloud
  - Usage examples for each backend type
  - Credential management guidance (environment variables, IAM roles)
- [ ] CHANGELOG.md updated with new feature
- [ ] All four affected functions work consistently with backend configuration
- [ ] Backwards compatibility maintained (default behavior unchanged)

## Expected Files Modified

- `src/main/main.py` - Add parameters and implementation to 4 functions
- `README.md` - Add "State Management" section with backend examples
- `CHANGELOG.md` - Document new feature
- `examples/backend-configs/` (new directory) - Example HCL files for common backends

## Dependencies

None - this is a self-contained enhancement to existing deployment functions.

## Notes

- This prompt is part 1 of 2 for state management improvements
- Part 2 (separate prompt) adds persistent local state directory support with mutual exclusion
- The implementation should be identical across all four deployment functions to maintain consistency
- Consider adding helper function to reduce duplication: `_configure_backend(ctr, backend_type, backend_config_file)`
