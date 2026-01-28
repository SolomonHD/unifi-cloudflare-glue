# KCL Configuration Module

This directory contains KCL (Kusion Configuration Language) schemas and generators for the `unifi-cloudflare-glue` project.

## Purpose

The KCL module provides:

- **Schema Validation**: Define and validate service configurations using type-safe schemas
- **Cross-Provider Validation**: Ensure consistency between UniFi and Cloudflare configurations
- **JSON Generation**: Generate provider-specific JSON configurations from unified definitions

## Directory Structure

```
kcl/
├── kcl.mod           # KCL module manifest
├── README.md         # This file
├── schemas/          # Schema definitions
│   ├── base.k        # Base schemas (Entity, Endpoint, Service, MACAddress)
│   ├── unifi.k       # UniFi-specific schema extensions
│   └── cloudflare.k  # Cloudflare-specific schema extensions
└── generators/       # Configuration generators
    ├── unifi.k       # UniFi JSON generator
    └── cloudflare.k  # Cloudflare JSON generator
```

## Usage

### Validate Configuration

```bash
kcl run schemas/base.k
```

### Generate UniFi Configuration

```bash
kcl run generators/unifi.k > unifi.json
```

### Generate Cloudflare Configuration

```bash
kcl run generators/cloudflare.k > cloudflare.json
```

## Schemas

### Base Schemas (`schemas/base.k`)

Defines core domain models:
- `Entity`: Base entity with name and description
- `MACAddress`: Normalized MAC address format (lowercase colon)
- `Endpoint`: Service endpoint with host, port, and protocol
- `Service`: High-level service definition

### UniFi Schemas (`schemas/unifi.k`)

Extends base schemas for UniFi DNS management:
- `UniFiClient`: UniFi client device with MAC and IP
- `UniFiDNSRecord`: DNS record for local resolution

### Cloudflare Schemas (`schemas/cloudflare.k`)

Extends base schemas for Cloudflare Tunnel:
- `CloudflareTunnel`: Tunnel configuration
- `CloudflareIngress`: Ingress rule for tunnel routing
- `CloudflareConfig`: Complete Cloudflare configuration

## Generators

Generators transform KCL configurations into provider-specific JSON formats that can be consumed by Terraform modules.

## Examples

See `../examples/homelab-media-stack/` for a complete working example.
