# Deployment Patterns

This guide describes three environment-specific deployment patterns for `unifi-cloudflare-glue`, each designed for different stages of infrastructure maturity and team collaboration needs.

## Overview

Choosing the right deployment pattern is crucial for balancing security, cost, and operational complexity. This guide helps you select and implement the appropriate pattern for your use case.

| Pattern | State | Secrets | Cost | Best For |
|---------|-------|---------|------|----------|
| **Development** | Ephemeral | Environment variables | $0 | Solo development, learning |
| **Staging** | S3 + lockfile | Environment variables | ~$2-5/month | Team collaboration, pre-production |
| **Production** | S3 + DynamoDB | 1Password/vals | ~$5-15/month | Production workloads, compliance |

## Quick Comparison

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ENVIRONMENT PROGRESSION                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Dev          →      Staging         →       Production              │
│  ───               ────────                  ───────────             │
│  • Ephemeral        • S3 backend            • S3 + DynamoDB          │
│  • No cost          • Lockfile              • Full locking           │
│  • Solo work        • Team sharing          • Enterprise security    │
│  • Fast iteration   • Minimal cost          • Secret management      │
│                                                                      │
│  Complexity & Security Increase →                                    │
└──────────────────────────────────────────────────────────────────────┘
```

## Development Environment

The development environment prioritizes speed and simplicity over persistence and collaboration.

### Characteristics

| Aspect | Configuration |
|--------|---------------|
| **State Management** | Ephemeral (container-only) |
| **Secret Storage** | Environment variables |
| **Cost** | $0 (no backend infrastructure) |
| **Setup Time** | < 5 minutes |
| **Team Sharing** | Not supported |

### When to Use

**Good for:**
- Learning `unifi-cloudflare-glue`
- Testing configuration changes
- Pre-commit validation
- Rapid iteration on KCL
- Solo development

**Not suitable for:**
- Production workloads
- Team collaboration
- Long-running infrastructure

### Deployment Commands

```bash
cd examples/dev-environment/

# Configure
cp .env.example .env
# Edit .env with your credentials

# Deploy
./deploy.sh

# Destroy
./destroy.sh
```

### Security Considerations

- Secrets in `.env` file (never commit!)
- State lost after container exit
- No audit trail
- Suitable for non-sensitive development only

See [Development Environment Example](../examples/dev-environment/) for complete setup.

## Staging Environment

The staging environment adds state persistence and team collaboration while keeping costs minimal.

### Characteristics

| Aspect | Configuration |
|--------|---------------|
| **State Management** | S3 with native lockfile |
| **Secret Storage** | Environment variables |
| **Cost** | ~$2-5/month (S3 only) |
| **Setup Time** | ~15 minutes |
| **Team Sharing** | Full support |

### When to Use

**Good for:**
- Pre-production testing
- Team collaboration
- CI/CD pipelines
- Integration testing
- Long-running non-production infrastructure

**Not suitable for:**
- Production workloads (missing enterprise security features)
- Rapid iteration (backend setup required)

### Deployment Commands

```bash
cd examples/staging-environment/

# Configure
cp .env.example .env
# Edit .env and backend.yaml

# Deploy
make deploy

# Destroy
make destroy
```

### Security Considerations

- Secrets still in `.env` file
- State persists in S3 (encrypted)
- Lockfile prevents concurrent modifications
- Versioned state with S3

See [Staging Environment Example](../examples/staging-environment/) for complete setup.

## Production Environment

The production environment provides enterprise-grade security with secret management and robust state locking.

### Characteristics

| Aspect | Configuration |
|--------|---------------|
| **State Management** | S3 with DynamoDB locking |
| **Secret Storage** | 1Password via vals |
| **Cost** | ~$5-15/month (S3 + DynamoDB) |
| **Setup Time** | ~30-45 minutes |
| **Security Level** | Enterprise-grade |

### When to Use

**Good for:**
- Production workloads
- Compliance requirements (SOC2, HIPAA)
- Audit trail requirements
- Secret rotation needs
- Multi-operator teams

**Not suitable for:**
- Development/learning
- Budget-constrained projects
- Quick prototypes

### Deployment Commands

```bash
cd examples/production-environment/

# Configure 1Password (see SECRETS.md)
op item create ...

# Configure
cp .env.example .env
# Edit .env (non-sensitive values only)

# Deploy (automatic secret cleanup)
make deploy

# Destroy
make destroy
```

### Security Considerations

- Secrets in 1Password (never touch disk)
- Automatic secret cleanup after deployment
- Audit trail via 1Password
- Encryption at rest (S3 + DynamoDB)
- Least-privilege IAM policies

See [Production Environment Example](../examples/production-environment/) for complete setup.

## Environment Comparison

### Feature Matrix

| Feature | Dev | Staging | Production |
|---------|-----|---------|------------|
| State persistence | ❌ | ✅ S3 | ✅ S3 |
| State locking | ❌ | ✅ Lockfile | ✅ DynamoDB |
| Team collaboration | ❌ | ✅ | ✅ |
| Secret management | ❌ .env | ❌ .env | ✅ 1Password |
| Audit logging | ❌ | ❌ | ✅ |
| Encryption at rest | N/A | ✅ S3 | ✅ S3 + DynamoDB |
| Versioned state | ❌ | ✅ | ✅ |
| Automatic secret cleanup | ❌ | ❌ | ✅ |
| Infrastructure cost | $0 | ~$2-5/mo | ~$5-15/mo |
| Setup complexity | Low | Medium | High |

### Use Case Matrix

| Use Case | Recommended |
|----------|-------------|
| Learning/testing | Dev |
| Solo development | Dev |
| Pre-production testing | Staging |
| Team collaboration | Staging |
| CI/CD pipelines | Staging |
| Production workloads | Production |
| Compliance requirements | Production |
| Multi-team shared infrastructure | Production |

## Best Practices

### Secret Handling

**Development:**
```bash
# .env file (gitignored)
CF_TOKEN=your-token
# Never commit this file!
```

**Staging:**
```bash
# Same as dev - plan migration to 1Password
# Consider staging a "pre-production" practice environment
```

**Production:**
```bash
# Use vals for secret injection
vals eval -e CF_TOKEN='ref+op://Infrastructure/cloudflare/api-token'
# Secrets never touch disk in plaintext
```

### Testing Progression

Follow this progression for safe infrastructure changes:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Development │────▶│   Staging    │────▶│  Production  │
│  ──────────  │     │  ──────────  │     │  ──────────  │
│  • Test KCL  │     │  • Team review│     │  • Final     │
│  • Validate  │     │  • Integration│     │    deployment│
│  • Iterate   │     │  • Check state│     │  • Monitor   │
└──────────────┘     └──────────────┘     └──────────────┘
      5 min                15 min               45 min
```

