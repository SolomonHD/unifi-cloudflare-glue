# Backend Configuration Guide

This guide provides comprehensive information about configuring Terraform remote backends for `unifi-cloudflare-glue`, with a focus on state locking options and best practices.

## Overview

Terraform uses "backends" to store state files. By default, state is stored locally, but for production use and team collaboration, remote backends are essential. Remote backends provide:

- **State persistence**: State survives container restarts and CI/CD pipeline execution
- **Team collaboration**: Multiple users can safely work on the same infrastructure
- **State locking**: Prevents concurrent modifications that could corrupt state
- **Backup and versioning**: Built-in state history and recovery options

This project supports multiple backend types (S3, Azure, GCS, Terraform Cloud) with flexible configuration formats (HCL and YAML).

## S3 Native Lockfile (Terraform 1.9+)

Terraform 1.9+ introduced native state locking support for S3 backends using a lockfile mechanism stored directly in S3. This eliminates the need for a separate DynamoDB table.

### Advantages

- **No additional infrastructure**: No DynamoDB table required, reducing AWS resource overhead
- **Lower cost**: Avoids DynamoDB charges (~$0.25/month per table)
- **Automatic cleanup**: Stale locks are automatically cleaned up by Terraform
- **Simpler setup**: Configure with a single parameter (`use_lockfile: true`)
- **Reduced complexity**: Fewer moving parts in your infrastructure

### Limitations

- **Terraform 1.9+ only**: Not backward compatible with older Terraform versions
- **Newer feature**: Less battle-tested than DynamoDB locking (though thoroughly validated by HashiCorp)
- **Team coordination**: Consider team Terraform version requirements before adopting

### Configuration Example

```yaml
# S3 Backend with Native Lockfile (Terraform 1.9+)
# Requires Terraform >= 1.9.0

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
use_lockfile: true  # Enable S3 native locking
```

### Usage with Dagger

```bash
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend-lockfile.yaml \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

See the complete example in [`examples/backend-configs/s3-backend-lockfile.yaml`](../examples/backend-configs/s3-backend-lockfile.yaml).

## DynamoDB State Locking (Traditional)

DynamoDB state locking is the traditional approach for S3 backend state locking. It uses a DynamoDB table to manage locks, providing robust coordination for team environments.

> **Important**: DynamoDB locking is **NOT deprecated** and remains a fully supported, valid option alongside S3 native lockfile.

### Advantages

- **Universal compatibility**: Works with all Terraform versions (1.0+)
- **Battle-tested**: Years of production use across countless organizations
- **Better for multi-team coordination**: More granular lock management
- **Explicit control**: Manual lock inspection and cleanup when needed

### Limitations

- **Additional infrastructure**: Requires DynamoDB table setup
- **Ongoing cost**: Approximately $0.25/month per table (as of 2024)
- **Manual stale lock cleanup**: Requires `terraform force-unlock` for stuck locks
- **More setup steps**: Must create table with correct primary key schema

### Configuration Example

```yaml
# S3 Backend with DynamoDB Locking
# Compatible with all Terraform versions

bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock  # DynamoDB table name
```

### DynamoDB Table Setup

Create the DynamoDB table with the correct primary key:

```bash
aws dynamodb create-table \
    --table-name terraform-state-lock \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region us-east-1
```

**Table Requirements:**
- Table name: Must match the `dynamodb_table` parameter
- Primary key: `LockID` (String type, HASH key)
- Billing mode: `PAY_PER_REQUEST` recommended for low-volume usage

### Usage with Dagger

```bash
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend-dynamodb.yaml \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

See the complete example in [`examples/backend-configs/s3-backend-dynamodb.yaml`](../examples/backend-configs/s3-backend-dynamodb.yaml).

## Choosing Between S3 Lockfile and DynamoDB

Use this decision tree to choose the right locking mechanism for your use case:

