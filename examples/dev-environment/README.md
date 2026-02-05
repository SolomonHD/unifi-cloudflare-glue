# Development Environment Example

> **⚠️ NOT FOR PRODUCTION USE**
>
> This example uses ephemeral state and simple environment variable secrets. It is designed for rapid development iteration only. For production deployments, use the [production-environment](../production-environment/) example.

A minimal, fast-setup development environment for testing `unifi-cloudflare-glue` configurations. This example demonstrates rapid iteration with ephemeral state - perfect for learning, experimentation, and pre-commit validation.

## Characteristics

| Aspect | Configuration |
|--------|---------------|
| **State Management** | Ephemeral (no persistence) |
| **Secret Storage** | Environment variables |
| **Cost** | Zero infrastructure costs |
| **Setup Time** | < 5 minutes |
| **Team Sharing** | Not supported |
| **Best For** | Solo development, testing, learning |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Edit KCL  │────▶│   Deploy    │────▶│   Test      │       │
│  │  Config     │     │  (ephemeral)│     │             │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         ▲                                    │                   │
│         └────────────────────────────────────┘                   │
│                   (destroy & repeat)                             │
│                                                                  │
│  State: Lives only in container (no persistence)                 │
│  Secrets: Loaded from .env file                                  │
│  Cost: $0 (no backend infrastructure)                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## When to Use This Pattern

### ✅ Good For

- **Learning**: First-time users exploring `unifi-cloudflare-glue`
- **Rapid iteration**: Testing configuration changes quickly
- **Pre-commit validation**: Verifying KCL syntax before committing
- **Experimentation**: Trying different service configurations
- **Proof of concept**: Demonstrating the tool to team members
- **Solo development**: Single developer working on a project

### ❌ Not Suitable For

- **Production workloads**: No state persistence, no locking
- **Team collaboration**: No shared state
- **Long-running infrastructure**: State lost on container exit
- **Compliance requirements**: Environment variables are less secure than secret managers

## Prerequisites

