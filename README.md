# unifi-cloudflare-glue

A hybrid DNS infrastructure tool that bridges UniFi network DNS with Cloudflare Tunnel edge DNS. This project enables seamless DNS management across local UniFi networks and Cloudflare's edge infrastructure.

## Purpose

`unifi-cloudflare-glue` solves the challenge of managing DNS records for services that need to be accessible both locally (via UniFi) and remotely (via Cloudflare Tunnel). It provides:

- **Unified Configuration**: Define services once in KCL, generate configurations for both UniFi and Cloudflare
- **DNS Loop Prevention**: Ensures Cloudflare local_service_url uses internal domains only
- **MAC Address Management**: Normalizes and validates MAC addresses across providers
- **One Tunnel Per Device**: Each physical device gets exactly one tunnel

## Project Structure

```
unifi-cloudflare-glue/
├── terraform/
│   └── modules/
│       ├── unifi-dns/          # Terraform module for UniFi DNS management
│       └── cloudflare-tunnel/  # Terraform module for Cloudflare Tunnel
├── kcl/
│   ├── schemas/                # KCL schema definitions
│   │   ├── base.k              # Base schemas (Entity, Endpoint, Service, MACAddress)
│   │   ├── unifi.k             # UniFi-specific schema extensions
│   │   └── cloudflare.k        # Cloudflare-specific schema extensions
│   └── generators/             # KCL configuration generators
│       ├── unifi.k             # UniFi JSON generator
│       └── cloudflare.k        # Cloudflare JSON generator
├── src/                        # Dagger module source
│   └── main/
│       └── main.py             # Dagger functions implementation
├── examples/
│   └── homelab-media-stack/    # Example configuration
└── openspec/                   # OpenSpec change management
```

## Quickstart

### Prerequisites

- Terraform >= 1.5.0
- KCL installed (`curl -sSL https://kcl-lang.io/script/install-cli.sh | bash`)
- UniFi controller access
- Cloudflare account with Tunnel credentials

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/SolomonHD/unifi-cloudflare-glue.git
   cd unifi-cloudflare-glue
   ```

2. Initialize the KCL module:
   ```bash
   cd kcl
   kcl mod add kcl-lang/hello
   cd ..
   ```

3. See the `examples/homelab-media-stack/` directory for a complete working example.

### Usage

#### Option 1: Using Dagger (Recommended - No local KCL needed)

The Dagger module provides containerized KCL generation:

```bash
# Generate UniFi configuration
dagger call generate-unifi-config --source=./kcl export --path=./unifi.json

# Generate Cloudflare configuration
dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
```

#### Option 2: Using Local KCL

1. Define your services in KCL (see examples)
2. Generate JSON configurations:
    ```bash
    cd kcl
    kcl run generators/unifi.k > unifi.json
    kcl run generators/cloudflare.k > cloudflare.json
    ```

3. Apply Terraform configurations:
    ```bash
    cd terraform/modules/unifi-dns
    terraform init
    terraform apply -var-file="../../unifi.json"
    ```

## Using as a Dagger Module

The `unifi-cloudflare-glue` Dagger module can be used remotely from other projects without cloning this repository. This enables you to leverage containerized infrastructure deployment in your own projects with guaranteed reproducibility and no local tool installation requirements.

### Installation

Install the module in your project using `dagger install`:

```bash
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0
```

This registers the module in your project's `dagger.json` and makes it available with the `-m unifi-cloudflare-glue` flag.

### Version Selection

**Production environments should always pin to specific versions:**

- ✅ **Recommended**: Use `@vX.Y.Z` for production (e.g., `@v0.2.0`)
- ⚠️ **Not recommended**: Avoid `@main` in production (unpredictable changes)

**Finding available versions:**

- Check [GitHub releases](https://github.com/SolomonHD/unifi-cloudflare-glue/releases)
- Review [`CHANGELOG.md`](./CHANGELOG.md) for version changes
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

### Function Usage Examples

All examples below assume the module is installed. For direct remote usage without installation, see [Module Calling Patterns](#module-calling-patterns).

#### Deploy (Full Orchestration)

Deploys both UniFi DNS and Cloudflare Tunnel in the correct order:

```bash
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com

