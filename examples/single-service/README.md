# Single Service Example

A minimal working example demonstrating a single device with one service accessible both internally (via UniFi DNS) and externally (via Cloudflare Tunnel).

## Overview

This example configures:
- One device (`media-server`) with a single network interface
- One service (Jellyfin media server on port 8096)
- Dual exposure: accessible both inside your network and from the internet

## Architecture

```
┌─────────────────┐
│  media-server   │
│  (aa:bb:cc:..)  │
│                 │
│  ┌───────────┐  │
│  │ Jellyfin  │  │
│  │  :8096    │  │
│  └─────┬─────┘  │
└────────┼────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌─────────────────┐
│  UniFi │  │   Cloudflare    │
│  DNS   │  │     Tunnel      │
└────────┘  └─────────────────┘
    │               │
    ▼               ▼
jellyfin.     media.example.com
internal.lan   (public)
(private)
```

## Prerequisites

1. KCL installed (`kcl` command available)
2. A UniFi Controller with API access
3. A Cloudflare account with a domain
4. Your device's MAC address

## Files

- `main.k` - Complete KCL configuration
- `kcl.mod` - KCL module manifest

## Quick Start

### 1. Customize the Configuration

Edit `main.k` and replace the placeholders:

```kcl
# Line 29: Your device's MAC address
mac_address = "aa:bb:cc:dd:ee:ff"

# Line 46: Your Cloudflare zone
zone_name = "example.com"

# Line 49: Your Cloudflare account ID
account_id = "your-account-id"

# Line 41: Your UniFi Controller host
host = "unifi.internal.lan"

# Lines 58, 78: Match your domain
public_hostname = "media.example.com"
```

### 2. Validate the Configuration

```bash
kcl run main.k
```

**Expected output:**
```yaml
_unifi:
  devices:
    - friendly_hostname: media-server
      domain: internal.lan
      service_cnames:
        - jellyfin.internal.lan
      nics:
        - mac_address: aa:bb:cc:dd:ee:ff
          nic_name: eth0
  default_domain: internal.lan
_cloudflare:
  zone_name: example.com
  account_id: your-account-id
  tunnels:
    aa:bb:cc:dd:ee:ff:
      tunnel_name: media-server
      services:
        - public_hostname: media.example.com
          local_service_url: http://jellyfin.internal.lan:8096
          no_tls_verify: false
```

### 3. Deploy

Using Dagger:
```bash
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.3.2 deploy \
    --kcl-source=. \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com
```

## Customization Guide

### Changing the Service

To use a different service, modify the `services` list:

```kcl
services = [
    unifi.Service {
        name = "plex"           # Change service name
        port = 32400            # Change port
        protocol = "https"      # Change protocol (http/https/tcp)
        distribution = "both"
        internal_hostname = "plex.internal.lan"
        public_hostname = "plex.example.com"
    }
]
```

### Adding More Services

Add additional services to the list:

```kcl
services = [
    unifi.Service {
        name = "jellyfin"
        port = 8096
        protocol = "http"
        distribution = "both"
        internal_hostname = "jellyfin.internal.lan"
        public_hostname = "media.example.com"
    }
    unifi.Service {              # Second service
        name = "admin"
        port = 8080
        protocol = "https"
        distribution = "unifi_only"  # Internal only
        internal_hostname = "admin.internal.lan"
    }
]
```

See the [multiple-services](../multiple-services/) example for more details.

### Using Different Domains

Change the internal domain:

```kcl
# In UniFiEntity
domain = "home.local"           # Was: "internal.lan"

# In Service
internal_hostname = "jellyfin.home.local"

# In UniFiConfig
default_domain = "home.local"

# In TunnelService
local_service_url = "http://jellyfin.home.local:8096"
```

### Changing MAC Address Format

All these formats work and normalize to the same value:

```kcl
mac_address = "aa:bb:cc:dd:ee:ff"   # Standard
mac_address = "AA:BB:CC:DD:EE:FF"   # Uppercase (normalized)
mac_address = "aa-bb-cc-dd-ee-ff"   # Hyphen
mac_address = "aabbccddeeff"        # No separator
```

## Understanding Distribution

The `distribution` field controls DNS record creation:

| Value | UniFi DNS | Cloudflare | Use Case |
|-------|-----------|------------|----------|
| `unifi_only` | ✅ | ❌ | Internal tools, admin panels |
| `cloudflare_only` | ❌ | ✅ | Public APIs, external services |
| `both` | ✅ | ✅ | Services accessed from anywhere |

## Troubleshooting

### MAC Consistency Error

If you see:
```
Error: MAC_CONSISTENCY_ERROR
missing_macs: ["aa:bb:cc:dd:ee:ff"]
```

Ensure the MAC address in `CloudflareTunnel` matches the MAC in `UniFiEntity`.

### DNS Loop Error

If you see:
```
Error: local_service_url must use an internal domain
```

Ensure `local_service_url` uses an internal domain (`.internal.lan`, `.local`, `.home`):

```kcl
# Wrong - creates DNS loop
local_service_url = "http://jellyfin.example.com:8096"

# Correct
local_service_url = "http://jellyfin.internal.lan:8096"
```

### Validation Errors

If you see validation errors like:
```
✗ VALIDATION FAILED
Found 1 validation error(s):
✗ MAC_CONSISTENCY_ERROR
```

This means your configuration has issues that must be fixed before deployment. See:
- [Validation Errors Documentation](../../docs/validation-errors.md) - Detailed error reference
- [Validation Testing Example](../validation-testing/) - Learn how validation works

Run `kcl run main.k` to see detailed error messages with line numbers.

## Next Steps

- **Add more services**: See [multiple-services](../multiple-services/)
- **Internal-only setup**: See [internal-only](../internal-only/)
- **External-only setup**: See [external-only](../external-only/)
- **Learn about validation**: See [validation-testing](../validation-testing/)
- **Full documentation**: See [KCL Guide](../../docs/kcl-guide.md)

## License

MIT - See [LICENSE](../../LICENSE)