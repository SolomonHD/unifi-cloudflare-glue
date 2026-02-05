# Backend Configuration Examples

This directory contains example configuration files for various Terraform remote backends. These backends enable persistent state storage for production deployments, allowing state to survive container restarts and enabling team collaboration.

## Available Backend Examples

### HCL Format (Traditional)

| File | Backend | Best For |
|------|---------|----------|
| `s3-backend.hcl` | AWS S3 + DynamoDB | AWS environments, most popular option |
| `azurerm-backend.hcl` | Azure Blob Storage | Microsoft Azure environments |
| `gcs-backend.hcl` | Google Cloud Storage | Google Cloud environments |
| `remote-backend.hcl` | Terraform Cloud | Teams wanting managed Terraform |

### YAML Format (vals Integration)

| File | Backend | Best For |
|------|---------|----------|
| `s3-backend.yaml` | AWS S3 + DynamoDB | AWS environments with basic YAML config |
| `azurerm-backend.yaml` | Azure Blob Storage | Azure environments with basic YAML config |
| `gcs-backend.yaml` | Google Cloud Storage | GCP environments with basic YAML config |
| `remote-backend.yaml` | Terraform Cloud | Terraform Cloud with basic YAML config |

### S3 Backend Locking Options (Terraform 1.9+)

| File | Locking Mechanism | Terraform Version | Best For |
|------|-------------------|-------------------|----------|
| `s3-backend-lockfile.yaml` | S3 Native Lockfile | 1.9+ only | Simplest setup, lowest cost |
| `s3-backend-dynamodb.yaml` | DynamoDB Table | All versions | Maximum compatibility, multi-team |