### State Management Best Practices

1. **Never mix environments**: Use separate S3 prefixes for each environment
   ```yaml
   # Dev: no backend (ephemeral)
   # Staging:
   key: unifi-cloudflare-glue/staging/terraform.tfstate
   # Production:
   key: unifi-cloudflare-glue/production/terraform.tfstate
   ```

2. **Enable versioning**: Always enable S3 versioning for state buckets
   ```bash
   aws s3api put-bucket-versioning \
     --bucket my-terraform-state \
     --versioning-configuration Status=Enabled
   ```

3. **Locking is mandatory**: For any shared environment, always use locking
   ```yaml
   # Staging: lockfile (simpler)
   use_lockfile: true
   
   # Production: DynamoDB (more robust)
   dynamodb_table: terraform-state-lock
   ```

### Security Checklist

**All Environments:**
- [ ] `.env` files in `.gitignore`
- [ ] Restricted API tokens (least privilege)
- [ ] TLS for all connections

**Staging & Production:**
- [ ] S3 bucket encryption
- [ ] S3 versioning enabled
- [ ] State locking configured
- [ ] IAM policies least-privilege

**Production Only:**
- [ ] 1Password vault for secrets
- [ ] vals installed and configured
- [ ] DynamoDB for state locking
- [ ] Audit logging enabled
- [ ] Automatic secret cleanup in Makefile
- [ ] Regular credential rotation scheduled

## Example Setup Workflows

### New Developer Onboarding

```bash
# 1. Start with dev environment
cd examples/dev-environment/
cp .env.example .env
# Edit .env

# 2. Deploy and experiment
./deploy.sh
./destroy.sh

# 3. Move to staging when ready for team collaboration
cd ../staging-environment/
# ... set up staging ...
```

### CI/CD Pipeline

```yaml
# Use staging pattern for CI/CD
stages:
  - validate
  - plan
  - deploy

validate:
  script:
    - cd examples/staging-environment/
    - make validate

plan:
  script:
    - cd examples/staging-environment/
    - make plan

deploy:
  script:
    - cd examples/staging-environment/
    - make deploy
```

### Production Deployment

```bash
# 1. Set up 1Password
op vault create Infrastructure
# ... create items ...

# 2. Configure production
cd examples/production-environment/
cp .env.example .env

# 3. Deploy with secret management
make deploy  # Automatically cleans secrets
```

## Troubleshooting by Environment

### Development

**"State not found"**: Expected - state is ephemeral. Use `./destroy.sh` from same session.

**"Missing environment variable"**: Check `.env` file exists and is sourced.

### Staging

**"S3 access denied"**: Check AWS credentials and IAM policies.

**"Lockfile exists"**: Another team member is deploying. Wait or investigate.

### Production

**"vals: command not found"**: Install vals: `brew install vals`

**"could not find item"**: Check 1Password vault and item names match `backend.yaml.tmpl`.

**"DynamoDB lock timeout"**: Check table exists and IAM has DynamoDB access.

## Migration Guide

### Dev → Staging

```bash
# 1. Copy config
cp -r dev-environment/ staging-environment/

# 2. Add backend.yaml
cat > backend.yaml <<EOF
bucket: my-state-bucket
key: staging/terraform.tfstate
region: us-east-1
use_lockfile: true
EOF

# 3. Add Makefile
# Copy from examples/staging-environment/Makefile

# 4. Update deployment commands
./deploy.sh → make deploy
```

### Staging → Production

```bash
# 1. Copy config
cp -r staging-environment/ production-environment/

# 2. Convert backend.yaml to template
mv backend.yaml backend.yaml.tmpl

# 3. Add vals references
# bucket: my-bucket → bucket: ref+op://Infrastructure/state/bucket

# 4. Add SECRETS.md and update Makefile
# Copy from examples/production-environment/

# 5. Set up 1Password
# Follow SECRETS.md instructions
```

## Next Steps

- **[Development Environment](../examples/dev-environment/)**: Get started quickly
- **[Staging Environment](../examples/staging-environment/)**: Add team collaboration
- **[Production Environment](../examples/production-environment/)**: Enterprise security
- **[State Management](state-management.md)**: Deep dive into state backends
- **[vals Integration](vals-integration.md)**: Secret injection guide
- **[Security](security.md)**: Comprehensive security practices

## See Also

- [Backend Configuration](backend-configuration.md): All backend options
- [Getting Started](getting-started.md): First-time setup
- [Troubleshooting](troubleshooting.md): Common issues
