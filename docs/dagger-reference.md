# Dagger Reference

Complete reference for all Dagger functions in the `unifi-cloudflare-glue` module.

## Table of Contents

- [Installation](#installation)
- [Configuration Generation](#configuration-generation)
- [Deployment Functions](#deployment-functions)
- [Plan Generation](#plan-generation)
- [Testing](#testing)
- [Module Calling Patterns](#module-calling-patterns)
- [CI/CD Integration](#cicd-integration)

## Installation

### Installing the Module

```bash
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.3.2
```

### Version Selection

**Production environments should always pin to specific versions:**

- ✅ **Recommended**: Use `@vX.Y.Z` for production (e.g., `@v0.3.2`)
- ⚠️ **Not recommended**: Avoid `@main` in production (unpredictable changes)

**Finding available versions:**

- Check [GitHub releases](https://github.com/SolomonHD/unifi-cloudflare-glue/releases)
- Review [CHANGELOG.md](../CHANGELOG.md) for version changes
- Test new versions in non-production environments first

### Critical: Parameter Differences

> **⚠️ IMPORTANT:** Remote module users must understand the difference between `--source` and `--kcl-source` parameters.

| Parameter | Purpose | When to Use |
|-----------|---------|-------------|
| `--source=.` | Reads the **module's** KCL files | ❌ Only for local development within this repository |
| `--kcl-source=./your-config` | Reads **your project's** KCL files | ✅ Required when using the module remotely |

**Why this matters:**

- Local development (within this repo): `--source=.` works because it reads the module's own KCL schemas
- Remote usage (from your project): You **must** use `--kcl-source=./your-config` to provide your own KCL configuration
- Using `--source=.` remotely will fail or read the wrong files

## Configuration Generation

### `generate-unifi-config`

Generate UniFi JSON configuration from KCL schemas.

```bash
dagger call generate-unifi-config --source=./kcl export --path=./unifi.json
```

### `generate-cloudflare-config`

Generate Cloudflare JSON configuration from KCL schemas.

```bash
dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
```

## Deployment Functions

### `deploy`

Full deployment orchestration (UniFi first, then Cloudflare).

Deploys in the correct order: UniFi DNS first (creates local DNS), then Cloudflare Tunnels (point to now-resolvable hostnames).

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--kcl-source` | ✅ | Path to your KCL configuration directory |
| `--unifi-url` | ✅ | UniFi controller URL (e.g., `https://unifi.local:8443`) |
| `--unifi-api-key` | ✅* | UniFi API key (or use username/password) |
| `--cloudflare-token` | ✅ | Cloudflare API token |
| `--cloudflare-account-id` | ✅ | Cloudflare account ID |
| `--zone-name` | ✅ | DNS zone name (e.g., `example.com`) |
| `--unifi-insecure` | ❌ | Skip TLS verification (for self-signed certs) |
| `--terraform-version` | ❌ | Terraform version (default: "latest") |
| `--kcl-version` | ❌ | KCL version (default: "latest") |
| `--state-dir` | ❌ | Path for persistent local state |

*Use `--unifi-api-key` OR (`--unifi-username` AND `--unifi-password`)

**Examples:**

```bash
# Basic deployment
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com

# With self-signed certificates
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://192.168.10.1 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --unifi-insecure

# With persistent local state
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --state-dir=./terraform-state

# With pinned versions
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --terraform-version=1.10.0 \
    --kcl-version=0.11.0
```

### `deploy-unifi`

Deploy only UniFi DNS configuration.

**Authentication options (pick one):**
1. API Key (recommended): `--unifi-api-key`
2. Username/Password: Both `--unifi-username` and `--unifi-password`

**TLS options:**
- `--unifi-insecure` - Skip TLS certificate verification

**Examples:**

```bash
# Using API key (recommended)
dagger call -m unifi-cloudflare-glue deploy-unifi \
    --source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

# Using username/password
dagger call -m unifi-cloudflare-glue deploy-unifi \
    --source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-username=env:UNIFI_USER \
    --unifi-password=env:UNIFI_PASS

# With self-signed certificates
dagger call -m unifi-cloudflare-glue deploy-unifi \
    --source=./kcl \
    --unifi-url=https://192.168.10.1 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-insecure

# With persistent local state
dagger call -m unifi-cloudflare-glue deploy-unifi \
    --source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --state-dir=./terraform-state
```

### `deploy-cloudflare`

Deploy only Cloudflare Tunnel configuration.

**Examples:**

```bash
# Basic usage
dagger call -m unifi-cloudflare-glue deploy-cloudflare \
    --source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com

# With persistent local state
dagger call -m unifi-cloudflare-glue deploy-cloudflare \
    --source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --state-dir=./terraform-state
```

### `destroy`

Destroy all resources (Cloudflare first, then UniFi).

**⚠️ DESTRUCTIVE OPERATION:** Destroys in reverse order to avoid DNS loops.

**Examples:**

```bash
# Basic destruction
dagger call -m unifi-cloudflare-glue destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com

# With persistent local state (must use same state-dir as deploy)
dagger call -m unifi-cloudflare-glue destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --state-dir=./terraform-state
```

## Plan Generation

### `plan`

Generate Terraform plans without applying changes. Creates execution plans enabling the standard plan → review → apply workflow.

**Output formats per module:**
- Binary plan files (for `terraform apply`)
- JSON (for automation)
- Human-readable text (for review)

**Examples:**

```bash
# Basic usage - export plans to ./plans directory
dagger call -m unifi-cloudflare-glue plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --unifi-api-key=env:UNIFI_API_KEY \
    export --path=./plans

# With persistent local state
dagger call -m unifi-cloudflare-glue plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --unifi-api-key=env:UNIFI_API_KEY \
    --state-dir=./terraform-state \
    export --path=./plans

# With remote backend (S3)
dagger call -m unifi-cloudflare-glue plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --unifi-api-key=env:UNIFI_API_KEY \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    export --path=./plans
```

**Output Directory Structure:**

```
plans/
├── unifi-plan.tfplan      # Binary plan
├── unifi-plan.json        # Structured JSON
├── unifi-plan.txt         # Human-readable
├── cloudflare-plan.tfplan # Binary plan
├── cloudflare-plan.json   # Structured JSON
├── cloudflare-plan.txt    # Human-readable
└── plan-summary.txt       # Aggregated summary
```

**Security Note:** Plan files may contain sensitive values. Add your plans directory to `.gitignore`.

## Testing

### `test-integration`

Run integration tests with ephemeral resources against live APIs.

**Parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `--source` | ✅ | Path to KCL configuration |
| `--cloudflare-zone` | ✅ | Test zone (e.g., `test.example.com`) |
| `--cloudflare-token` | ✅ | Cloudflare API token |
| `--cloudflare-account-id` | ✅ | Cloudflare account ID |
| `--unifi-url` | ✅ | UniFi controller URL |
| `--api-url` | ✅ | UniFi API URL |
| `--unifi-api-key` | ✅ | UniFi API key |
| `--test-mac-address` | ❌ | Real device MAC (default: "aa:bb:cc:dd:ee:ff") |
| `--no-cache` | ❌ | Bypass Dagger cache |
| `--cache-buster` | ❌ | Custom cache key |

**Examples:**

```bash
# Basic test
dagger call -m unifi-cloudflare-glue test-integration \
    --source=./kcl \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

# Force fresh execution
dagger call -m unifi-cloudflare-glue test-integration \
    --source=./kcl \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --no-cache

# With real MAC address
dagger call -m unifi-cloudflare-glue test-integration \
    --source=./kcl \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --test-mac-address=de:ad:be:ef:12:34
```

### `hello`

Verify the module is working.

```bash
dagger call hello
```

## Module Calling Patterns

### 1. Installed Module Pattern (Recommended for Local Development)

After running `dagger install`, use the module name directly:

```bash
dagger call -m unifi-cloudflare-glue <function-name> \
    --kcl-source=./your-config \
    <other-parameters>
```

**Pros:**
- Shorter commands
- Persistent across terminal sessions
- Cleaner for iterative development

**Cons:**
- Requires initial `dagger install` step
- Version managed in `dagger.json`

### 2. Direct Remote Pattern (Recommended for CI/CD)

Call the module directly without installation:

```bash
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.3.2 \
    unifi-cloudflare-glue <function-name> \
    --kcl-source=./your-config \
    <other-parameters>
```

**Pros:**
- No installation required
- Explicit version control in command
- Ideal for CI/CD pipelines

**Cons:**
- Longer commands
- Must repeat full URL each time

### Pattern Comparison

| Aspect | Installed Module | Direct Remote |
|--------|-----------------|---------------|
| **Command Length** | Short (`-m unifi-cloudflare-glue`) | Long (full URL + module name) |
| **Installation** | Required (`dagger install`) | Not required |
| **Versioning** | In `dagger.json` | In command (`@v0.3.2`) |
| **Best For** | Local development, iteration | CI/CD, one-off operations |

## CI/CD Integration

### Version Pinning Best Practices

**⚠️ ALWAYS use specific version tags (`@vX.Y.Z`) in production environments.**

**Benefits:**
- **Reproducibility**: Same version = same behavior
- **Predictability**: No unexpected breaking changes
- **Safety**: Test changes before upgrading

**Example GitHub Actions workflow:**

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

**Key CI/CD patterns:**

- Use **direct remote pattern** (no installation step)
- **Pin versions** for reproducibility
- Store **secrets in CI environment variables**
- Use **ephemeral state** or remote backend

### Adapting to Other CI Systems

This pattern works with any CI system (GitLab CI, CircleCI, Jenkins, etc.):

1. Install Dagger CLI
2. Set environment variables for secrets
3. Call module using direct remote pattern
4. Use appropriate state management

See [Dagger CI integration docs](https://docs.dagger.io/integrations/ci) for platform-specific guidance.

## Additional Resources

- **KCL configuration examples**: See [`examples/homelab-media-stack/`](../examples/homelab-media-stack/)
- **Function signatures**: Run `dagger functions` to list all available functions
- **Parameter details**: Use `dagger call <function> --help`
- **KCL language guide**: [KCL Documentation](https://kcl-lang.io/)
