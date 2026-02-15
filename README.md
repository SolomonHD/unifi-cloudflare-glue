# unifi-cloudflare-glue

A hybrid DNS infrastructure tool that bridges UniFi network DNS with Cloudflare Tunnel edge DNS. This project enables seamless DNS management for services that need to be accessible both locally (via UniFi) and remotely (via Cloudflare Tunnel).

## Purpose

`unifi-cloudflare-glue` solves the challenge of managing DNS records for hybrid infrastructure. Define your services once in KCL, and the tool generates configurations for both UniFi (local DNS) and Cloudflare (remote access via Tunnels).

## Quick Start

```bash
# 1. Install the Dagger module
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.9.2

# 2. Deploy both UniFi DNS and Cloudflare Tunnel
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com
```

See the [examples/homelab-media-stack/](examples/homelab-media-stack/) directory for a complete working configuration.

## Documentation

| Document | Description |
|----------|-------------|
| **[Architecture](docs/architecture.md)** | Visual diagrams of system components and data flow |
| **[KCL Configuration Guide](docs/kcl-guide.md)** | Complete KCL schema reference, validation rules, and examples |
| **[Validation Errors](docs/validation-errors.md)** | Validation error types and how to fix them |
| **[Deployment Patterns](docs/deployment-patterns.md)** | Environment-specific patterns (dev, staging, production) |
| **[Getting Started](docs/getting-started.md)** | Installation, prerequisites, and first deployment |
| **[Dagger Reference](docs/dagger-reference.md)** | Complete function reference with examples |
| **[Terraform Modules](docs/terraform-modules.md)** | Standalone Terraform module usage |
| **[State Management](docs/state-management.md)** | State backends: ephemeral, local, and remote |
| **[Security](docs/security.md)** | Security best practices and credential handling |
| **[vals Integration](docs/vals-integration.md)** | Secret injection with vals for backend configs |
| **[Backend Configuration](docs/backend-configuration.md)** | Comprehensive backend and state locking guide |
| **[Troubleshooting](docs/troubleshooting.md)** | Error references, decision trees, and solutions |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   KCL Config    │────▶│     main.k      │────▶│  JSON Output    │
│  (services.k)   │     │  (entry point)  │     │ (unifi.json)    │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                              ┌──────────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │  Dagger Module  │
                    │ (Orchestration) │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  UniFi DNS   │ │Cloudflare    │ │  Terraform   │
    │   Records    │ │  Tunnel      │ │   State      │
    └──────────────┘ └──────────────┘ └──────────────┘
```

The Dagger module provides containerized, reproducible pipelines that orchestrate KCL configuration generation and Terraform deployments without requiring local tool installation.

## Key Features

- **Unified Configuration**: Define services once in KCL, generate configurations for both UniFi and Cloudflare
- **DNS Loop Prevention**: Ensures Cloudflare `local_service_url` uses internal domains only
- **MAC Address Management**: Normalizes and validates MAC addresses across providers
- **One Tunnel Per Device**: Each physical device gets exactly one tunnel
- **Flexible State Management**: Ephemeral, persistent local, or remote backends
- **CI/CD Ready**: Designed for automated deployments with secret management

## Project Structure

```
unifi-cloudflare-glue/
├── docs/                       # Documentation
├── terraform/modules/          # Terraform modules
│   ├── unifi-dns/              # UniFi DNS management
│   └── cloudflare-tunnel/      # Cloudflare Tunnel management
├── main.k                      # KCL entry point (exports unifi_output and cf_output)
├── schemas/                    # KCL schema definitions
├── generators/                 # KCL output generators (imported by main.k)
├── examples/                   # Example configurations
│   └── homelab-media-stack/    # Complete working example
└── src/                        # Dagger module source
```

## Common Commands

### Deploy

```bash
# Full deployment (UniFi + Cloudflare)
dagger call -m unifi-cloudflare-glue deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com

# Deploy only UniFi
dagger call -m unifi-cloudflare-glue deploy-unifi \
    --source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

# Deploy only Cloudflare
dagger call -m unifi-cloudflare-glue deploy-cloudflare \
    --source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```

### Plan and Destroy

```bash
# Generate plans without applying
dagger call -m unifi-cloudflare-glue plan \
    --kcl-source=./kcl ... \
    export --path=./plans

# Destroy all resources (Cloudflare first, then UniFi)
dagger call -m unifi-cloudflare-glue destroy \
    --kcl-source=./kcl ...
```

### Generate Configurations

```bash
# Generate UniFi JSON
dagger call generate-unifi-config --source=./kcl export --path=./unifi.json

# Generate Cloudflare JSON
dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
```

## Critical: Parameter Differences

> **⚠️ IMPORTANT:** Remote module users must understand the difference between `--source` and `--kcl-source` parameters.

| Parameter | Purpose | When to Use |
|-----------|---------|-------------|
| `--source=.` | Reads the **module's** KCL files | ❌ Only for local development within this repository |
| `--kcl-source=./your-config` | Reads **your project's** KCL files | ✅ Required when using the module remotely |

**Why this matters:**
- Local development: `--source=.` works because it reads the module's own KCL schemas
- Remote usage: You **must** use `--kcl-source` to provide your own configuration
- Using `--source=.` remotely will fail or read the wrong files

## Versioning

This project uses unified versioning where all components (KCL schemas, Terraform modules, and Dagger module) share the same version number.

**Current Version: 0.1.0**

Always pin to specific versions in production:

```bash
# ✅ Recommended - pinned version
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.9.2