> **Note:** DynamoDB locking is **NOT deprecated**. Both options remain fully supported. See [S3 Locking Options](#s3-locking-options) below for detailed comparison.

### YAML Templates (vals Secret Injection)

| File | Backend | Secret Source |
|------|---------|---------------|
| `s3-backend-1password.yaml.tmpl` | AWS S3 + DynamoDB | 1Password vault |
| `azurerm-backend-1password.yaml.tmpl` | Azure Blob Storage | 1Password vault |
| `s3-backend-aws-secrets.yaml.tmpl` | AWS S3 + DynamoDB | AWS Secrets Manager |
| `azurerm-backend-azure-kv.yaml.tmpl` | Azure Blob Storage | Azure Key Vault |
| `gcs-backend-gcp-secrets.yaml.tmpl` | Google Cloud Storage | GCP Secret Manager |

**Template files use vals for secret injection.** See the [vals Integration Guide](../../docs/vals-integration.md) for complete documentation.

**Note:** YAML files are automatically converted to HCL format by the Dagger module. Both formats are fully supported and can be used interchangeably.

## Quick Start

### Using HCL Format

1. Copy the example file for your chosen backend:
   ```bash
   cp s3-backend.hcl my-backend.hcl
   ```

2. Edit the configuration with your actual values:
   ```bash
   vim my-backend.hcl
   ```

3. Set the required environment variables (see the comments in the HCL file)

4. Deploy with the backend configuration:
   ```bash
   dagger call deploy \
       --backend-type=s3 \
       --backend-config-file=./my-backend.hcl \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com
   ```

### Using YAML Format (vals Integration)

1. Copy the YAML example file:
   ```bash
   cp s3-backend.yaml my-backend.yaml
   ```

2. Edit with your values (YAML is cleaner for secret injection):
   ```bash
   vim my-backend.yaml
   ```

3. Deploy with the YAML backend configuration:
   ```bash
   dagger call deploy \
       --backend-type=s3 \
       --backend-config-file=./my-backend.yaml \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com
   ```

The module automatically converts YAML to HCL format.

## Backend Types Reference

### S3 Backend (`s3`)

Stores state in AWS S3 with optional DynamoDB locking.

**Required Setup:**
- S3 bucket for state storage
- DynamoDB table for state locking (optional but recommended)
- AWS credentials (via environment variables)

**Example Usage:**
```bash
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    ...
```

### S3 Locking Options

AWS S3 backends support two state locking mechanisms. Choose based on your Terraform version and requirements:

| Feature | S3 Native Lockfile | DynamoDB Locking |
|---------|-------------------|------------------|
| **Terraform Version** | 1.9+ only | All versions (1.0+) |
| **Additional Infrastructure** | None (S3 only) | DynamoDB table |
| **Cost** | Lower (S3 only) | ~$0.25/month (DynamoDB table) |
| **Setup Complexity** | Simple | Moderate (table creation) |
| **Stale Lock Cleanup** | Automatic | Manual (`force-unlock`) |
| **Production Maturity** | HashiCorp validated | Battle-tested |
| **Best For** | Simple setups, cost-conscious | Multi-team, complex workflows |

> **Cost Note:** DynamoDB pricing is approximately $0.25/month per table for on-demand capacity. Pricing may vary by region. See [AWS DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/).

**When to use `s3-backend-lockfile.yaml`:**
- You use Terraform 1.9 or later exclusively
- You want the simplest setup with minimal infrastructure
- Cost optimization is a priority
- You don't need advanced lock management features

**When to use `s3-backend-dynamodb.yaml`:**
- You need to support older Terraform versions
- You have complex multi-team coordination requirements
- You prefer battle-tested infrastructure patterns
- You need explicit lock visibility and control

> **Important:** DynamoDB locking is **NOT deprecated**. Both options remain fully supported. The S3 native lockfile is an alternative, not a replacement.

**Quick Start:**
```bash
# S3 Native Lockfile (Terraform 1.9+)
cp s3-backend-lockfile.yaml my-backend.yaml

# DynamoDB Locking (All versions)
cp s3-backend-dynamodb.yaml my-backend.yaml
```

For comprehensive guidance including migration instructions, security best practices, and IAM policies, see the [Backend Configuration Guide](../../docs/backend-configuration.md).

### Azure Blob Storage Backend (`azurerm`)

Stores state in Azure Storage Account blob container.

**Required Setup:**
- Azure Storage Account
- Blob container within the account
- Azure service principal or MSI credentials

**Example Usage:**
```bash
dagger call deploy \
    --backend-type=azurerm \
    --backend-config-file=./azurerm-backend.hcl \
    ...
```

### Google Cloud Storage Backend (`gcs`)

Stores state in Google Cloud Storage bucket.

**Required Setup:**
- GCS bucket with Object Versioning enabled
- Service account with Storage Object Admin role
- GOOGLE_APPLICATION_CREDENTIALS environment variable

**Example Usage:**
```bash
dagger call deploy \
    --backend-type=gcs \
    --backend-config-file=./gcs-backend.hcl \
    ...
```

### Terraform Cloud Backend (`remote`)

Stores state in Terraform Cloud (or Terraform Enterprise).

**Required Setup:**
- Terraform Cloud organization and workspace
- API token (TF_TOKEN_app_terraform_io)

**Example Usage:**
```bash
dagger call deploy \
    --backend-type=remote \
    --backend-config-file=./remote-backend.hcl \
    ...
```

## Security Best Practices

### 1. Never Commit Credentials

Never commit backend configuration files containing real credentials to version control. Use environment variables for sensitive values:

```bash
# Good: Credentials via environment
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Bad: Credentials in HCL file
# access_key = "AKIAIOSFODNN7EXAMPLE"  # DON'T DO THIS
```

### 2. Use Least Privilege

Grant the minimum required permissions to the credentials used for state access:

- **S3**: `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the state bucket
- **DynamoDB**: `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem` on the lock table
- **Azure**: `Storage Blob Data Contributor` on the container
- **GCS**: `roles/storage.objectAdmin` on the bucket

### 3. Enable Encryption

All backend examples include encryption options:

- **S3**: Set `encrypt = true` for server-side encryption
- **Azure**: Storage accounts encrypt by default
- **GCS**: Buckets encrypt by default, or use CMEK for additional control

### 4. State Locking

Always enable state locking to prevent concurrent modifications:

- **S3**: Use `dynamodb_table` parameter
- **Azure**: Native locking (no extra config needed)
- **GCS**: Native locking via Object Versioning
- **Terraform Cloud**: Automatic locking

### 5. State Backup

Even with remote backends, consider periodic state backups:

```bash
# Export state to local file for backup
dagger call deploy ...
terraform state pull > backup-$(date +%Y%m%d).tfstate
```

## Migration from Local to Remote Backend

To migrate existing local state to a remote backend:

1. Ensure your remote backend infrastructure is ready (bucket, table, etc.)

2. Deploy once with the new backend to initialize:
   ```bash
   dagger call deploy \
       --backend-type=s3 \
       --backend-config-file=./s3-backend.hcl \
       ...
   ```

3. Terraform will detect the existing local state and prompt to migrate it to the remote backend

4. Verify the migration:
   ```bash
   # Check that state exists in remote backend
   aws s3 ls s3://my-bucket/unifi-cloudflare-glue/
   ```

## Troubleshooting

### "No state found" Error

When running `destroy`, ensure you use the **same** backend configuration that was used during `deploy`:

```bash
# Deploy with backend
dagger call deploy --backend-type=s3 --backend-config-file=./s3-backend.hcl ...

# Destroy must use same backend
dagger call destroy --backend-type=s3 --backend-config-file=./s3-backend.hcl ...
```

### "Backend configuration changed" Error

If you change backend configuration, Terraform may refuse to proceed. In this case:

1. Run with matching backend to destroy resources
2. Then run with new backend to re-create them

Or manually migrate state:
```bash
terraform init -migrate-state
```

### Permission Denied Errors

Check that your credentials have the required permissions:

- Verify environment variables are set correctly
- Check IAM policies (AWS), RBAC (Azure), or IAM (GCP)
- Ensure the backend resource (bucket, container) exists

## vals Integration with YAML

The YAML format enables seamless integration with `vals` for secret injection. This allows you to reference secrets from AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, and more.

### Example: AWS Secrets Manager with vals

Create a YAML template with vals references:

```yaml
# backend.yaml.tmpl
bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
access_key: ref+awssecretsmanager://terraform-aws-access-key
secret_key: ref+awssecretsmanager://terraform-aws-secret-key
```

Evaluate the template with vals:

```bash
# Install vals if needed: https://github.com/helmfile/vals
vals eval -f backend.yaml.tmpl > backend.yaml
```

Use the rendered YAML:

```bash
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./backend.yaml \
    --kcl-source=./kcl \
    ...
```

### Supported vals Backends

- `ref+awssecretsmanager://` - AWS Secrets Manager
- `ref+azurekeyvault://` - Azure Key Vault
- `ref+gcpsecretsmanager://` - GCP Secret Manager
- `ref+vault://` - HashiCorp Vault
- `ref+ssm://` - AWS SSM Parameter Store
- And more: see [vals documentation](https://github.com/helmfile/vals)

## vals Integration with Makefile Automation

For automated secret management with automatic cleanup, use the [Makefile.example](Makefile.example):

```bash
# Copy the example Makefile
cp Makefile.example Makefile

# Deploy with automatic secret rendering and cleanup
make deploy

# Destroy with automatic secret rendering and cleanup
make destroy
```

The Makefile provides:
- Automatic secret rendering with vals
- 1Password CLI integration for inline account ID injection
- Guaranteed cleanup (even on deployment failure)
- Customizable variables for different backends

See the [vals Integration Guide](../../docs/vals-integration.md) for complete documentation on using vals with various secret backends.

## Template Files Reference

Template files (`.yaml.tmpl`) contain vals references and can be safely committed to version control:

| Template | Backend | Secret Source |
|----------|---------|---------------|
| `s3-backend-1password.yaml.tmpl` | AWS S3 | 1Password |
| `azurerm-backend-1password.yaml.tmpl` | Azure Blob | 1Password |
| `s3-backend-aws-secrets.yaml.tmpl` | AWS S3 | AWS Secrets Manager |
| `azurerm-backend-azure-kv.yaml.tmpl` | Azure Blob | Azure Key Vault |
| `gcs-backend-gcp-secrets.yaml.tmpl` | GCS | GCP Secret Manager |

**Important:** Rendered `.yaml` files contain plaintext secrets and must never be committed. Use `.gitignore` to exclude them.

## Additional Resources

- [Terraform S3 Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
- [Terraform Azure Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/azurerm)
- [Terraform GCS Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/gcs)
- [Terraform Cloud Documentation](https://developer.hashicorp.com/terraform/cloud-docs)
- [vals - Configuration Values](https://github.com/helmfile/vals)
- [vals Integration Guide](../../docs/vals-integration.md) - Complete guide for secret injection