1. [Dagger](https://docs.dagger.io/install) installed
2. [KCL](https://kcl-lang.io/docs/user_docs/getting-started/install) installed (optional, for local validation)
3. UniFi Controller with API access
4. Cloudflare account with API token
5. A device with a known MAC address

## Quick Start

### 1. Configure Environment

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

### 2. Customize KCL Configuration

Edit [`kcl/main.k`](kcl/main.k) and replace placeholders:

```kcl
# Line 24: Your device's MAC address
mac_address = "aa:bb:cc:dd:ee:ff"

# Line 47: Your test domain
public_hostname = "dev.example.com"

# Line 62: Your UniFi Controller host
host = "unifi.internal.lan"

# Line 76: Your Cloudflare zone
zone_name = "example.com"

# Line 79: Your Cloudflare account ID
account_id = "your-account-id"
```

### 3. Validate Configuration

```bash
# Download dependencies (first time only)
kcl mod update

# Validate KCL syntax
kcl run kcl/main.k
```

### 4. Deploy

```bash
# Make scripts executable
chmod +x deploy.sh destroy.sh

# Deploy infrastructure
./deploy.sh
```

### 5. Test

```bash
# Test internal DNS
nslookup dev-app.internal.lan

# Test external access (after cloudflared is configured)
curl https://dev.example.com
```

### 6. Clean Up

```bash
# Destroy all resources
./destroy.sh
```

## File Structure

```
dev-environment/
├── README.md           # This file
├── kcl.mod            # KCL module manifest
├── .env.example       # Environment variable template
├── deploy.sh          # Deployment script
├── destroy.sh         # Destruction script
└── kcl/
    └── main.k         # KCL configuration
```

## Scripts Reference

### deploy.sh

Deploys infrastructure with ephemeral state.

```bash
# Deploy
./deploy.sh

# Preview changes (plan only)
./deploy.sh --plan
```

### destroy.sh

Destroys all infrastructure.

```bash
# Destroy with confirmation
./destroy.sh

# Destroy without confirmation
./destroy.sh --force
```

## Understanding Ephemeral State

In this development environment, Terraform state is **not persisted**:

```
┌─────────────────┐
│   Dagger Call   │
│   (container)   │
│                 │
│  ┌───────────┐  │
│  │ Terraform │  │
│  │  State    │  │  ◄── Only lives here
│  │ (in-mem)  │  │
│  └───────────┘  │
└─────────────────┘
         │
         ▼
   Container exits
         │
         ▼
   State is lost
```

**Implications:**
- ✅ Fast deployment (no backend to configure)
- ✅ Safe experimentation (can't corrupt shared state)
- ✅ Zero cost (no S3/DynamoDB)
- ❌ Must destroy from same session (can't resume later)
- ❌ Not for production (no state history)

## Security Considerations

### Environment Variables

This example uses `.env` files for secrets:

```bash
# .env (never commit this!)
CF_TOKEN=your-cloudflare-token
UNIFI_API_KEY=your-unifi-api-key
```

**Security level**: Medium
- Secrets in environment variables are isolated to the process
- Risk of exposure in shell history (mitigated by using `env:` prefix)
- Not suitable for production (use secret managers instead)

### Best Practices

1. **Never commit `.env` files**:
   ```bash
   # Already in .gitignore
echo ".env" >> .gitignore
   ```

2. **Use restricted API tokens**:
   - Cloudflare: Only Zone:Read, DNS:Edit, Cloudflare Tunnel:Edit
   - UniFi: Only read/write DNS permissions

3. **Rotate credentials regularly**:
   ```bash
   # Cloudflare: Create new token, update .env, revoke old token
   # UniFi: Regenerate API key, update .env
   ```

## Customization

### Adding More Services

Edit `kcl/main.k` to add additional services:

```kcl
services = [
    unifi.Service {
        name = "dev-app"
        port = 8080
        protocol = "http"
        distribution = "both"
        internal_hostname = "dev-app.internal.lan"
        public_hostname = "dev.example.com"
    }
    # Add more services here
    unifi.Service {
        name = "api"
        port = 3000
        protocol = "http"
        distribution = "cloudflare_only"
        internal_hostname = "api.internal.lan"
        public_hostname = "api-dev.example.com"
    }
]
```

### Using Test Domains

For development, use subdomains:

```kcl
# Instead of production domains:
# public_hostname = "app.example.com"

# Use test domains:
public_hostname = "dev-app.example.com"
# or
public_hostname = "staging-app.example.com"
```

### Enabling HTTPS in Development

The configuration allows self-signed certificates:

```kcl
# In CloudflareConfig
default_no_tls_verify = True

# In TunnelService
no_tls_verify = True
```

**Remember**: Set to `False` for production!

## Troubleshooting

### "dagger: command not found"

Install Dagger:
```bash
curl -L https://dl.dagger.io/dagger/install.sh | sh
sudo mv bin/dagger /usr/local/bin/
```

### "kcl: command not found"

Install KCL:
```bash
curl -sSL https://kcl-lang.io/script/install-cli.sh | bash
```

### "Error: missing environment variable"

Ensure `.env` file exists and contains all required variables:
```bash
# Check file exists
ls -la .env

# Verify contents
cat .env
```

### KCL Import Errors

Download dependencies:
```bash
cd kcl
kcl mod update
```

### Deployment Fails

Check credentials:
```bash
# Test Cloudflare token
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CF_TOKEN"

# Test UniFi connectivity
# (Use UniFi API directly or check controller logs)
```

## Migration to Staging/Production

When ready to move beyond development:

| From | To | Action |
|------|-----|--------|
| Ephemeral state | Persistent state | Add `--state-dir` or remote backend |
| .env secrets | Secret manager | Use [vals](../production-environment/) with 1Password/AWS Secrets Manager |
| Test domains | Production domains | Update `public_hostname` values |
| Self-signed certs | Valid certs | Set `no_tls_verify = False` |

See:
- [Staging Environment](../staging-environment/) for team collaboration
- [Production Environment](../production-environment/) for full security

## Next Steps

- **[Staging Environment](../staging-environment/)**: Add persistent state for team collaboration
- **[Production Environment](../production-environment/)**: Production-grade security with secret management
- **[KCL Guide](../../docs/kcl-guide.md)**: Complete KCL reference
- **[Dagger Reference](../../docs/dagger-reference.md)**: All available functions

## License

MIT - Part of the `unifi-cloudflare-glue` project.