# Staging Environment Example

> **Team Collaboration Environment**
>
> This example demonstrates a staging environment with remote state storage for team collaboration. State is persisted in S3 with locking support for safe concurrent operations.

A staging environment configuration for team-based pre-production testing. This example uses S3 backend with native lockfile (Terraform 1.9+) for state persistence and coordination among multiple team members.

## Characteristics

| Aspect | Configuration |
|--------|---------------|
| **State Management** | S3 backend with lockfile |
| **Secret Storage** | Environment variables |
| **Cost** | Minimal (~$0.50-2/month for S3) |
| **Setup Time** | ~15 minutes |
| **Team Sharing** | Full support |
| **Best For** | Pre-production testing, team validation |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAGING WORKFLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Edit KCL  │────▶│   Commit    │────▶│   Deploy    │       │
│  │  Config     │     │   to Git    │     │  (S3 state) │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         ▲                                    │                   │
│         └────────────────────────────────────┘                   │
│                   (team iteration)                               │
│                                                                  │
│  State: Stored in S3 bucket (shared)                             │
│  Locking: S3 native lockfile                                     │
│  Secrets: Loaded from .env file                                  │
│  Cost: S3 storage + requests                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## When to Use This Pattern

### ✅ Good For

- **Team collaboration**: Multiple developers working on infrastructure
- **Pre-production validation**: Testing before production deployment
- **CI/CD pipelines**: Shared state for automated deployments
- **Staging environments**: Long-running non-production infrastructure
- **Integration testing**: Stable environment for external integration tests

### ❌ Not Suitable For

- **Local development**: Use [dev-environment](../dev-environment/) for faster iteration
- **Production workloads**: Use [production-environment](../production-environment/) for enhanced security
- **Single developer**: S3 backend adds unnecessary complexity for solo work
- **Temporary testing**: State cleanup required when done

## Prerequisites

