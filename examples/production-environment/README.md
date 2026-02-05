# Production Environment Example

> **🔒 Production-Grade Security**
>
> This example demonstrates enterprise-grade security with vals secret injection, DynamoDB state locking, and comprehensive access controls. Suitable for production workloads.

A secure, production-ready environment configuration using vals with 1Password for secret management. This example demonstrates the highest level of security for critical infrastructure.

## Characteristics

| Aspect | Configuration |
|--------|---------------|
| **State Management** | S3 backend with DynamoDB locking |
| **Secret Storage** | 1Password via vals |
| **Cost** | ~$5-15/month (S3 + DynamoDB) |
| **Setup Time** | ~30-45 minutes |
| **Security Level** | Enterprise-grade |
| **Best For** | Production workloads, compliance requirements |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   PRODUCTION WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  1Password  │────▶│    vals     │────▶│   Deploy    │       │
│  │   Secrets   │     │   Render    │     │  (S3+DDB)   │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         ▲                                    │                   │
│         └────────────────────────────────────┘                   │
│              (secrets never touch disk)                          │
│                                                                  │
│  State: S3 with versioning and encryption                        │
│  Locking: DynamoDB for concurrent access                         │
│  Secrets: Injected at runtime, never stored                      │
│  Audit: 1Password access logs                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## When to Use This Pattern

### ✅ Good For

- **Production workloads**: Customer-facing services requiring high availability
- **Compliance requirements**: SOC2, HIPAA, PCI-DSS environments
- **Team collaboration**: Multiple operators with audit requirements
- **Secret rotation**: Automated credential rotation without code changes
- **Audit trails**: Complete logs of who accessed what and when

### ❌ Not Suitable For

- **Development**: Over-engineered for rapid iteration
- **Personal projects**: Unnecessary complexity and cost
- **Quick prototypes**: Setup time is longer than other patterns
- **Budget-constrained**: S3 + DynamoDB have ongoing costs

## Prerequisites

