# unifi-cloudflare-glue

A hybrid DNS infrastructure tool that bridges UniFi network DNS with Cloudflare Tunnel edge DNS. This project enables seamless DNS management for services that need to be accessible both locally (via UniFi) and remotely (via Cloudflare Tunnel).

## Purpose

`unifi-cloudflare-glue` solves the challenge of managing DNS records for hybrid infrastructure. Define your services once in KCL, and the tool generates configurations for both UniFi (local DNS) and Cloudflare (remote access via Tunnels).

## Quick Start

```bash
# 1. Install the Dagger module
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.6.0

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
│   KCL Config    │────▶│   Generators    │────▶│  JSON Output    │
│  (services.k)   │     │ (unifi/cloudflare)│    │ (unifi.json)    │
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
├── kcl/                        # KCL schemas and generators
│   ├── schemas/                # Schema definitions
│   └── generators/             # Configuration generators
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
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.6.0

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
    dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.6.0 \
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

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Running tests
- Submitting changes

## License

MIT
