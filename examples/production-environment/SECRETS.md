# Production Secrets Setup

This document describes how to configure 1Password and vals for secure secret management in the production environment.

## Overview

The production environment uses [vals](https://github.com/helmfile/vals) to inject secrets from 1Password into the Terraform backend configuration. This approach ensures:

- **No secrets in version control**: Only templates are committed
- **Automatic secret rotation**: Update 1Password, no code changes needed
- **Audit trail**: 1Password logs access to secrets
- **Team sharing**: Authorized team members can access secrets without sharing files

## Prerequisites

1. **1Password account** with CLI access
2. **vals** installed: `brew install vals` or see [installation guide](https://github.com/helmfile/vals#installation)
3. **1Password CLI** configured: `op signin`

## 1Password Vault Structure

Create a vault named `Infrastructure` (or your preferred name) with the following items:

### Item: terraform-state

**Type**: Secure Note or Login

**Fields**:

| Field | Value | Description |
|-------|-------|-------------|
| `bucket` | `my-terraform-state-bucket` | S3 bucket for state storage |
| `region` | `us-east-1` | AWS region for S3 bucket |
| `dynamodb-table` | `terraform-state-lock` | DynamoDB table for locking |

### Item: cloudflare

**Type**: API Credential or Login

**Fields**:

| Field | Value | Description |
|-------|-------|-------------|
| `api-token` | `your-cloudflare-token` | Cloudflare API token |

### Item: unifi

**Type**: Password or API Credential

**Fields**:

| Field | Value | Description |
|-------|-------|-------------|
| `api-key` | `your-unifi-api-key` | UniFi API key |

### Item: aws (optional)

**Type**: Login (only needed if not using IAM roles)

**Fields**:

| Field | Value | Description |
|-------|-------|-------------|
| `access-key-id` | `AKIA...` | AWS access key ID |
| `secret-access-key` | `secret...` | AWS secret access key |

## vals Syntax Reference

The `backend.yaml.tmpl` uses vals syntax for secret references:

```yaml
# 1Password syntax
ref+op://vault/item/field

# Examples
bucket: ref+op://Infrastructure/terraform-state/bucket
api_token: ref+op://Infrastructure/cloudflare/api-token
```

### Other Secret Managers

If using a different secret manager, adapt the syntax:

**HashiCorp Vault**:
```yaml
bucket: ref+vault://secret/data/terraform-state#/data/bucket
```

**AWS Secrets Manager**:
```yaml
bucket: ref+awssecrets://terraform-state/bucket
```

**Google Secret Manager**:
```yaml
bucket: ref+gcpsecrets://projects/my-project/secrets/terraform-bucket
```

See [vals documentation](https://github.com/helmfile/vals#supported-backends) for more options.

## Setup Instructions

### Step 1: Install Tools

```bash
# Install vals
brew install vals

# Or on Linux
curl -fsSL https://github.com/helmfile/vals/releases/latest/download/vals_$(uname -s)_$(uname -m).tar.gz | tar xz -C /tmp
sudo mv /tmp/vals /usr/local/bin/

# Install 1Password CLI
brew install 1password-cli
```

### Step 2: Configure 1Password

```bash
# Sign in to 1Password
op signin

# Verify access
op vault list
op item list --vault Infrastructure
```

### Step 3: Create Secrets in 1Password

```bash
# Create terraform-state item
op item create --category=SecureNote --vault=Infrastructure \
  --title="terraform-state" \
  bucket="my-terraform-state-bucket" \
  region="us-east-1" \
  dynamodb-table="terraform-state-lock"

# Create cloudflare item
op item create --category=APICredential --vault=Infrastructure \
  --title="cloudflare" \
  api-token="your-cloudflare-api-token"

# Create unifi item
op item create --category=Password --vault=Infrastructure \
  --title="unifi" \
  api-key="your-unifi-api-key"
```

### Step 4: Test vals

```bash
# Render the template
vals eval -f backend.yaml.tmpl

# Should output the rendered YAML with secrets replaced
```

### Step 5: Deploy

```bash
# Deploy with automatic secret cleanup
make deploy
```

The Makefile will:
1. Render secrets from 1Password
2. Deploy infrastructure
3. Automatically clean up the rendered `backend.yaml`

## Security Best Practices

### 1. Use IAM Roles (AWS)

Instead of injecting AWS credentials, use IAM roles:

```bash
# For EC2 instances
# Attach an instance profile with S3/DynamoDB access

# For local development
export AWS_PROFILE=production
```

Remove from `backend.yaml.tmpl`:
```yaml
# Remove these lines if using IAM roles
# access_key: ref+op://Infrastructure/aws/access-key-id
# secret_key: ref+op://Infrastructure/aws/secret-access-key
```

### 2. Enable 1Password Audit Logging

Enable audit logging in your 1Password Business/Enterprise account to track:
- Who accessed secrets
- When they were accessed
- From which devices

### 3. Rotate Credentials Regularly

Set calendar reminders to rotate:
- Cloudflare API tokens (every 90 days)
- UniFi API keys (every 90 days)
- AWS credentials (if using static keys)

```bash
# Update in 1Password
op item edit --vault Infrastructure cloudflare api-token="new-token"

# No code changes needed - next deployment uses new secret
```

### 4. Use Least-Privilege IAM Policies

For the S3 bucket:
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
      "Resource": "arn:aws:s3:::my-terraform-state-bucket/unifi-cloudflare-glue/production/*"
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

For DynamoDB:
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

### 5. Enable S3 Access Logging

```bash
# Create logging bucket
aws s3 mb s3://my-terraform-logs --region us-east-1

# Enable logging on state bucket
aws s3api put-bucket-logging \
  --bucket my-terraform-state-bucket \
  --bucket-logging-status file://logging.json
```

## Troubleshooting

### "vals: command not found"

Install vals:
```bash
brew install vals
```

### "op: command not found"

Install 1Password CLI:
```bash
brew install 1password-cli
```

### "could not find item"

Verify item exists:
```bash
op item list --vault Infrastructure
op item get terraform-state --vault Infrastructure
```

### "permission denied"

Check 1Password vault permissions:
```bash
# Ensure you have access to the vault
op vault user list Infrastructure
```

### Secrets not rendering

Test vals directly:
```bash
# Test single value
vals get ref+op://Infrastructure/terraform-state/bucket

# Test full template
vals eval -f backend.yaml.tmpl
```

## Migration from Environment Variables

If currently using `.env` files, migrate to 1Password:

1. **Export existing secrets** (securely):
   ```bash
   # Don't save this to disk!
   echo $CF_TOKEN
   ```

2. **Create items in 1Password** (see Step 3 above)

3. **Update .env.example** to reference vals:
   ```bash
   # Instead of:
   CF_TOKEN=actual-token
   
   # Use:
   # Run: vals eval -e CF_TOKEN='ref+op://Infrastructure/cloudflare/api-token'
   ```

4. **Test deployment**:
   ```bash
   make deploy
   ```

## Team Onboarding

New team members need:

1. **1Password access**: Add to `Infrastructure` vault
2. **AWS credentials**: Add to appropriate IAM group
3. ** vals installed**: `brew install vals`
4. **1Password CLI configured**: `op signin`

Document in team wiki:
```markdown
## Production Deployment Access

1. Request access to 1Password `Infrastructure` vault
2. Request AWS IAM user/role
3. Install tools: `brew install vals 1password-cli`
4. Configure 1Password CLI: `op signin`
5. Test: `make status`
```

## References

- [vals GitHub](https://github.com/helmfile/vals)
- [1Password CLI Documentation](https://developer.1password.com/docs/cli/)
- [vals Integration Guide](../../docs/vals-integration.md)