# With persistent local state
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --state-dir=./terraform-state

# With pinned tool versions
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

#### Deploy-UniFi (UniFi Only)

Deploys only UniFi DNS records:

```bash
dagger call -m unifi-cloudflare-glue deploy-unifi \
    --source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

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

#### Deploy-Cloudflare (Cloudflare Only)

Deploys only Cloudflare Tunnel and DNS:

```bash
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

#### Destroy (Infrastructure Teardown)

**⚠️ DESTRUCTIVE OPERATION:** Destroys all managed infrastructure in reverse order (Cloudflare first, then UniFi):

```bash
dagger call -m unifi-cloudflare-glue destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com

# With persistent local state (use same state-dir as deploy)
dagger call -m unifi-cloudflare-glue destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --state-dir=./terraform-state
```

#### Plan (Preview Changes)

Generates Terraform plans without applying changes:

```bash
# Export plans to ./plans directory
dagger call -m unifi-cloudflare-glue plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    export --path=./plans

# With persistent local state
dagger call -m unifi-cloudflare-glue plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com \
    --state-dir=./terraform-state \
    export --path=./plans
```

**Output files:** `plans/unifi-plan.{tfplan,json,txt}`, `plans/cloudflare-plan.{tfplan,json,txt}`, `plans/plan-summary.txt`

#### Test-Integration (Integration Testing)

Runs ephemeral integration tests against live APIs:

```bash
dagger call -m unifi-cloudflare-glue test-integration \
    --source=./kcl \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

# Force fresh execution (bypass cache)
dagger call -m unifi-cloudflare-glue test-integration \
    --source=./kcl \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --no-cache

# With real MAC address from your UniFi controller
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

### Module Calling Patterns

There are two ways to call module functions:

#### 1. Installed Module Pattern (Recommended for Local Development)

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

#### 2. Direct Remote Pattern (Recommended for CI/CD)

Call the module directly without installation:

```bash
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0 \
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

#### Pattern Comparison

| Aspect | Installed Module | Direct Remote |
|--------|-----------------|---------------|
| **Command Length** | Short (`-m unifi-cloudflare-glue`) | Long (full URL + module name) |
| **Installation** | Required (`dagger install`) | Not required |
| **Versioning** | In `dagger.json` | In command (`@v0.2.0`) |
| **Best For** | Local development, iteration | CI/CD, one-off operations |

### Version Pinning Best Practices

**⚠️ ALWAYS use specific version tags (`@vX.Y.Z`) in production environments.**

**Benefits:**
- **Reproducibility**: Same version = same behavior across time and environments
- **Predictability**: No unexpected breaking changes
- **Safety**: Test changes before upgrading

**Version update strategy:**

1. Test new version in non-production environment
2. Review [`CHANGELOG.md`](./CHANGELOG.md) for breaking changes
3. Update version pin only after validation
4. Use automated testing to catch regressions

**Example CI/CD with version pinning:**

```yaml
# .github/workflows/deploy.yml
- name: Deploy infrastructure
  run: |
    dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0 \
      unifi-cloudflare-glue deploy \
      --kcl-source=./kcl \
      --unifi-url=${{ secrets.UNIFI_URL }} \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=${{ secrets.CF_ACCOUNT_ID }} \
      --zone-name=${{ secrets.CF_ZONE }}
```

### CI/CD Integration

Example GitHub Actions workflow:

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
          # Direct remote pattern - no installation step
          dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0 \
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

- Use **direct remote pattern** (no installation step required)
- **Pin versions** for reproducibility (`@v0.2.0`)
- Store **secrets in CI environment variables**
- Use **ephemeral state** or remote backend for state management

**Adapting to other CI systems:**

This pattern works with any CI system (GitLab CI, CircleCI, Jenkins, etc.):

1. Install Dagger CLI
2. Set environment variables for secrets
3. Call module using direct remote pattern
4. Use appropriate state management for your environment

