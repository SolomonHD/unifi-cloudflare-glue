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
   git clone https://github.com/yourusername/unifi-cloudflare-glue.git
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
  ```

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
