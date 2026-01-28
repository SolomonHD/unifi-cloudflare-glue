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

### Terraform Modules

- **[`terraform/modules/unifi-dns`](./terraform/modules/unifi-dns/)** - Manages UniFi DNS records
- **[`terraform/modules/cloudflare-tunnel`](./terraform/modules/cloudflare-tunnel/)** - Manages Cloudflare Tunnels and DNS

### KCL Module

- **[`kcl/`](./kcl/)** - KCL schemas and generators for configuration validation and generation

## Examples

See [`examples/homelab-media-stack/`](./examples/homelab-media-stack/) for a complete example with media services.

## License

MIT