1. [Dagger](https://docs.dagger.io/install) installed
2. [KCL](https://kcl-lang.io/docs/user_docs/getting-started/install) installed (optional, for local validation)
3. [vals](https://github.com/helmfile/vals#installation) installed: `brew install vals`
4. [1Password CLI](https://developer.1password.com/docs/cli/get-started/) configured: `op signin`
5. AWS account with S3 and DynamoDB access
6. UniFi Controller with API access
7. Cloudflare account with API token
8. 1Password Business/Enterprise account

## Quick Start

### 1. Install Required Tools

```bash
# Install vals
brew install vals

# Install 1Password CLI
brew install 1password-cli

# Sign in to 1Password
op signin
```

### 2. Create AWS Infrastructure

```bash
# Create S3 bucket for state
aws s3 mb s3://my-terraform-state-bucket --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket my-terraform-state-bucket \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket my-terraform-state-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
  }'

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name terraform-state-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

### 3. Configure 1Password Secrets

See [SECRETS.md](SECRETS.md) for detailed setup. Quick summary:

```bash
# Create vault and items in 1Password
op vault create Infrastructure

op item create --category=SecureNote --vault=Infrastructure \
  --title="terraform-state" \
  bucket="my-terraform-state-bucket" \
  region="us-east-1" \
  dynamodb-table="terraform-state-lock"

op item create --category=APICredential --vault=Infrastructure \
  --title="cloudflare" \
  api-token="your-cloudflare-token"

op item create --category=Password --vault=Infrastructure \
  --title="unifi" \
  api-key="your-unifi-api-key"
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with non-sensitive values
nano .env
```

Required variables (non-sensitive):
- `UNIFI_HOST`: Your UniFi Controller hostname
- `CF_ACCOUNT_ID`: Cloudflare Account ID
- `CF_ZONE_NAME`: Your domain
- `AWS_REGION`: AWS region

### 5. Update Backend Template

Edit [`backend.yaml.tmpl`](backend.yaml.tmpl) and customize the 1Password paths:

```yaml
# Adjust these to match your 1Password vault/item structure
bucket: ref+op://Infrastructure/terraform-state/bucket
region: ref+op://Infrastructure/terraform-state/region
dynamodb_table: ref+op://Infrastructure/terraform-state/dynamodb-table
```

### 6. Customize KCL Configuration

Edit [`kcl/main.k`](kcl/main.k) and replace placeholders:

```kcl
# Line 31: Your production device's MAC address
mac_address = "aa:bb:cc:dd:ee:ff"

# Line 43: Your production domain
public_hostname = "app.example.com"

# Line 93: Your UniFi Controller host
host = "unifi.internal.lan"

# Line 99: Your Cloudflare zone
zone_name = "example.com"

# Line 101: Your Cloudflare account ID
account_id = "your-account-id"
```

### 7. Validate Configuration

```bash
# Download dependencies
kcl mod update

# Validate KCL syntax
kcl run kcl/main.k

# Test vals rendering
vals eval -f backend.yaml.tmpl
```

### 8. Deploy

```bash
# Preview changes
make plan

# Deploy infrastructure
make deploy
```

The Makefile will:
1. Render secrets from 1Password
2. Deploy infrastructure
3. Automatically clean up the rendered `backend.yaml`

### 9. Test

```bash
# Test internal DNS
nslookup production-app.internal.lan

# Test external access
curl https://app.example.com
```

### 10. Clean Up (if needed)

```bash
# Destroy all resources
make destroy

# Clean all generated files
make clean
```

## File Structure

```
production-environment/
├── README.md              # This file
├── SECRETS.md             # 1Password setup guide
├── kcl.mod               # KCL module manifest
├── backend.yaml.tmpl     # vals template (safe to commit)
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore rules (critical!)
├── Makefile              # Deployment automation
└── kcl/
    └── main.k            # KCL configuration
```

**Important**: Never commit `backend.yaml` (the rendered file) - it contains plaintext secrets!

## Security Features

### Automatic Secret Cleanup

The Makefile automatically removes rendered secrets after operations:

```makefile
deploy: render-secrets
	# ... deployment ...
	@$(MAKE) clean-secrets  # Auto-cleanup
```

### No Secrets in Version Control

```bash
# backend.yaml.tmpl (committed) - template only
bucket: ref+op://Infrastructure/terraform-state/bucket

# backend.yaml (NOT committed) - rendered with secrets
bucket: my-actual-bucket-name  # Secret value!
```

### Audit Trail

1Password logs all secret access:
- Who accessed secrets
- When they were accessed
- From which device/IP

### Encryption at Rest

- S3 bucket encryption enabled
- DynamoDB encryption at rest
- TLS for all API communications

## Makefile Targets

### make deploy

Deploy infrastructure with automatic secret cleanup.

```bash
make deploy
```

### make destroy

Destroy all resources with confirmation and cleanup.

```bash
make destroy
```

### make plan

Preview changes without applying.

```bash
make plan
```

### make clean

Remove all generated files and secrets.

```bash
make clean
```

### make status

Show current environment status.

```bash
make status
```

## Security Best Practices

### 1. Use IAM Roles

For AWS authentication, use IAM roles instead of static credentials:

```bash
# On EC2 - attach instance profile
# On ECS - use task role
# On Lambda - use execution role
# Locally - use AWS CLI profiles
export AWS_PROFILE=production
```

### 2. Rotate Secrets Regularly

Set up automated rotation:

```bash
# Cloudflare - rotate every 90 days
# UniFi - rotate API keys every 90 days
# AWS - use IAM role (no rotation needed)
```

### 3. Enable Access Logging

```bash
# Enable CloudTrail for AWS API calls
aws cloudtrail create-trail --name production --s3-bucket-name my-cloudtrail-bucket

# Enable S3 access logging
aws s3api put-bucket-logging --bucket my-terraform-state-bucket ...
```

### 4. Use Least-Privilege Access

Grant minimal permissions:
- S3: Only specific bucket and prefix
- DynamoDB: Only specific table
- Cloudflare: Only required zones
- UniFi: Only DNS management

### 5. Monitor Access

Regularly review:
- 1Password access logs
- AWS CloudTrail logs
- Cloudflare audit logs
- UniFi event logs

## Troubleshooting

### "vals: command not found"

```bash
brew install vals
```

### "op: command not found"

```bash
brew install 1password-cli
op signin
```

### "could not find item"

Verify 1Password items exist:
```bash
op item list --vault Infrastructure
op item get terraform-state --vault Infrastructure
```

### "Error acquiring the state lock"

Check DynamoDB for stuck locks:
```bash
aws dynamodb scan --table-name terraform-state-lock
```

Release stuck lock (use with caution!):
```bash
aws dynamodb delete-item \
  --table-name terraform-state-lock \
  --key '{"LockID": {"S": "my-terraform-state-bucket/unifi-cloudflare-glue/production/terraform.tfstate"}}'
```

### "Access Denied" on S3

Check IAM permissions:
```bash
aws s3 ls s3://my-terraform-state-bucket/
aws s3 ls s3://my-terraform-state-bucket/unifi-cloudflare-glue/production/
```

## Cost Breakdown (AWS us-east-1)

| Service | Cost |
|---------|------|
| S3 Standard (1 GB) | ~$0.023/month |
| S3 API Requests | ~$0.005/1000 requests |
| DynamoDB On-Demand | ~$1.25/million writes, $0.25/million reads |
| **Total** | **~$5-15/month** |

Costs vary based on:
- Number of deployments
- State file size
- Team size (concurrent access)

## Migration from Other Environments

### From Development

```bash
# 1. Copy KCL config
cp ../dev-environment/kcl/main.k kcl/main.k

# 2. Update domains to production
# dev.example.com → app.example.com

# 3. Add backend template
cp backend.yaml.tmpl backend.yaml.tmpl

# 4. Setup 1Password (see SECRETS.md)

# 5. Deploy with make
make deploy
```

### From Staging

```bash
# 1. Update backend from lockfile to DynamoDB
# use_lockfile: true → dynamodb_table: ...

# 2. Move secrets to 1Password
# cp ../staging-environment/backend.yaml backend.yaml.tmpl
# Then add vals references

# 3. Update Makefile targets
# Use production Makefile (has secret cleanup)
```

## Next Steps

- **[SECRETS.md](SECRETS.md)**: Complete 1Password setup guide
- **[vals Integration](../../docs/vals-integration.md)**: Advanced vals usage
- **[Security](../../docs/security.md)**: Comprehensive security practices
- **[State Management](../../docs/state-management.md)**: Backend configuration

## License

MIT - Part of the `unifi-cloudflare-glue` project.