```
┌─────────────────────────────────────────────────────────────┐
│  Start: Choosing Your S3 State Locking Mechanism            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Do you need to support Terraform versions before 1.9?      │
└───────────────────────┬─────────────────────────────────────┘
                        │
           ┌────────────┴────────────┐
           │                         │
           ▼                         ▼
       YES │                    NO │
           │                         │
┌──────────┴──────────┐   ┌─────────┴──────────────────────────┐
│  USE DYNAMODB       │   │  Do you have multi-team            │
│  LOCKING            │   │  coordination requirements?        │
│                     │   │  (complex workflows, strict        │
│  • Universal        │   │  governance needs)                 │
│    compatibility    │   └─────────┬──────────────────────────┘
│  • Battle-tested    │             │
│  • Better for       │    ┌────────┴────────┐
│    complex teams    │    │                 │
└─────────────────────┘    ▼                 ▼
                        YES │           NO │
                            │              │
               ┌────────────┴──┐  ┌────────┴──────────────┐
               │  USE          │  │  USE S3 NATIVE        │
               │  DYNAMODB     │  │  LOCKFILE             │
               │  LOCKING      │  │                       │
               │               │  │  • Simpler setup      │
               │  • Granular   │  │  • Lower cost         │
               │    control    │  │  • No extra infra     │
               │  • Explicit   │  │  • Auto cleanup       │
               │    lock mgmt  │  │                       │
               └───────────────┘  └───────────────────────┘
```

### Quick Decision Reference

| Factor | Choose S3 Lockfile | Choose DynamoDB |
|--------|-------------------|-----------------|
| Terraform version | 1.9+ only | Any version |
| Setup simplicity | ⭐⭐⭐ Excellent | ⭐⭐ Good |
| Cost | ⭐⭐⭐ Lower | ⭐⭐ Standard (~$0.25/mo) |
| Multi-team needs | ⭐⭐ Good | ⭐⭐⭐ Excellent |
| Production maturity | ⭐⭐⭐ HashiCorp validated | ⭐⭐⭐ Battle-tested |
| Automatic cleanup | ⭐⭐⭐ Yes | ⭐⭐ Manual |

**Cost Note:** DynamoDB pricing is approximately $0.25/month per table for on-demand capacity in most regions. Pricing may vary by region and usage. Verify current pricing at [AWS DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/).

## Migration from DynamoDB to S3 Lockfile

If you have an existing DynamoDB-based setup and want to migrate to S3 native lockfile, follow these steps.

> **Note**: Migration is completely optional. DynamoDB remains a fully supported option. Only migrate if the benefits align with your needs.

### Prerequisites

- All team members using Terraform 1.9+
- Coordination with team members to avoid concurrent operations
- Backup of existing state (recommended)

### Migration Steps

1. **Verify Terraform version:**
   ```bash
   terraform version
   # Must be 1.9.0 or higher
   ```

2. **Create backup (optional but recommended):**
   ```bash
   # With existing backend configured
   terraform state pull > backup-$(date +%Y%m%d).tfstate
   ```

3. **Update backend configuration:**
   
   Change from:
   ```yaml
   dynamodb_table: terraform-state-lock
   ```
   
   To:
   ```yaml
   use_lockfile: true
   ```

4. **Reinitialize Terraform:**
   ```bash
   terraform init -reconfigure
   ```
   
   The `-reconfigure` flag tells Terraform to reconfigure the backend without migrating state (state stays in S3).

5. **Verify the migration:**
   ```bash
   terraform plan
   # Should show no changes (infrastructure unchanged)
   ```

6. **Test locking:**
   ```bash
   # Run a quick apply to verify locking works
   terraform apply -auto-approve
   ```

7. **Clean up DynamoDB (optional):**
   
   After confirming S3 lockfile works, you can optionally delete the DynamoDB table:
   ```bash
   aws dynamodb delete-table --table-name terraform-state-lock
   ```

### Rollback

If you need to rollback to DynamoDB locking:

1. Restore the `dynamodb_table` parameter in your backend config
2. Run `terraform init -reconfigure`
3. The table must still exist (or be recreated)

## All Backend Types

While this guide focuses on S3 backends and locking options, `unifi-cloudflare-glue` supports multiple backend types:

### AWS S3 (`s3`)

- **Best for**: AWS environments, most common choice
- **Locking options**: S3 native lockfile (1.9+) or DynamoDB
- **State storage**: S3 bucket
- **Example**: [`s3-backend-lockfile.yaml`](../examples/backend-configs/s3-backend-lockfile.yaml)

### Azure Blob Storage (`azurerm`)

- **Best for**: Microsoft Azure environments
- **Locking**: Native locking (no extra config needed)
- **State storage**: Blob container in Storage Account
- **Example**: [`azurerm-backend.hcl`](../examples/backend-configs/azurerm-backend.hcl)

