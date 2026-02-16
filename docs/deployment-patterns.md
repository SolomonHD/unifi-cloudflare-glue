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

## Deployment Type Patterns

Beyond environment-specific configurations (dev/staging/production), you can also choose what infrastructure components to deploy:

| Pattern | Command | Use Case |
|---------|---------|----------|
| **Full Deployment** | `dagger call deploy` | Deploy both UniFi DNS and Cloudflare Tunnels |
| **UniFi-Only** | `dagger call deploy --unifi-only` | Deploy only UniFi DNS records |
| **Cloudflare-Only** | `dagger call deploy --cloudflare-only` | Deploy only Cloudflare Tunnels |

These patterns are independent of the environment (dev/staging/production) and can be combined with any state management approach.

### Full Deployment Pattern

The default and recommended pattern for most use cases. Deploys both UniFi DNS and Cloudflare Tunnels in the correct order.

**Command:**
```bash
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com
```

**When to Use:**
- Services need both local (UniFi) and remote (Cloudflare) access
- Standard homelab media server setup
- Full hybrid DNS infrastructure

**How It Works:**
The unified Terraform module deploys both providers in a single operation:
1. UniFi DNS records are created first (enables local resolution)
2. Cloudflare Tunnels are created second (point to now-resolvable local hostnames)

This combined approach simplifies the workflow and eliminates provider conflicts that existed with separate deployments.

### UniFi-Only Deployment Pattern

Deploy only UniFi DNS records without creating Cloudflare Tunnels.

**Command:**
```bash
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only
```

**Required Parameters:**
- `--kcl-source` - Path to KCL configuration
- `--unifi-url` - UniFi controller URL
- `--unifi-api-key` - UniFi API key (or username/password)

**When to Use:**
- Internal-only services that don't need remote access
- Local network services (NAS, internal dashboards)
- Services behind VPN only
- Testing UniFi DNS configuration before adding Cloudflare

**Considerations:**
- Services will only be accessible from the local network
- No remote access via Cloudflare Tunnel
- Simpler configuration with fewer credentials needed

### Cloudflare-Only Deployment Pattern

Deploy only Cloudflare Tunnels without modifying UniFi DNS.

**Command:**
```bash
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --cloudflare-only
```

**Required Parameters:**
- `--kcl-source` - Path to KCL configuration
- `--cloudflare-token` - Cloudflare API token
- `--cloudflare-account-id` - Cloudflare account ID
- `--zone-name` - DNS zone name

**When to Use:**
- UniFi DNS is already configured manually or by another tool
- Migrating existing services to Cloudflare Tunnels
- Testing Cloudflare configuration separately

> **⚠️ DNS Loop Prevention Warning:** When using Cloudflare-only deployment, ensure your `local_service_url` values in KCL use internal domain names that are already resolvable via UniFi DNS (or another DNS system). If UniFi DNS is not configured, Cloudflare Tunnel will fail to resolve local hostnames.
>
> **Example:**
> - ✅ Good: `local_service_url: "http://jellyfin.internal.lan:8096"` (resolvable via existing UniFi DNS)
> - ❌ Bad: `local_service_url: "http://192.168.1.50:8096"` (bypasses DNS, may cause issues)

### Selective Deployment Comparison

| Aspect | Full | UniFi-Only | Cloudflare-Only |
|--------|------|------------|-----------------|
| **UniFi DNS Created** | ✅ | ✅ | ❌ |
| **Cloudflare Tunnels Created** | ✅ | ❌ | ✅ |
| **Local Access** | ✅ | ✅ | ✅* |
| **Remote Access** | ✅ | ❌ | ✅ |
| **Credentials Needed** | Both | UniFi only | Cloudflare only |

*Requires existing DNS resolution (UniFi or otherwise)

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

## Cache Control

Dagger's caching is extremely aggressive and operates at multiple levels (function results, container operations, and directory hashes). When working with remote infrastructure (Terraform backends, APIs), you may need to bypass caching to ensure fresh execution.

### Understanding Dagger's Caching

Dagger caches based on:
1. **Function-level**: Function code + input parameter values → cached result
2. **Container-level**: Container state (image, mounts, env vars, commands) → cached layer  
3. **Directory-level**: Directory content hash → cached directory object

### Bypassing Cache with Explicit Timestamps

The `--cache-buster` parameter accepts a unique string value that forces fresh execution by changing the cache key:

```bash
# Force fresh execution with current timestamp
dagger call -m unifi-cloudflare-glue test-integration \
    --source=./kcl \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cache-buster=$(date +%s)
```

The `$(date +%s)` shell substitution provides a unique Unix epoch timestamp (seconds since January 1, 1970) on each invocation. Because the value is different every second, it creates a unique cache key that forces Dagger to execute the function fresh rather than returning a cached result.

### When to Use Cache Busting

Use `--cache-buster=$(date +%s)` when:
- Running integration tests against live APIs/services
- External state (remote Terraform backend, APIs) may have changed
- Deploying infrastructure that exists outside Dagger's cache
- Debugging intermittent issues that might be cache-related
- You need deterministic re-execution without code changes

### When NOT to Use Cache Busting

Don't use cache busting for:
- Deterministic operations (same inputs → same outputs)
- Build operations where caching improves speed
- Development workflows where cache is beneficial
- Operations that don't interact with external mutable state

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