# ⚠️ Not recommended - latest main
dagger install github.com/SolomonHD/unifi-cloudflare-glue@main
```

Check the [CHANGELOG](CHANGELOG.md) for version history.

## Prerequisites

- Terraform >= 1.5.0 (only if using standalone modules)
- KCL (only if using local generation)
- UniFi controller access with API key or credentials
- Cloudflare account with API token

## Security

All credentials are handled using Dagger's `Secret` type:

```bash
# ✅ Correct - use env: prefix
dagger call deploy --unifi-api-key=env:UNIFI_API_KEY ...

# ❌ Never pass secrets directly
dagger call deploy --unifi-api-key="actual-secret" ...
```

See [docs/security.md](docs/security.md) for comprehensive security guidance.

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Deploy infrastructure
  run: |
    dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.9.2 \
      unifi-cloudflare-glue deploy \
      --kcl-source=./kcl \
      --unifi-url=${{ secrets.UNIFI_URL }} \
      --unifi-api-key=env:UNIFI_API_KEY \
      --cloudflare-token=env:CF_TOKEN \
      --cloudflare-account-id=${{ secrets.CF_ACCOUNT_ID }} \
      --zone-name=${{ secrets.CF_ZONE }}
```

See [docs/dagger-reference.md](docs/dagger-reference.md#cicd-integration) for detailed CI/CD patterns.

## State Management

Three modes supported:

| Mode | Use Case | Command |
|------|----------|---------|
| **Ephemeral** | Testing, CI/CD | Default (no flags) |
| **Persistent Local** | Solo development | `--state-dir=./terraform-state` |
| **Remote Backend** | Production | `--backend-type=s3 --backend-config-file=./backend.hcl` |

See [docs/state-management.md](docs/state-management.md) for detailed configuration.

## Testing

### Generator Validation Tests

The project includes comprehensive validation tests for KCL generator output to ensure compatibility with Terraform modules.

**Run all generator tests:**
```bash
pytest tests/unit/test_generator_output.py -v
```

**Run specific test classes:**
```bash
# UniFi generator tests only
pytest tests/unit/test_generator_output.py::TestUniFiGeneratorOutput -v

# Cloudflare generator tests only
pytest tests/unit/test_generator_output.py::TestCloudflareGeneratorOutput -v

# Edge case tests
pytest tests/unit/test_generator_output.py::TestEdgeCases -v
```

**Run with coverage:**
```bash
pytest tests/unit/test_generator_output.py --cov=tests.unit.test_generator_output
```

### Expected Generator Output Format

**Consumer Contract:** Your [`main.k`](main.k) **MUST** export these public variables:
- `unifi_output`: UniFi DNS configuration (dict/object)
- `cf_output`: Cloudflare Tunnel configuration (dict/object)

The Dagger module runs `kcl run main.k`, writes the output to a file, then extracts each section using `yq` (e.g., `yq eval '.unifi_output'`). If either variable is missing, you'll get a clear error message.

**UniFi Output** (extracted from `main.k` as `unifi_output`):
```json
{
  "devices": [
    {
      "friendly_hostname": "media-server",
      "domain": "internal.lan",
      "service_cnames": ["jellyfin.internal.lan"],
      "nics": [
        {
          "mac_address": "aa:bb:cc:dd:ee:ff",
          "nic_name": "eth0",
          "service_cnames": ["nas.internal.lan"]
        }
      ]
    }
  ],
  "default_domain": "internal.lan",
  "site": "default"
}
```

**Cloudflare Output** (extracted from `main.k` as `cf_output`):
```json
{
  "zone_name": "example.com",
  "account_id": "1234567890abcdef1234567890abcdef",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "media-server",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "services": [
        {
          "public_hostname": "jellyfin.example.com",
          "local_service_url": "http://jellyfin.internal.lan:8096",
          "no_tls_verify": false
        }
      ]
    }
  }
}
```

### Example Test Failure Output

When a test fails, you'll see detailed error messages like:

```
✗ Generator Output Validation Failed

Field:      devices[0].nics[0].mac_address
Expected:   string matching pattern "^[0-9a-f]{2}:[0-9a-f]{2}:..."
Found:      "AA-BB-CC-DD-EE-FF" (wrong format: uppercase with dashes)
Hint:       MAC addresses should be normalized to lowercase colon format (aa:bb:cc:dd:ee:ff)
```

This helps identify issues quickly, such as:
- Missing required fields (e.g., the `site` field was previously missing)
- Type mismatches (e.g., `devices` being a string instead of array)
- Invalid MAC address formats (e.g., uppercase or dashes instead of lowercase colons)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Running tests
- Submitting changes

## License

MIT
