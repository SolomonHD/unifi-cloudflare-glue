# KCL Configuration Module

This directory contains KCL (Kusion Configuration Language) schemas and generators for the `unifi-cloudflare-glue` project.

> **📖 Complete Documentation**: For comprehensive KCL documentation including schema reference, validation rules, configuration patterns, debugging guide, and examples, see the **[KCL Configuration Guide](../docs/kcl-guide.md)**.

## Purpose

The KCL module provides:

- **Schema Validation**: Define and validate service configurations using type-safe schemas
- **Cross-Provider Validation**: Ensure consistency between UniFi and Cloudflare configurations
- **JSON Generation**: Generate provider-specific JSON configurations from unified definitions

## Directory Structure

```
kcl/
├── kcl.mod              # KCL module manifest
├── README.md            # This file
├── main.k               # Main entrypoint with unified config and validation
├── test_validation.k    # Validation test cases
├── schemas/             # Schema definitions
│   ├── base.k           # Base schemas (Entity, Endpoint, Service, MACAddress)
│   ├── unifi.k          # UniFi-specific schema extensions
│   └── cloudflare.k     # Cloudflare-specific schema extensions
└── generators/          # Configuration generators
    ├── unifi.k          # UniFi JSON generator
    └── cloudflare.k     # Cloudflare JSON generator
```

## Usage

### Quick Start with Unified Configuration

The **only** supported way to run KCL for this project is through the main entry point:

```bash
kcl run main.k
```

This validates your configuration and generates unified output containing both `unifi_output` and `cf_output` sections.

> **Important**: The Dagger module extracts specific sections using `yq`. You should NOT run individual generator files directly (e.g., `kcl run generators/unifi.k`) as this triggers a SIGSEGV bug in KCL v0.12.x when using git dependencies.

Your `main.k` must export these public variables:
- `unifi_output`: Configuration for UniFi DNS (extracted by Dagger)
- `cf_output`: Configuration for Cloudflare Tunnel (extracted by Dagger)

### Validate Configuration

```bash
kcl run main.k
```

Validation happens automatically when you run `main.k`. Check for validation errors in the output.

### Run Validation Tests

```bash
kcl run test_validation.k
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
- `UniFiEndpoint`: Network interface with MAC address and UniFi-specific settings
- `UniFiEntity`: Device with hostname, domain, endpoints, and services
- `UniFiController`: Connection details for UniFi Controller
- `UniFiConfig`: Root configuration container
- `Service`: Application service with distribution settings

### Cloudflare Schemas (`schemas/cloudflare.k`)

Extends base schemas for Cloudflare Tunnel:
- `CloudflareTunnel`: Tunnel configuration linked to a physical device by MAC address
- `TunnelService`: Ingress rule mapping public hostname to internal service URL
- `CloudflareConfig`: Complete Cloudflare configuration with zone and account settings
- `is_valid_domain()`: Validates domain syntax per RFC 1123 (DNS loop prevention)
- `hostname_in_zone()`: Validates that hostnames belong to the configured zone

## Generators

Generators transform KCL configurations into provider-specific output sections. These are imported and called by [`main.k`](main.k); they should **NOT** be run directly due to a KCL v0.12.x bug with git dependencies.

### UniFi Generator (`generators/unifi.k`)

The UniFi generator transforms `UniFiConfig` schemas into the `unifi_output` section.

#### Usage

Generators are invoked via [`main.k`](main.k):

```kcl
import generators.unifi as unifi_gen

unifi_output = unifi_gen.generate_unifi_config(config.unifi)
```

The Dagger module then extracts `unifi_output` from the unified YAML.

#### Functions

- `generate_unifi_config(config)`: Main entry point - transforms a `UniFiConfig` into JSON-compatible dictionary
- `transform_entity(entity)`: Converts a `UniFiEntity` to a device record
- `transform_endpoint(endpoint)`: Converts a `UniFiEndpoint` to a NIC record
- `filter_unifi_services(services)`: Filters services for UniFi DNS (excludes `cloudflare_only`)
- `normalize_mac(mac)`: Normalizes MAC addresses to lowercase colon format

#### Output Format

```json
{
  "devices": [{
    "friendly_hostname": "media-server",
    "domain": "internal.lan",
    "service_cnames": ["storage.internal.lan", "jellyfin.internal.lan"],
    "nics": [{
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "nic_name": "eth0",
      "service_cnames": ["nas.internal.lan"]
    }]
  }],
  "default_domain": "internal.lan"
}
```

#### Service Distribution

Services are filtered based on their `distribution` field:
- `unifi_only`: Included in UniFi DNS
- `both`: Included in UniFi DNS
- `cloudflare_only`: Excluded from UniFi DNS

### Cloudflare Generator (`generators/cloudflare.k`)

The Cloudflare generator transforms `CloudflareConfig` schemas into the `cf_output` section.

#### Usage

Generators are invoked via [`main.k`](main.k):

```kcl
import generators.cloudflare as cf_gen