1. [Dagger](https://docs.dagger.io/install) installed
2. [KCL](https://kcl-lang.io/docs/user_docs/getting-started/install) installed (optional, for local validation)
3. AWS account with S3 access
4. UniFi Controller with API access
5. Cloudflare account with API token
6. A device with a known MAC address

## Quick Start

### 1. Configure AWS Credentials

Ensure AWS credentials are configured for S3 backend access:

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="us-east-1"

# Option 2: AWS CLI profile
aws configure --profile staging
export AWS_PROFILE=staging
```

### 2. Create S3 Bucket

```bash
# Create bucket for Terraform state
aws s3 mb s3://my-terraform-state-bucket --region us-east-1

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
  --bucket my-terraform-state-bucket \
  --versioning-configuration Status=Enabled
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or your preferred editor
```

Required variables:
- `UNIFI_HOST`: Your UniFi Controller hostname
- `CF_TOKEN`: Cloudflare API token
- `CF_ACCOUNT_ID`: Cloudflare Account ID
- `CF_ZONE_NAME`: Your domain (e.g., `example.com`)
- `AWS_*`: AWS credentials for S3 backend

### 4. Update Backend Configuration

Edit [`backend.yaml`](backend.yaml) and update:

```yaml
# Line 13: Your S3 bucket name
bucket: my-terraform-state-bucket

# Line 14: State file path (customize as needed)
key: unifi-cloudflare-glue/staging/terraform.tfstate

# Line 15: Your AWS region
region: us-east-1
```

### 5. Customize KCL Configuration

Edit [`kcl/main.k`](kcl/main.k) and replace placeholders:

```kcl
# Line 31: Your device's MAC address
mac_address = "aa:bb:cc:dd:ee:ff"

# Line 45: Your staging domain
public_hostname = "staging.example.com"

# Line 82: Your UniFi Controller host
host = "unifi.internal.lan"

# Line 99: Your Cloudflare zone
zone_name = "example.com"

# Line 101: Your Cloudflare account ID
account_id = "your-account-id"
```

### 6. Validate Configuration

```bash
# Download dependencies (first time only)
kcl mod update

# Validate KCL syntax
kcl run kcl/main.k
```

### 7. Deploy

```bash
# Preview changes
make plan

# Deploy infrastructure
make deploy
```

### 8. Test

```bash
# Test internal DNS
nslookup staging-app.internal.lan

# Test external access
curl https://staging.example.com
```

### 9. Clean Up

```bash
# Destroy all resources
make destroy

# Clean local files
make clean
```

## File Structure

```
staging-environment/
├── README.md           # This file
├── kcl.mod            # KCL module manifest
├── backend.yaml       # S3 backend configuration
├── .env.example       # Environment variable template
├── .gitignore         # Git ignore rules
├── Makefile           # Deployment automation
└── kcl/
    └── main.k         # KCL configuration
```

## Makefile Targets

### make deploy

Deploy infrastructure with S3 backend state.

```bash
make deploy
```

This will:
1. Validate KCL configuration
2. Initialize Terraform with S3 backend
3. Apply changes with state locking

### make destroy

Destroy all infrastructure.

```bash
make destroy
```

### make plan

Preview changes without applying.

```bash
make plan
```

### make clean

Remove local generated files.

```bash
make clean
```

## Understanding S3 State Management

In this staging environment, Terraform state is stored in S3:

```
┌─────────────────┐
│   Team Member 1 │
│   (local)       │
│                 │
│  ┌───────────┐  │
│  │ Terraform │──┼──┐
│  │  Client   │  │  │
│  └───────────┘  │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌─────────────────┐
│   Team Member 2 │  │    │     AWS S3      │
│   (local)       │  │    │                 │
│                 │  │    │  ┌───────────┐  │
│  ┌───────────┐  │  └───▶│  │ Terraform │  │
│  │ Terraform │──┼──────▶│  │  State    │  │
│  │  Client   │  │       │  │  File     │  │
│  └───────────┘  │       │  └───────────┘  │
└─────────────────┘       │                 │
                          └─────────────────┘
```

**Benefits:**
- ✅ Team members share state
- ✅ State locking prevents conflicts
- ✅ State versioning with S3
- ✅ Works across CI/CD pipelines

## State Locking

This example uses S3 native lockfile (Terraform 1.9+):

```yaml
# backend.yaml
use_lockfile: true  # Enable S3 native locking
```

If you need DynamoDB locking (older Terraform versions):

```yaml
# Uncomment DynamoDB line, comment out use_lockfile
dynamodb_table: terraform-state-lock
```

## Security Considerations

### Environment Variables

This example uses `.env` files for secrets:

```bash
# .env (never commit this!)
CF_TOKEN=your-cloudflare-token
UNIFI_API_KEY=your-unifi-api-key
AWS_ACCESS_KEY_ID=your-aws-key
```

**Security level**: Medium
- Secrets in environment variables are isolated to the process
- AWS credentials should use IAM roles when possible (EC2/ECS/Lambda)
- Consider upgrading to [production-environment](../production-environment/) for secret manager integration

### Best Practices

1. **Never commit sensitive files**:
   ```bash
   # Already in .gitignore:
   # - .env
   # - backend.yaml (if rendered from template)
   # - *.tfstate*
   ```

2. **Use restricted API tokens**:
   - Cloudflare: Zone:Read, DNS:Edit, Cloudflare Tunnel:Edit
   - UniFi: Read/write DNS permissions only
   - AWS: S3 access to specific bucket only

3. **Enable S3 bucket versioning**:
   ```bash
   aws s3api put-bucket-versioning \
     --bucket my-bucket \
     --versioning-configuration Status=Enabled
   ```

4. **Encrypt state at rest**:
   ```yaml
   # backend.yaml
   encrypt: true  # Already enabled in this example
   ```

## Customization

### Adding Team Members

Each team member needs:
1. AWS credentials with S3 access
2. `.env` file with appropriate secrets
3. Same `backend.yaml` configuration

### Multiple Staging Environments

For multiple staging environments (e.g., staging-qa, staging-demo):

```bash
# Copy the example
cp -r staging-environment staging-qa

# Update backend.yaml
key: unifi-cloudflare-glue/staging-qa/terraform.tfstate

# Update KCL domains
public_hostname = "qa.example.com"
```

### Using GCS or Azure

For Google Cloud Storage:
```yaml
# backend.yaml for GCS
bucket: my-terraform-state-bucket
prefix: unifi-cloudflare-glue/staging
```

For Azure Blob Storage, see the [backend configuration documentation](../../docs/backend-configuration.md).

## Troubleshooting

### "Error: S3 bucket does not exist"

Create the bucket:
```bash
aws s3 mb s3://my-terraform-state-bucket --region us-east-1
```

### "Error: Access Denied"

Check AWS credentials:
```bash
aws s3 ls s3://my-terraform-state-bucket/
```

Ensure IAM user/role has:
- `s3:GetObject`, `s3:PutObject` on the state bucket
- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the lockfile (if using lockfile)
- `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem` (if using DynamoDB)

### "Error acquiring the state lock"

If a lock is stuck:
```bash
# List locks
aws s3 ls s3://my-terraform-state-bucket/unifi-cloudflare-glue/staging/

# Manually remove (use with caution!)
aws s3 rm s3://my-terraform-state-bucket/unifi-cloudflare-glue/staging/terraform.tfstate.tflock
```

### KCL Import Errors

Download dependencies:
```bash
cd kcl
kcl mod update
```

## Migration

### From Development Environment

| From | To | Action |
|------|-----|--------|
| Ephemeral state | S3 backend | Create `backend.yaml`, update commands |
| Local only | Team | Share S3 bucket, document `.env` setup |
| Test domains | Staging domains | Update `public_hostname` values |

### To Production Environment

| From | To | Action |
|------|-----|--------|
| Environment variables | Secret manager | Adopt [vals](../production-environment/) with 1Password |
| Lockfile locking | DynamoDB locking | Update `backend.yaml` |
| Basic security | Full security | Review [production-environment](../production-environment/) |

## Next Steps

- **[Development Environment](../dev-environment/)**: Fast iteration for local development
- **[Production Environment](../production-environment/)**: Production-grade security
- **[Backend Configuration](../../docs/backend-configuration.md)**: Complete backend options
- **[State Management](../../docs/state-management.md)**: State management patterns

## License

MIT - Part of the `unifi-cloudflare-glue` project.
