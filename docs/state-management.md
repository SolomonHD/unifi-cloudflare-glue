# State Management

All deployment functions support configurable Terraform state management with three modes to suit different workflows.

## State Management Modes

| Mode | Use Case | Persistence | Best For |
|------|----------|-------------|----------|
| **Ephemeral** (default) | Testing, CI/CD, one-off operations | Container-only, lost on exit | Quick tests, ephemeral environments |
| **Persistent Local** | Solo development | Host filesystem at `./terraform-state` | Iterative development without remote backend setup |
| **Remote Backend** | Production, team collaboration | S3, Azure, GCS, Terraform Cloud | Team environments, production infrastructure |

## Ephemeral State (Default)

By default, Terraform stores state locally in the container:
- State is ephemeral and lost when the container exits
- Suitable for testing and development
- **Warning**: State files may contain sensitive values

No configuration required - this is the default behavior.

## Persistent Local State

For solo development workflows, you can persist Terraform state locally without setting up a remote backend. This provides a middle ground between ephemeral container state (lost on exit) and remote backends (requires cloud credentials and infrastructure).

### Usage

```bash
# Create a directory for state storage
mkdir -p ./terraform-state

# Deploy with persistent local state
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --state-dir=./terraform-state

# Destroy using the same state directory
dagger call destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --state-dir=./terraform-state
```

> **Note:** `--state-dir` and `--backend-type` (remote backend) are **mutually exclusive**. Choose one state management strategy per deployment.

### How It Works

When using `--state-dir`:
1. The specified directory is mounted into the container at `/state`
2. Terraform module files are copied to the state directory
3. Terraform operations run from `/state`, keeping state files and module code together
4. State persists on your host filesystem between runs

### Security Considerations

When using persistent local state:

- **State files may contain sensitive values** (API tokens, passwords)
- **Add your state directory to `.gitignore`** to prevent accidental commits
- **Backup your state directory** regularly - losing it means losing track of your infrastructure
- **No state locking** - avoid concurrent operations from different machines
- Use filesystem permissions to restrict access to the state directory

Example `.gitignore` entries:
```gitignore
# Terraform state files (if using persistent local state)
terraform-state/
*.tfstate
*.tfstate.*
```

## Remote Backends

To use a remote backend, specify the backend type and provide a configuration file:

```bash
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

> **Important:** When using remote backends, you must use the **same backend configuration** for both `deploy` and `destroy` operations.

### Supported Backend Types

- `s3` - AWS S3 with optional DynamoDB locking
- `azurerm` - Azure Blob Storage
- `gcs` - Google Cloud Storage
- `remote` - Terraform Cloud / Terraform Enterprise
- And any other backend supported by Terraform

### Backend Configuration Files

Example configuration files are provided in [`examples/backend-configs/`](../examples/backend-configs/):

- `s3-backend.hcl` - AWS S3 configuration
- `azurerm-backend.hcl` - Azure Blob Storage configuration
- `gcs-backend.hcl` - Google Cloud Storage configuration
- `remote-backend.hcl` - Terraform Cloud configuration

### YAML Backend Config Support

The module now supports YAML format for backend configuration files, enabling seamless integration with secret management tools like `vals`. YAML files are automatically converted to Terraform-compatible HCL format.

#### Why Use YAML?

- **Native vals integration**: YAML works seamlessly with `vals` for secret injection
- **Simpler syntax**: No need to quote strings or handle HCL-specific formatting
- **Backward compatible**: Existing HCL files continue to work unchanged

#### Usage

Pass a YAML file to `--backend-config-file` and it will be automatically converted:

```bash
# Deploy with YAML backend config
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.yaml
```

#### YAML Format

Create your backend config in YAML format:

```yaml
# s3-backend.yaml
bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
```

This is equivalent to the HCL format:

```hcl
# s3-backend.hcl
bucket = "my-terraform-state-bucket"
key    = "unifi-cloudflare-glue/terraform.tfstate"
region = "us-east-1"
encrypt = true
dynamodb_table = "terraform-state-lock"
```

#### Supported YAML Types

| YAML Type | Example | HCL Output |
|-----------|---------|------------|
| String | `bucket: my-bucket` | `bucket = "my-bucket"` |
| Integer | `port: 8080` | `port = 8080` |
| Float | `version: 1.5` | `version = 1.5` |
| Boolean | `encrypt: true` | `encrypt = true` |
| List | `endpoints: ["a", "b"]` | `endpoints = ["a", "b"]` |
| Nested Object | `workspaces: {name: dev}` | `workspaces = { name = "dev" }` |

#### vals Integration Workflow

Use `vals` to inject secrets into your YAML backend config:

```bash
# 1. Create a YAML template with vals references
# s3-backend.yaml.tmpl
bucket: my-terraform-state
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
access_key: ref+awssecretsmanager://terraform-aws-access-key
secret_key: ref+awssecretsmanager://terraform-aws-secret-key

# 2. Use vals to evaluate the template
vals eval -f s3-backend.yaml.tmpl > s3-backend.yaml

# 3. Pass the rendered YAML to the module
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.yaml
```

#### Backward Compatibility

- **HCL files continue to work**: The module auto-detects YAML vs HCL format
- **No API changes**: The `--backend-config-file` parameter works with both formats
- **Graceful fallback**: If YAML parsing fails, the file is treated as HCL

### Backend Examples

#### S3 Backend

```hcl
# s3-backend.hcl
bucket = "my-terraform-state-bucket"
key    = "unifi-cloudflare-glue/terraform.tfstate"
region = "us-east-1"
encrypt = true
dynamodb_table = "terraform-state-lock"
```

**Required Environment Variables:**
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Azure Blob Storage

```hcl
# azurerm-backend.hcl
storage_account_name = "myterraformstate"
container_name       = "terraform-state"
key                  = "unifi-cloudflare-glue/terraform.tfstate"
resource_group_name  = "my-resource-group"
```

**Required Environment Variables:**
```bash
export ARM_CLIENT_ID="your-service-principal-client-id"
export ARM_CLIENT_SECRET="your-service-principal-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"
```

#### Google Cloud Storage

```hcl
# gcs-backend.hcl
bucket = "my-terraform-state-bucket"
prefix = "unifi-cloudflare-glue/terraform"
```

**Required Environment Variables:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### Terraform Cloud

```hcl
# remote-backend.hcl
organization = "my-organization"
workspaces {
  name = "unifi-cloudflare-glue"
}
```

**Required Environment Variable:**
```bash
export TF_TOKEN_app_terraform_io="your-terraform-cloud-api-token"
```

## Backend Validation

The module validates backend configuration and provides clear error messages:

```bash
# Error: Missing config file for remote backend
$ dagger call deploy --backend-type=s3 ...
✗ Failed: Backend type 's3' requires --backend-config-file

# Error: Config file provided but local backend selected
$ dagger call deploy --backend-type=local --backend-config-file=./s3-backend.hcl ...
✗ Failed: --backend-config-file specified but backend_type is 'local'
```

## Security Best Practices

### General Security

- **Never commit credentials** in backend configuration files
- Use **environment variables** for all sensitive values
- Enable **encryption at rest** (supported by all remote backends)
- Use **state locking** to prevent concurrent modifications
- Apply **least privilege** permissions to backend credentials

### State File Cleanup

When using local state, remember to clean up state files if needed:

```bash
# After destroy, clean up any remaining state files
rm -f terraform.tfstate terraform.tfstate.backup
```

See [`examples/backend-configs/README.md`](../examples/backend-configs/README.md) for detailed security guidance.