See [Dagger CI integration docs](https://docs.dagger.io/integrations/ci) for platform-specific guidance.

### Additional Resources

- **KCL configuration examples**: See [`examples/homelab-media-stack/`](./examples/homelab-media-stack/) for complete working configuration
- **Terraform module usage**: See [Using as Terraform Modules](#using-as-terraform-modules) if you only need the Terraform modules
- **Function signatures**: Run `dagger functions` to list all available functions
- **Parameter details**: Use `dagger call <function> --help` for detailed parameter information
- **KCL language guide**: [KCL Documentation](https://kcl-lang.io/)

## Modules

### Dagger Functions

The Dagger module provides containerized, reproducible pipelines for managing hybrid DNS infrastructure without requiring local KCL or Terraform installation:

#### Configuration Generation

- **`generate-unifi-config`** - Generate UniFi JSON configuration from KCL schemas
  ```bash
  dagger call generate-unifi-config --source=./kcl export --path=./unifi.json
  ```

- **`generate-cloudflare-config`** - Generate Cloudflare JSON configuration from KCL schemas
  ```bash
  dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
  ```

#### Deployment (No Local Terraform Required)

- **`deploy-unifi`** - Deploy UniFi DNS configuration using Terraform
  
  Authentication options (pick one):
  1. API Key (recommended): `--unifi-api-key`
  2. Username/Password: Both `--unifi-username` and `--unifi-password`
  
  TLS options (optional):
  - `--unifi-insecure` - Skip TLS certificate verification (useful for self-signed certificates)
  
  Container version options (optional):
  - `--terraform-version` - Terraform version to use (default: "latest")
  
  ```bash
  # Using API key (recommended)
  dagger call deploy-unifi \
      --source=. \
      --unifi-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY
  
  # Using username/password
  dagger call deploy-unifi \
      --source=. \
      --unifi-url=https://unifi.local:8443 \
      --unifi-username=env:UNIFI_USER \
      --unifi-password=env:UNIFI_PASS
  
  # With self-signed certificates (skip TLS verification)
  dagger call deploy-unifi \
      --source=. \
      --unifi-url=https://192.168.10.1 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --unifi-insecure
  
   # With pinned Terraform version
   dagger call deploy-unifi \
       --source=. \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --terraform-version=1.10.0
   
   # With persistent local state
   dagger call deploy-unifi \
       --source=. \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --state-dir=./terraform-state
   ```

- **`deploy-cloudflare`** - Deploy Cloudflare Tunnel configuration using Terraform
  
  Container version options (optional):
  - `--terraform-version` - Terraform version to use (default: "latest")
  
  ```bash
  dagger call deploy-cloudflare \
      --source=. \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com
  
   # With pinned Terraform version
   dagger call deploy-cloudflare \
       --source=. \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com \
       --terraform-version=1.10.0
   
   # With persistent local state
   dagger call deploy-cloudflare \
       --source=. \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com \
       --state-dir=./terraform-state
   ```

- **`deploy`** - Full deployment orchestration (UniFi first, then Cloudflare)
  
  Deploys in the correct order: UniFi DNS first (creates local DNS), then Cloudflare Tunnels (point to now-resolvable hostnames).
  
  TLS options (optional):
  - `--unifi-insecure` - Skip TLS certificate verification (useful for self-signed certificates)
  
  Container version options (optional):
  - `--terraform-version` - Terraform version to use (default: "latest")
  - `--kcl-version` - KCL version to use (default: "latest")
  
  ```bash
  dagger call deploy \
      --kcl-source=./kcl \
      --unifi-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com
  
  # With self-signed certificates (skip TLS verification)
  dagger call deploy \
      --kcl-source=./kcl \
      --unifi-url=https://192.168.10.1 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com \
      --unifi-insecure
  
   # With pinned versions
   dagger call deploy \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com \
       --terraform-version=1.10.0 \
       --kcl-version=0.11.0
   
   # With persistent local state
   dagger call deploy \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com \
       --state-dir=./terraform-state
   ```

- **`destroy`** - Destroy all resources (Cloudflare first, then UniFi)
  
  Destroys in reverse order to avoid DNS loops: Cloudflare resources first, then UniFi.
  
  TLS options (optional):
  - `--unifi-insecure` - Skip TLS certificate verification (useful for self-signed certificates)
  
  Container version options (optional):
  - `--terraform-version` - Terraform version to use (default: "latest")
  - `--kcl-version` - KCL version to use (default: "latest")
  
  ```bash
  dagger call destroy \
      --kcl-source=./kcl \
      --unifi-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com
  
  # With self-signed certificates (skip TLS verification)
  dagger call destroy \
      --kcl-source=./kcl \
      --unifi-url=https://192.168.10.1 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com \
      --unifi-insecure
  
   # With pinned versions
   dagger call destroy \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com \
       --terraform-version=1.10.0 \
       --kcl-version=0.11.0
   
   # With persistent local state (must use same state directory as deploy)
   dagger call destroy \
       --kcl-source=./kcl \
       --unifi-url=https://unifi.local:8443 \
       --unifi-api-key=env:UNIFI_API_KEY \
       --cloudflare-token=env:CF_TOKEN \
       --cloudflare-account-id=xxx \
       --zone-name=example.com \
       --state-dir=./terraform-state
   ```

#### Plan Generation

- **`plan`** - Generate Terraform plans for both UniFi DNS and Cloudflare Tunnel configurations

  Creates execution plans without applying changes, enabling the standard plan → review → apply
  workflow. Generates three output formats per module: binary plan files, JSON for automation,
  and human-readable text for manual review.

  TLS options (optional):
  - `--unifi-insecure` - Skip TLS certificate verification for self-signed certificates

  Container version options (optional):
  - `--terraform-version` - Terraform version to use (default: "latest")
  - `--kcl-version` - KCL version to use (default: "latest")

  Cache control options (optional):
  - `--no-cache` - Bypass Dagger cache, force fresh execution
  - `--cache-buster` - Custom cache key (advanced use)

  ```bash
  # Basic usage - export plans to ./plans directory
  dagger call plan \
      --kcl-source=./kcl \
      --unifi-url=https://unifi.local:8443 \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com \
      --unifi-api-key=env:UNIFI_API_KEY \
      export --path=./plans

  # With persistent local state
  dagger call plan \
      --kcl-source=./kcl \
      --unifi-url=https://unifi.local:8443 \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com \
      --unifi-api-key=env:UNIFI_API_KEY \
      --state-dir=./terraform-state \
      export --path=./plans

  # With remote backend (S3)
  dagger call plan \
      --kcl-source=./kcl \
      --unifi-url=https://unifi.local:8443 \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --zone-name=example.com \
      --unifi-api-key=env:UNIFI_API_KEY \
      --backend-type=s3 \
      --backend-config-file=./s3-backend.hcl \
      export --path=./plans
  ```

  **Output Directory Structure:**
  ```
  plans/
  ├── unifi-plan.tfplan      # Binary plan (for terraform apply)
  ├── unifi-plan.json        # Structured JSON (for automation)
  ├── unifi-plan.txt         # Human-readable (for review)
  ├── cloudflare-plan.tfplan # Binary plan
  ├── cloudflare-plan.json   # Structured JSON
  ├── cloudflare-plan.txt    # Human-readable
  └── plan-summary.txt       # Aggregated summary
  ```

  **Security Note:** Plan files may contain sensitive values (API tokens, passwords). 
  Add your plans directory to `.gitignore` and handle plan files securely.

#### Testing

- **`test-integration`** - Run integration tests with ephemeral resources
  
  TLS options (optional):
  - `--unifi-insecure` - Skip TLS certificate verification (useful for self-signed certificates)
  
  Test configuration options:
  - `--test-mac-address` - MAC address of a real device in your UniFi controller (default: "aa:bb:cc:dd:ee:ff")
  
  Container version options (optional):
  - `--terraform-version` - Terraform version to use (default: "latest")
  - `--kcl-version` - KCL version to use (default: "latest")
  
  ```bash
  # Basic test
  dagger call test-integration \
      --source=. \
      --cloudflare-zone=test.example.com \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --unifi-url=https://unifi.local:8443 \
      --api-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY

  # With self-signed certificates (skip TLS verification)
  dagger call test-integration \
      --source=. \
      --cloudflare-zone=test.example.com \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --unifi-url=https://192.168.10.1 \
      --api-url=https://192.168.10.1 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --unifi-insecure

  # With cache buster to force re-execution
  dagger call test-integration \
      --source=. \
      --cloudflare-zone=test.example.com \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --unifi-url=https://unifi.local:8443 \
      --api-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cache-buster=$(date +%s)

  # With wait for manual verification
  dagger call test-integration \
      --source=. \
      --cloudflare-zone=test.example.com \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --unifi-url=https://unifi.local:8443 \
      --api-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --wait-before-cleanup=30

  # With a real MAC address (required for UniFi integration)
  dagger call test-integration \
      --source=. \
      --cloudflare-zone=test.example.com \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --unifi-url=https://unifi.local:8443 \
      --api-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --test-mac-address=de:ad:be:ef:12:34

  # With pinned versions
  dagger call test-integration \
      --source=. \
      --cloudflare-zone=test.example.com \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=xxx \
      --unifi-url=https://unifi.local:8443 \
      --api-url=https://unifi.local:8443 \
      --unifi-api-key=env:UNIFI_API_KEY \
      --terraform-version=1.10.0 \
      --kcl-version=0.11.0
  ```

- **`hello`** - Verify the module is working
  ```bash
  dagger call hello
  ```

### Terraform Modules

- **[`terraform/modules/unifi-dns`](./terraform/modules/unifi-dns/)** - Manages UniFi DNS records
- **[`terraform/modules/cloudflare-tunnel`](./terraform/modules/cloudflare-tunnel/)** - Manages Cloudflare Tunnels and DNS

### KCL Module

- **[`kcl/`](./kcl/)** - KCL schemas and generators for configuration validation and generation

## Using as Terraform Modules

The Terraform modules in this repository can be consumed directly from external projects using Git-based module sourcing. This allows you to use these modules as infrastructure dependencies without cloning the entire repository.

### Module Source

Terraform supports fetching modules directly from Git repositories using the following syntax:

```hcl
source = "github.com/OWNER/REPOSITORY//SUBDIR?ref=VERSION"
```

For this project:
- **Repository**: `github.com/SolomonHD/unifi-cloudflare-glue`
- **Module paths**: `//terraform/modules/unifi-dns` or `//terraform/modules/cloudflare-tunnel`
- **Version**: Use `?ref=v0.1.0` to pin to a specific release (recommended)

### Module: unifi-dns

```hcl
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"

  config = {
    devices = [
      {
        friendly_hostname = "media-server"
        domain            = "internal.lan"
        nics = [
          {
            mac_address = "aa:bb:cc:dd:ee:01"
          }
        ]
      }
    ]
    default_domain = "internal.lan"
    site           = "default"
  }

  strict_mode = false
}
```

### Module: cloudflare-tunnel

```hcl
module "cloudflare_tunnel" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/cloudflare-tunnel?ref=v0.1.0"

  config = {
    zone_name  = "example.com"
    account_id = "your-cloudflare-account-id"
    tunnels = {
      "aa:bb:cc:dd:ee:ff" = {
        tunnel_name = "home-server"
        mac_address = "aa:bb:cc:dd:ee:ff"
        services = [
          {
            public_hostname   = "media.example.com"
            local_service_url = "http://jellyfin.internal.lan:8096"
            no_tls_verify     = false
          }
        ]
      }
    }
  }
}
```

## Examples

See [`examples/homelab-media-stack/`](./examples/homelab-media-stack/) for a complete example with media services.

## Versioning

This project uses a **unified versioning strategy** where all components (KCL schemas, Terraform modules, and Dagger module) share the same version number. This ensures compatibility across all components.

### Current Version

**Version: 0.1.0**

### Version Components

| Component | Version Location |
|-----------|------------------|
| KCL Module | [`kcl/kcl.mod`](./kcl/kcl.mod:4) |
| Terraform Modules | Comment in `versions.tf` files |
| Dagger Module | `pyproject.toml` and `VERSION` file |

### Semantic Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.y.z): Breaking changes in any component
- **MINOR** (x.Y.z): New features (backward compatible)
- **PATCH** (x.y.Z): Bug fixes

### Querying the Version

Use the Dagger `version` function to check the current version:

```bash
dagger call version --source=.
```

### Version Pinning

You can pin to specific versions of container tools for reproducibility:

```bash
# Pin Terraform version
dagger call deploy --source=. --terraform-version=1.10.0 ...

# Pin KCL version
dagger call deploy --source=. --kcl-version=0.11.0 ...

# Pin both
dagger call deploy --source=. --terraform-version=1.10.0 --kcl-version=0.11.0 ...
```

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for the release process.

## State Management

All deployment functions support configurable Terraform state management with three modes to suit different workflows:

### State Management Modes

| Mode | Use Case | Persistence | Best For |
|------|----------|-------------|----------|
| **Ephemeral** (default) | Testing, CI/CD, one-off operations | Container-only, lost on exit | Quick tests, ephemeral environments |
| **Persistent Local** | Solo development | Host filesystem at `./terraform-state` | Iterative development without remote backend setup |
| **Remote Backend** | Production, team collaboration | S3, Azure, GCS, Terraform Cloud | Team environments, production infrastructure |

### Persistent Local State

For solo development workflows, you can persist Terraform state locally without setting up a remote backend. This provides a middle ground between ephemeral container state (lost on exit) and remote backends (requires cloud credentials and infrastructure).

```bash
# Create a directory for state storage
mkdir -p ./terraform-state

# Deploy with persistent local state
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --state-dir=./terraform-state

# Destroy using the same state directory
dagger call destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --state-dir=./terraform-state
```

> **Note:** `--state-dir` and `--backend-type` (remote backend) are **mutually exclusive**. Choose one state management strategy per deployment.

### How Persistent Local State Works

When using `--state-dir`:
1. The specified directory is mounted into the container at `/state`
2. Terraform module files are copied to the state directory
3. Terraform operations run from `/state`, keeping state files and module code together
4. State persists on your host filesystem between runs

### Using Remote Backends

To use a remote backend, specify the backend type and provide a configuration file:

### Using Remote Backends

To use a remote backend, specify the backend type and provide a configuration file:

```bash
dagger call deploy \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

> **Important:** When using remote backends, you must use the **same backend configuration** for both `deploy` and `destroy` operations.

### Supported Backend Types

- `s3` - AWS S3 with optional DynamoDB locking
- `azurerm` - Azure Blob Storage
- `gcs` - Google Cloud Storage
- `remote` - Terraform Cloud / Terraform Enterprise
- And any other backend supported by Terraform

### Backend Configuration Files

Example configuration files are provided in [`examples/backend-configs/`](./examples/backend-configs/):

- `s3-backend.hcl` - AWS S3 configuration
- `azurerm-backend.hcl` - Azure Blob Storage configuration
- `gcs-backend.hcl` - Google Cloud Storage configuration
- `remote-backend.hcl` - Terraform Cloud configuration

#### S3 Backend Example

```hcl
# s3-backend.hcl
bucket = "my-terraform-state-bucket"
key    = "unifi-cloudflare-glue/terraform.tfstate"
region = "us-east-1"
encrypt = true
dynamodb_table = "terraform-state-lock"
```

**Required Environment Variables:**
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Azure Blob Storage Example

```hcl
# azurerm-backend.hcl
storage_account_name = "myterraformstate"
container_name       = "terraform-state"
key                  = "unifi-cloudflare-glue/terraform.tfstate"
resource_group_name  = "my-resource-group"
```

**Required Environment Variables:**
```bash
export ARM_CLIENT_ID="your-service-principal-client-id"
export ARM_CLIENT_SECRET="your-service-principal-client-secret"
export ARM_SUBSCRIPTION_ID="your-subscription-id"
export ARM_TENANT_ID="your-tenant-id"
```

#### Google Cloud Storage Example

```hcl
# gcs-backend.hcl
bucket = "my-terraform-state-bucket"
prefix = "unifi-cloudflare-glue/terraform"
```

**Required Environment Variables:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### Terraform Cloud Example

```hcl
# remote-backend.hcl
organization = "my-organization"
workspaces {
  name = "unifi-cloudflare-glue"
}
```

**Required Environment Variable:**
```bash
export TF_TOKEN_app_terraform_io="your-terraform-cloud-api-token"
```

### Backend Validation

The module validates backend configuration and provides clear error messages:

```bash
# Error: Missing config file for remote backend
$ dagger call deploy --backend-type=s3 ...
✗ Failed: Backend type 's3' requires --backend-config-file

# Error: Config file provided but local backend selected
$ dagger call deploy --backend-type=local --backend-config-file=./s3-backend.hcl ...
✗ Failed: --backend-config-file specified but backend_type is 'local'
```

### State Management Security

#### General Security Best Practices

- **Never commit credentials** in backend configuration files
- Use **environment variables** for all sensitive values
- Enable **encryption at rest** (supported by all remote backends)
- Use **state locking** to prevent concurrent modifications
- Apply **least privilege** permissions to backend credentials

#### Persistent Local State Security

When using `--state-dir` for persistent local state:

- **State files may contain sensitive values** (API tokens, passwords)
- **Add your state directory to `.gitignore`** to prevent accidental commits
- **Backup your state directory** regularly - losing it means losing track of your infrastructure
- **No state locking** - avoid concurrent operations from different machines
- Use filesystem permissions to restrict access to the state directory

Example `.gitignore` entries:
```gitignore
# Terraform state files (if using persistent local state)
terraform-state/
*.tfstate
*.tfstate.*
```

See [`examples/backend-configs/README.md`](./examples/backend-configs/README.md) for detailed security guidance.

## Security Best Practices

### Credential Handling

All sensitive credentials are handled using Dagger's `Secret` type, which ensures:
- Secrets are never logged to console output
- Secrets are not stored in command history
- Secrets are passed securely to containers via environment variables

#### Environment Variable Pattern

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

#### Required Environment Variables

| Variable | Description | Used By |
|----------|-------------|---------|
| `UNIFI_API_KEY` | UniFi API key (recommended) | `deploy-unifi`, `deploy`, `destroy` |
| `UNIFI_USER` | UniFi username (alternative) | `deploy-unifi`, `deploy`, `destroy` |
| `UNIFI_PASS` | UniFi password (alternative) | `deploy-unifi`, `deploy`, `destroy` |
| `CF_TOKEN` | Cloudflare API token | `deploy-cloudflare`, `deploy`, `destroy` |

### Authentication Methods

#### UniFi Authentication (Choose One)

1. **API Key (Recommended)** - More secure, single token
   ```bash
   export UNIFI_API_KEY="your-api-key"
   dagger call deploy-unifi --unifi-api-key=env:UNIFI_API_KEY ...
   ```

2. **Username/Password** - Traditional authentication
   ```bash
   export UNIFI_USER="admin"
   export UNIFI_PASS="password"
   dagger call deploy-unifi \
       --unifi-username=env:UNIFI_USER \
       --unifi-password=env:UNIFI_PASS ...
   ```

**Note**: You cannot use both methods simultaneously. The module will reject ambiguous authentication configurations.

### Terraform State Security

#### Local State (Default)

By default, Terraform stores state locally in the container:
- State is ephemeral and lost when the container exits
- Suitable for testing and development
- **Warning**: State files may contain sensitive values

#### Remote State (Recommended for Production)

For production use, configure remote state backend in your Terraform modules:

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

### State File Cleanup

When using local state, remember to clean up state files if needed:

```bash
# After destroy, clean up any remaining state files
rm -f terraform.tfstate terraform.tfstate.backup
```

### CI/CD Security

When using in CI/CD pipelines:

1. **Store secrets in CI environment variables** (not in code)
2. **Use short-lived tokens** when possible
3. **Rotate credentials regularly**
4. **Enable audit logging** on UniFi and Cloudflare
5. **Restrict API token permissions** to minimum required:
   - Cloudflare token: Zone:Read, DNS:Edit, Cloudflare Tunnel:Edit
   - UniFi API key: Administrator role (or custom with network management)

### Network Security

- Use HTTPS URLs for UniFi controller (`https://unifi.local:8443`)
- Verify TLS certificates in production
- Consider VPN or private networking for UniFi access
- Firewall rules should restrict UniFi controller access

## License

MIT