### Google Cloud Storage (`gcs`)

- **Best for**: Google Cloud environments
- **Locking**: Native locking via Object Versioning
- **State storage**: GCS bucket
- **Example**: [`gcs-backend.hcl`](../examples/backend-configs/gcs-backend.hcl)

### Terraform Cloud (`remote`)

- **Best for**: Teams wanting managed Terraform
- **Locking**: Automatic (managed by Terraform Cloud)
- **State storage**: Terraform Cloud workspaces
- **Example**: [`remote-backend.hcl`](../examples/backend-configs/remote-backend.hcl)

### Local Directory (`local`)

- **Best for**: Solo development, testing
- **Locking**: File-based (not suitable for teams)
- **State storage**: Local filesystem
- **Usage**: `--state-dir=./terraform-state`

For detailed configuration of non-S3 backends, see [`examples/backend-configs/README.md`](../examples/backend-configs/README.md).

## Security Best Practices

### Encryption

Always enable encryption for state files:

```yaml
# S3 backend
encrypt: true  # Enables S3 server-side encryption
```

- **S3**: Set `encrypt: true` for server-side encryption
- **Azure**: Storage accounts encrypt by default
- **GCS**: Buckets encrypt by default, with option for customer-managed keys

### Credential Management

**Never commit credentials to version control.** Use environment variables:

```bash
# Good: Credentials via environment
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Bad: Never do this in config files
# access_key: AKIAIOSFODNN7EXAMPLE  # DON'T DO THIS
```

For advanced secret management, use [vals integration](vals-integration.md) with secret backends like AWS Secrets Manager, Azure Key Vault, or 1Password.

### Least Privilege Access

Grant minimum required permissions:

**S3 Backend IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::my-terraform-state-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::my-terraform-state-bucket"
    }
  ]
}
```

**DynamoDB Locking IAM Policy (if using DynamoDB):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/terraform-state-lock"
    }
  ]
}
```

**S3 Native Lockfile IAM Policy (Terraform 1.9+):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::my-terraform-state-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::my-terraform-state-bucket"
    }
  ]
}
```

### State Access Logging

Enable access logging on your state bucket for audit purposes:

```bash
aws s3api put-bucket-logging \
    --bucket my-terraform-state-bucket \
    --bucket-logging-status '{
        "LoggingEnabled": {
            "TargetBucket": "my-logs-bucket",
            "TargetPrefix": "terraform-state-logs/"
        }
    }'
```

### State Backup

Even with remote backends, consider periodic backups:

```bash
# Export state to local file
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./backend.yaml \
    ...

# Pull state for backup
terraform state pull > backup-$(date +%Y%m%d).tfstate
```

## Troubleshooting

### "No state found" Error

When running `destroy`, use the **same** backend configuration as `deploy`:

```bash
# Deploy with backend
dagger call deploy --backend-type=s3 --backend-config-file=./backend.yaml ...

# Destroy must use same backend
dagger call destroy --backend-type=s3 --backend-config-file=./backend.yaml ...
```

### Stale Lock Issues

**DynamoDB:**
```bash
# Force unlock if lock is stuck
terraform force-unlock <LOCK_ID>
```

**S3 Native Lockfile:**
```bash
# Stale locks auto-cleanup, but can force if needed
terraform force-unlock <LOCK_ID>
```

### "Backend configuration changed" Error

If you change backend configuration, Terraform may refuse to proceed:

```bash
# Option 1: Migrate state
terraform init -migrate-state

# Option 2: Reconfigure (state stays in place)
terraform init -reconfigure
```

### Permission Denied Errors

- Verify environment variables are set
- Check IAM policies grant required permissions
- Ensure bucket/table exist in the specified region
- Verify credentials have not expired

## Additional Resources

- [Terraform S3 Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/s3)
- [Terraform Azure Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/azurerm)
- [Terraform GCS Backend Documentation](https://developer.hashicorp.com/terraform/language/settings/backends/gcs)
- [Terraform Cloud Documentation](https://developer.hashicorp.com/terraform/cloud-docs)
- [vals Integration Guide](vals-integration.md)
- [State Management Guide](state-management.md)
- [Security Best Practices](security.md)
