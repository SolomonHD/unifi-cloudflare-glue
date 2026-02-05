# Documentation

Welcome to the `unifi-cloudflare-glue` documentation. This directory contains comprehensive guides organized by topic.

## Quick Navigation

| Document | Description |
|----------|-------------|
| **[KCL Configuration Guide](kcl-guide.md)** | Complete KCL schema reference, validation rules, patterns, and examples |
| **[Getting Started](getting-started.md)** | Installation, prerequisites, and first deployment |
| **[Dagger Reference](dagger-reference.md)** | Complete function reference and CI/CD integration |
| **[Terraform Modules](terraform-modules.md)** | Standalone Terraform module usage |
| **[State Management](state-management.md)** | State backends: ephemeral, local, and remote |
| **[Security](security.md)** | Security best practices and credential handling |
| **[vals Integration](vals-integration.md)** | Secret injection with vals for backend configurations |
| **[Backend Configuration](backend-configuration.md)** | Comprehensive backend and state locking guide |
| **[Troubleshooting](troubleshooting.md)** | Common issues and solutions *(coming soon)* |

## Getting Started

New to `unifi-cloudflare-glue`? Start here:

1. **[Getting Started](getting-started.md)** - Install and deploy for the first time
2. **[Security](security.md)** - Understand credential handling
3. **[Dagger Reference](dagger-reference.md)** - Learn the available functions

## By Use Case

### Local Development
- [Getting Started](getting-started.md) - Installation and setup
- [State Management](state-management.md) - Local state persistence
- [Dagger Reference](dagger-reference.md) - All deployment functions

### CI/CD Integration
- [Dagger Reference - CI/CD Integration](dagger-reference.md#cicd-integration)
- [Security](security.md#cicd-security)
- [State Management - Remote Backends](state-management.md#remote-backends)

### Production Deployment
- [Security](security.md) - Essential security practices
- [State Management](state-management.md) - Remote state backends
- [Terraform Modules](terraform-modules.md) - Standalone module usage

## Key Features

### Unified Configuration
Define services once in KCL, generate configurations for both UniFi and Cloudflare.

### DNS Loop Prevention
Ensures Cloudflare `local_service_url` uses internal domains only.

### MAC Address Management
Normalizes and validates MAC addresses across providers.

### One Tunnel Per Device
Each physical device gets exactly one tunnel.

## Project Structure

```
unifi-cloudflare-glue/
├── docs/                       # This documentation
├── terraform/modules/          # Terraform modules
│   ├── unifi-dns/              # UniFi DNS management
│   └── cloudflare-tunnel/      # Cloudflare Tunnel management
├── kcl/                        # KCL schemas and generators
├── examples/                   # Example configurations
└── src/                        # Dagger module source
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for information on:
- Setting up a development environment
- Running tests
- Submitting changes

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history and changes.

## License

MIT License - See [LICENSE](../LICENSE) for details.
