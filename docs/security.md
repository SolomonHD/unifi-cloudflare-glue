# Security Best Practices

This guide covers security best practices for using `unifi-cloudflare-glue`, including credential handling, authentication methods, and CI/CD security.

## Credential Handling

All sensitive credentials are handled using Dagger's `Secret` type, which ensures:
- Secrets are never logged to console output
- Secrets are not stored in command history
- Secrets are passed securely to containers via environment variables

### Environment Variable Pattern

Always pass secrets via environment variables using the `env:` prefix:

```bash
# ✅ Correct - uses environment variable
dagger call deploy-unifi \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-url=https://unifi.local:8443

# ❌ Incorrect - never pass secrets directly on command line
dagger call deploy-unifi \
    --unifi-api-key="actual-secret-value" \
    --unifi-url=https://unifi.local:8443
```

### Required Environment Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `UNIFI_API_KEY` | UniFi API key (recommended) | `deploy-unifi`, `deploy`, `destroy` |
| `UNIFI_USER` | UniFi username (alternative) | `deploy-unifi`, `deploy`, `destroy` |
| `UNIFI_PASS` | UniFi password (alternative) | `deploy-unifi`, `deploy`, `destroy` |
| `CF_TOKEN` | Cloudflare API token | `deploy-cloudflare`, `deploy`, `destroy` |

## Authentication Methods

### UniFi Authentication (Choose One)

#### 1. API Key (Recommended)

More secure, single token authentication.

```bash
export UNIFI_API_KEY="your-api-key"
dagger call deploy-unifi --unifi-api-key=env:UNIFI_API_KEY ...
```

#### 2. Username/Password

Traditional authentication method.

```bash
export UNIFI_USER="admin"
export UNIFI_PASS="password"
dagger call deploy-unifi \
    --unifi-username=env:UNIFI_USER \
    --unifi-password=env:UNIFI_PASS ...
```

> **Note**: You cannot use both methods simultaneously. The module will reject ambiguous authentication configurations.

## Terraform State Security

### Local State (Default)

By default, Terraform stores state locally in the container:
- State is ephemeral and lost when the container exits
- Suitable for testing and development
- **Warning**: State files may contain sensitive values

### Remote State (Recommended for Production)

For production use, configure remote state backend:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "unifi-cloudflare/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

See [State Management](state-management.md) for detailed backend configuration.

### State File Cleanup

When using local state, remember to clean up state files if needed:

```bash
# After destroy, clean up any remaining state files
rm -f terraform.tfstate terraform.tfstate.backup
```

## CI/CD Security

When using in CI/CD pipelines:

1. **Store secrets in CI environment variables** (not in code)
2. **Use short-lived tokens** when possible
3. **Rotate credentials regularly**
4. **Enable audit logging** on UniFi and Cloudflare
5. **Restrict API token permissions** to minimum required

### Cloudflare Token Permissions

Your Cloudflare API token should have:
- Zone:Read
- DNS:Edit
- Cloudflare Tunnel:Edit

### UniFi API Key Permissions

Your UniFi API key should have:
- Administrator role (or custom with network management)

### Example GitHub Actions Security

```yaml
name: Deploy Infrastructure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install Dagger
        uses: dagger/dagger-for-github@v5
        with:
          install-only: true
      
      - name: Deploy with Dagger module
        run: |
          dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.3.2 \
            unifi-cloudflare-glue deploy \
            --kcl-source=./kcl \
            --unifi-url=${{ secrets.UNIFI_URL }} \
            --unifi-api-key=env:UNIFI_API_KEY \
            --cloudflare-token=env:CF_TOKEN \
            --cloudflare-account-id=${{ secrets.CF_ACCOUNT_ID }} \
            --zone-name=${{ secrets.CF_ZONE }}
        env:
          UNIFI_API_KEY: ${{ secrets.UNIFI_API_KEY }}
          CF_TOKEN: ${{ secrets.CF_TOKEN }}
```

## Network Security

- Use HTTPS URLs for UniFi controller (`https://unifi.local:8443`)
- Verify TLS certificates in production
- Consider VPN or private networking for UniFi access
- Firewall rules should restrict UniFi controller access

### Self-Signed Certificates

For development environments with self-signed certificates, use the `--unifi-insecure` flag:

```bash
dagger call deploy-unifi \
    --unifi-url=https://192.168.10.1 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-insecure
```

> **Warning**: Only use `--unifi-insecure` in development/trusted network environments.

## Backend Configuration Security

### Never Commit Credentials

Keep credentials out of your configuration files:

```hcl
# ❌ Don't do this
bucket = "my-bucket"
access_key = "AKIAIOSFODNN7EXAMPLE"  # NEVER commit this
secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"  # NEVER commit this
```

```hcl
# ✅ Use environment variables instead
bucket = "my-bucket"
# access_key and secret_key come from env vars
```

### Use vals for Secret Injection

Consider using [vals](https://github.com/helmfile/vals) for secret management:

```yaml
# backend-config.yaml.tmpl
bucket: my-terraform-state
access_key: ref+awssecretsmanager://terraform-aws-access-key
secret_key: ref+awssecretsmanager://terraform-aws-secret-key
```

See [State Management](state-management.md) for the complete vals integration workflow.

## Security Checklist

- [ ] All secrets passed via `env:` prefix, not directly
- [ ] Cloudflare token has minimum required permissions
- [ ] UniFi API key has appropriate role
- [ ] State files not committed to git (in `.gitignore`)
- [ ] Remote state encryption enabled
- [ ] State locking enabled for team environments
- [ ] Credentials rotated regularly
- [ ] Audit logging enabled on UniFi and Cloudflare
- [ ] HTTPS used for all URLs
- [ ] `--unifi-insecure` only used in development
