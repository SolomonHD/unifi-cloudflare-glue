# OpenSpec Change Prompt

## Context

The unifi-cloudflare-glue Dagger module currently supports Terraform backend configuration via HCL files (`.hcl` format) passed through the `--backend-config-file` parameter. Users who want to inject secrets using tools like `vals` (which works natively with YAML) must either:
1. Convert YAML to HCL manually
2. Use complex templating workarounds

This creates friction when integrating with modern secret management workflows.

## Goal

Add automatic YAML-to-Terraform-backend-config conversion support that:
- Detects YAML format automatically (content-based detection)
- Converts YAML to Terraform's `.tfbackend` format
- Properly handles all Terraform backend config value types (strings, numbers, booleans, lists, objects)
- Maintains backward compatibility with existing HCL files
- Enables seamless vals integration for secret injection

## Scope

**In scope:**
- Add YAML parsing capability to the Dagger module (Python's `yaml` library)
- Implement `_process_backend_config()` helper method that:
  - Attempts to parse backend config file as YAML
  - Converts YAML structure to Terraform `.tfbackend` HCL syntax
  - Falls back to treating file as HCL if YAML parsing fails
  - Returns tuple of (content, extension) for mounting
- Handle all Terraform backend config data types:
  - Strings (with proper quoting)
  - Numbers (no quotes)
  - Booleans (`true`/`false` literals)
  - Lists (HCL list syntax: `["item1", "item2"]`)
  - Objects/Maps (HCL object syntax: `{ key = "value" }`)
  - Nested structures
- Update all functions that use `backend_config_file` parameter to use the new helper
- Add comprehensive docstring examples showing YAML usage
- Update tests to cover YAML backend configs

**Out of scope:**
- Changing the existing parameter name or API
- Supporting YAML features that don't map to Terraform backend configs (anchors, custom tags, etc.)
- Validating that the YAML structure matches specific backend requirements (S3, Azure, GCS, etc.)
- Automatically running `vals` (users still run `vals eval` externally)

## Desired Behavior

### YAML Input Example
```yaml
# backend-config.yaml (S3 example)
bucket: "my-terraform-state"
key: "unifi-cloudflare/terraform.tfstate"
region: "us-east-1"
dynamodb_table: "terraform-locks"
encrypt: true
kms_key_id: "arn:aws:kms:us-east-1:123456789:key/abc"
skip_region_validation: false
workspace_key_prefix: "environments"
```

### Generated .tfbackend Output
```hcl
bucket                  = "my-terraform-state"
key                     = "unifi-cloudflare/terraform.tfstate"
region                  = "us-east-1"
dynamodb_table          = "terraform-locks"
encrypt                 = true
kms_key_id              = "arn:aws:kms:us-east-1:123456789:key/abc"
skip_region_validation  = false
workspace_key_prefix    = "environments"
```

### Complex Structures

**YAML with lists:**
```yaml
bucket: "my-state"
key: "terraform.tfstate"
allowed_account_ids: ["123456789", "987654321"]
```

**Converts to:**
```hcl
bucket              = "my-state"
key                 = "terraform.tfstate"
allowed_account_ids = ["123456789", "987654321"]
```

**YAML with nested objects:**
```yaml
bucket: "my-state"
key: "terraform.tfstate"
assume_role:
  role_arn: "arn:aws:iam::123456789:role/TerraformRole"
  session_name: "terraform-session"
```

**Converts to:**
```hcl
bucket      = "my-state"
key         = "terraform.tfstate"
assume_role = {
  role_arn     = "arn:aws:iam::123456789:role/TerraformRole"
  session_name = "terraform-session"
}
```

### Backward Compatibility

Existing HCL files continue to work unchanged:
```bash
# Still works exactly as before
dagger call deploy \
  --backend-type=s3 \
  --backend-config-file=./backend.hcl
```

### Integration with Vals

```bash
# 1. Create template with vals references
cat > backend-config.yaml <<EOF
bucket: ref+awsssm://terraform-state-bucket
key: unifi-cloudflare/terraform.tfstate
region: ref+awsssm://aws-region
dynamodb_table: ref+awsssm://terraform-locks-table
EOF

# 2. Resolve secrets with vals
vals eval -f backend-config.yaml > backend.resolved.yaml

# 3. Use with Dagger (auto-converts YAML → .tfbackend)
dagger call deploy \
  --backend-type=s3 \
  --backend-config-file=./backend.resolved.yaml \
  --cloudflare-token=env:CF_TOKEN \
  ...

# 4. Gitignore generated files
