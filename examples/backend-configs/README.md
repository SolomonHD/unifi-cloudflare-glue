# Backend Configuration Examples

This directory contains example configuration files for various Terraform remote backends. These backends enable persistent state storage for production deployments, allowing state to survive container restarts and enabling team collaboration.

## Available Backend Examples

| File | Backend | Best For |
|------|---------|----------|
| `s3-backend.hcl` | AWS S3 + DynamoDB | AWS environments, most popular option |
| `azurerm-backend.hcl` | Azure Blob Storage | Microsoft Azure environments |
| `gcs-backend.hcl` | Google Cloud Storage | Google Cloud environments |
| `remote-backend.hcl` | Terraform Cloud | Teams wanting managed Terraform |

## Quick Start

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

## Additional Resources

- [Terraform S3 Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
- [Terraform Azure Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/azurerm)
- [Terraform GCS Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/gcs)
- [Terraform Cloud Documentation](https://developer.hashicorp.com/terraform/cloud-docs)