cf_output = cf_gen.generate_cloudflare_config(config.cloudflare)
```

The Dagger module then extracts `cf_output` from the unified YAML.

#### Functions

- `generate_cloudflare_config(config)`: Main entry point - transforms a `CloudflareConfig` into JSON-compatible dictionary
- `generate_cloudflare_from_entities(entities, zone_name, account_id, ...)`: Alternative entry point using base `Entity` objects
- `transform_service(service, device_hostname, domain, zone_name, default_no_tls_verify)`: Converts a `Service` to a TunnelService record
- `filter_cloudflare_services(services)`: Filters services for Cloudflare (excludes `unifi_only`)
- `build_local_service_url(protocol, hostname, port)`: Constructs internal service URL
- `resolve_public_hostname(service, zone_name)`: Resolves public hostname for a service
- `validate_no_dns_loop(url, zone)`: Validates that local_service_url doesn't contain public zone (DNS loop prevention)
- `normalize_mac(mac)`: Normalizes MAC addresses to lowercase colon format

#### Output Format

```json
{
  "zone_name": "example.com",
  "account_id": "1234567890abcdef1234567890abcdef",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "media-server",
      "services": [{
        "public_hostname": "jellyfin.example.com",
        "local_service_url": "http://jellyfin.internal.lan:8096",
        "no_tls_verify": false
      }]
    }
  }
}
```

#### Service Distribution

Services are filtered based on their `distribution` field:
- `cloudflare_only`: Included in Cloudflare Tunnel
- `both`: Included in Cloudflare Tunnel
- `unifi_only`: Excluded from Cloudflare Tunnel

#### DNS Loop Prevention

The generator validates that `local_service_url` uses valid domain syntax per RFC 1123. Any valid domain name is accepted - users are responsible for ensuring DNS resolution is correct.
- `.internal.lan`
- `.local`
- `.home`
- `.home.arpa`
- `.localdomain`

Attempts to use the public zone name in `local_service_url` will fail validation.

## Unified Configuration (`main.k`)

The unified configuration provides a single source of truth for your entire infrastructure by combining UniFi and Cloudflare configurations with cross-provider validation.

### UnifiedConfig Schema

```kcl
import .main

config = main.UnifiedConfig {
    unifi = unifi.UniFiConfig {
        devices = [...]
        default_domain = "internal.lan"
        unifi_controller = unifi.UniFiController {
            host = "unifi.internal.lan"
        }
    }
    cloudflare = cloudflare.CloudflareConfig {
        zone_name = "example.com"
        account_id = "1234567890abcdef1234567890abcdef"
        tunnels = {...}
    }
    mappings = [
        main.DeviceToTunnelMapping {
            device_hostname = "media-server"
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:01"
        }
    ]
}

result = main.generate(config)
```

### GenerateResult Output

The `generate()` function returns a `GenerateResult` containing:

```yaml
result:
  unifi_json:       # UniFi-compatible JSON configuration
  cloudflare_json:  # Cloudflare-compatible JSON configuration
  valid: true       # Whether validation passed
  errors: []        # List of validation errors if any
```

### DeviceToTunnelMapping

Explicitly link UniFi devices to Cloudflare tunnels:

```kcl
main.DeviceToTunnelMapping {
    device_hostname = "media-server"    # Matches UniFiEntity.friendly_hostname
    tunnel_name = "media-server"         # Matches CloudflareTunnel.tunnel_name
    mac_address = "aa:bb:cc:dd:ee:01"    # Links both configurations
}
```

## Cross-Provider Validation

The `main.k` module implements comprehensive cross-provider validation that runs before any JSON generation (fail-fast behavior).

### Validation Rules

| Validation | Description | Error Code |
|------------|-------------|------------|
| MAC Consistency | All Cloudflare tunnel MACs must exist in UniFi devices | `MAC_CONSISTENCY_ERROR` |
| Hostname Uniqueness | No two devices can share the same `friendly_hostname` | `DUPLICATE_HOSTNAME_ERROR` |
| Public Hostname Uniqueness | No two tunnel services can share the same `public_hostname` | `DUPLICATE_PUBLIC_HOSTNAME_ERROR` |
| Domain Syntax | All `local_service_url` values must use valid RFC 1123 domain syntax | `DOMAIN_SYNTAX_ERROR` |

### Validation Functions

- `validate_mac_consistency(cfg)`: Checks all Cloudflare MACs exist in UniFi
- `validate_hostname_uniqueness(cfg)`: Checks for duplicate device hostnames
- `validate_public_hostname_uniqueness(cfg)`: Checks for duplicate public hostnames
- `validate_domain_syntax(cfg)`: Ensures local_service_url uses valid domain syntax per RFC 1123
- `validate_all(cfg)`: Runs all validations and returns error list

### Error Message Format

Validation errors include context and actionable suggestions:

```yaml
error: MAC_CONSISTENCY_ERROR
message: Cloudflare tunnels reference MAC addresses not found in UniFi devices
missing_macs: '[aa:bb:cc:dd:ee:99]'
available_unifi_macs: '[aa:bb:cc:dd:ee:01, aa:bb:cc:dd:ee:02]'
suggestion: Add UniFi devices with these MAC addresses or update tunnel configurations
```

## Examples

See `../examples/homelab-media-stack/` for a complete working example.
