# KCL Configuration Guide

Complete reference for configuring infrastructure using KCL (Kusion Configuration Language) with `unifi-cloudflare-glue`.

## Table of Contents

- [Overview](#overview)
- [Schema Reference](#schema-reference)
  - [Base Schemas](#base-schemas)
  - [UniFi Schemas](#unifi-schemas)
  - [Cloudflare Schemas](#cloudflare-schemas)
- [Validation Rules](#validation-rules)
- [Configuration Patterns](#configuration-patterns)
- [Debugging Guide](#debugging-guide)
- [Testing and Validation](#testing-and-validation)
- [Examples](#examples)
- [See Also](#see-also)

---

## Overview

KCL is the configuration language used to define your infrastructure in `unifi-cloudflare-glue`. It provides:

- **Type Safety**: Schemas validate your configuration at build time
- **Cross-Provider Consistency**: Single source of truth for UniFi and Cloudflare
- **Validation Rules**: Built-in checks prevent common mistakes
- **Code Reuse**: Modular schemas and generators

### Why KCL?

Traditional infrastructure configuration requires maintaining separate files for each provider. KCL enables a unified approach:

```kcl
# Define once, use everywhere
media_server = UniFiEntity {
    friendly_hostname = "media-server"
    services = [
        Service { name = "jellyfin", port = 8096, distribution = "both" }
    ]
}
# Generates both UniFi DNS records AND Cloudflare Tunnel config
```

### Workflow

1. **Define** your devices and services in KCL
2. **Validate** with `kcl run` to catch errors early
3. **Generate** JSON for Terraform consumption
4. **Deploy** via Dagger or standalone Terraform

---

## Schema Reference

### Base Schemas

Base schemas define the core domain models used across both UniFi and Cloudflare configurations.

#### MACAddress

Validates and normalizes MAC addresses to lowercase colon format.

**Type**: `str` with validation

**Accepted Formats**:
| Format | Example | Normalized To |
|--------|---------|---------------|
| Colon-separated | `aa:bb:cc:dd:ee:ff` | `aa:bb:cc:dd:ee:ff` |
| Hyphen-separated | `aa-bb-cc-dd-ee-ff` | `aa:bb:cc:dd:ee:ff` |
| No separator | `aabbccddeeff` | `aa:bb:cc:dd:ee:ff` |

**Validation**:
- Length must be 12 (no separator) or 17 (with separators) characters
- Hexadecimal characters only (auto-converted to lowercase)

**Examples**:
```kcl
# Valid MAC addresses
mac1 = "aa:bb:cc:dd:ee:ff"      # Standard format
mac2 = "AA:BB:CC:DD:EE:FF"      # Uppercase (normalized to lowercase)
mac3 = "aa-bb-cc-dd-ee-ff"      # Hyphen format
mac4 = "aabbccddeeff"           # No separators

# Invalid MAC addresses
invalid1 = "aa:bb:cc:dd:ee"     # Too short (5 octets)
invalid2 = "aa:bb:cc:dd:ee:ff:gg" # Too long (7 octets)
invalid3 = "aa:bb:cc:dd:ee:gg"  # Invalid hex (contains 'g')
```

---

#### Hostname

Validates DNS labels according to RFC 1123.

**Type**: `str` with validation

**Constraints**:
| Constraint | Value | Description |
|------------|-------|-------------|
| Length | 1-63 characters | DNS label limit |
| Start character | Letter or digit | Cannot start with hyphen |
| End character | Letter or digit | Cannot end with hyphen |
| Allowed characters | `[a-zA-Z0-9-]` | Letters, digits, hyphens only |

**Examples**:
```kcl
# Valid hostnames
hostname1 = "nas-01"            # Letters, digits, hyphens
hostname2 = "server-prod"       # Multiple words with hyphens
hostname3 = "web1"              # Letters and digits
hostname4 = "a"                 # Single character (minimum)

# Invalid hostnames
invalid1 = "_server"            # Starts with underscore
invalid2 = "server_prod"        # Contains underscore
invalid3 = "-server"            # Starts with hyphen
invalid4 = "server-"            # Ends with hyphen
invalid5 = "server.prod"        # Contains dot (use domain field)
invalid6 = "a" * 64             # Too long (>63 chars)
```

---

#### Distribution

Controls where service DNS records are published.

**Type**: String enum

**Values**:
| Value | Description | Use Case |
|-------|-------------|----------|
| `unifi_only` | DNS record only in UniFi (internal network) | Management interfaces, internal tools |
| `cloudflare_only` | DNS record only in Cloudflare (external/public) | Public APIs, customer portals |
| `both` | DNS records in both UniFi and Cloudflare | Services accessed internally and externally |

**Examples**:
```kcl
# Internal-only service
admin_panel = Service {
    name = "admin"
    distribution = "unifi_only"
}

# External-only service
public_api = Service {
    name = "api"
    distribution = "cloudflare_only"
}

# Dual exposure
media_server = Service {
    name = "jellyfin"
    distribution = "both"  # Accessible locally AND remotely
}
```

---

#### Endpoint

Represents a network interface on an entity.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mac_address` | MACAddress | Yes | - | MAC address of the interface |
| `nic_name` | str | No | None | Human-readable name (e.g., "eth0", "wlan0") |
| `service_cnames` | [str] | No | [] | CNAME aliases for services on this endpoint |

**Examples**:
```kcl
# Simple endpoint
endpoint1 = Endpoint {
    mac_address = "aa:bb:cc:dd:ee:ff"
}

# Endpoint with name and CNAMEs
endpoint2 = Endpoint {
    mac_address = "aa:bb:cc:dd:ee:ff"
    nic_name = "eth0"
    service_cnames = ["nas.internal.lan", "storage.internal.lan"]
}
```

---

#### Service

Represents an application running on an entity.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `name` | str | Yes | - | Service identifier (e.g., "jellyfin", "ssh") |
| `port` | int | Yes | - | TCP/UDP port number (1-65535) |
| `protocol` | str | Yes | - | Protocol: "http", "https", or "tcp" |
| `distribution` | Distribution | No | "both" | Where to publish DNS records |
| `internal_hostname` | str | No | None | Internal DNS name (e.g., "jellyfin.internal.lan") |
| `public_hostname` | str | No | None | Public DNS name (e.g., "jellyfin.example.com") |

**Examples**:
```kcl
# Minimal service (uses defaults)
service1 = Service {
    name = "jellyfin"
    port = 8096
    protocol = "http"
}

# Complete service definition
service2 = Service {
    name = "plex"
    port = 32400
    protocol = "https"
    distribution = "both"
    internal_hostname = "plex.internal.lan"
    public_hostname = "media.example.com"
}

# Internal-only service
service3 = Service {
    name = "ssh"
    port = 22
    protocol = "tcp"
    distribution = "unifi_only"
    internal_hostname = "ssh.internal.lan"
}
```

---

#### Entity

Represents a physical device with network interfaces and services.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `friendly_hostname` | Hostname | Yes | - | DNS-compatible hostname for the device |
| `domain` | str | Yes | - | Base domain for DNS records |
| `endpoints` | [Endpoint] | No | [] | List of network interfaces |
| `services` | [Service] | No | [] | List of services on this device |

**Examples**:
```kcl
# Simple entity
nas = Entity {
    friendly_hostname = "nas-01"
    domain = "internal.lan"
    endpoints = [
        Endpoint { mac_address = "aa:bb:cc:dd:ee:ff" }
    ]
    services = [
        Service { name = "files", port = 443, protocol = "https" }
    ]
}

# Multi-service entity
media_server = Entity {
    friendly_hostname = "media-server"
    domain = "internal.lan"
    endpoints = [
        Endpoint {
            mac_address = "aa:bb:cc:dd:ee:01"
            nic_name = "eth0"
        }
    ]
    services = [
        Service { name = "jellyfin", port = 8096, protocol = "http" }
        Service { name = "plex", port = 32400, protocol = "https" }
    ]
}
```

---

### UniFi Schemas

UniFi schemas extend base schemas for UniFi DNS management.

#### UniFiEndpoint

Network interface with UniFi-specific properties for IP management.

**Schema Fields** (extends Endpoint):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `mac_address` | MACAddress | Yes | - | MAC address of the interface |
| `nic_name` | str | No | None | Human-readable name |
| `service_cnames` | [str] | No | [] | CNAME aliases |
| `query_unifi` | bool | No | True | Query UniFi Controller for current IP |
| `static_ip` | str | No | None | Static IP when query_unifi is false |

**Examples**:
```kcl
# Endpoint with dynamic IP from UniFi
endpoint1 = UniFiEndpoint {
    mac_address = "aa:bb:cc:dd:ee:ff"
    query_unifi = True
}

# Endpoint with static IP
endpoint2 = UniFiEndpoint {
    mac_address = "aa:bb:cc:dd:ee:ff"
    query_unifi = False
    static_ip = "192.168.1.100"
}

# Complete endpoint
endpoint3 = UniFiEndpoint {
    mac_address = "aa:bb:cc:dd:ee:ff"
    nic_name = "eth0"
    service_cnames = ["admin.internal.lan"]
    query_unifi = True
}
```

---

#### UniFiEntity

Physical device in the UniFi network with site support.

**Schema Fields** (extends Entity):

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `friendly_hostname` | Hostname | Yes | - | DNS-compatible hostname |
| `domain` | str | Yes | - | Base domain (must end in .lan, .local, or .home) |
| `endpoints` | [UniFiEndpoint] | No | [] | Network interfaces |
| `services` | [Service] | No | [] | Services |
| `unifi_site` | str | No | "default" | UniFi site name |
| `service_cnames` | [str] | No | [] | Device-level CNAME aliases |

**Validation Rules**:
- Must have at least one endpoint
- Domain must end in `.lan`, `.local`, or `.home` (safety requirement)

**Examples**:
```kcl
# Simple device
device1 = UniFiEntity {
    friendly_hostname = "nas-01"
    domain = "internal.lan"
    endpoints = [
        UniFiEndpoint { mac_address = "aa:bb:cc:dd:ee:ff" }
    ]
}

# Device with site and CNAMEs
device2 = UniFiEntity {
    friendly_hostname = "media-server"
    domain = "home.local"
    unifi_site = "default"
    service_cnames = ["storage.home.local"]
    endpoints = [
        UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
        }
    ]
    services = [
        Service {
            name = "jellyfin"
            port = 8096
            protocol = "http"
            internal_hostname = "jellyfin.home.local"
        }
    ]
}
```

---

#### UniFiController

Connection configuration for UniFi Controller.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `host` | str | Yes | - | Hostname or IP of UniFi Controller |
| `port` | int | No | 443 | HTTPS port for controller |
| `username_ref` | str | No | "UNIFI_USERNAME" | Environment variable for username |
| `password_ref` | str | No | "UNIFI_PASSWORD" | Environment variable for password |
| `site` | str | No | "default" | Default site name |

**Examples**:
```kcl
# Standard controller
controller = UniFiController {
    host = "unifi.internal.lan"
    port = 443
}

# Custom credentials
controller2 = UniFiController {
    host = "192.168.1.1"
    port = 8443
    username_ref = "MY_UNIFI_USER"
    password_ref = "MY_UNIFI_PASS"
    site = "home"
}
```

---

#### UniFiConfig

Root configuration container for UniFi DNS management.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `devices` | [UniFiEntity] | No | [] | List of devices |
| `default_domain` | str | No | "internal.lan" | Default domain for DNS records |
| `unifi_controller` | UniFiController | No | UniFiController{} | Controller connection details |

**Examples**:
```kcl
# Complete UniFi configuration
unifi_config = UniFiConfig {
    devices = [media_server, nas_device]
    default_domain = "internal.lan"
    unifi_controller = UniFiController {
        host = "unifi.internal.lan"
    }
}
```

---

### Cloudflare Schemas

Cloudflare schemas extend base schemas for Cloudflare Tunnel management.

#### TunnelService

Ingress rule for Cloudflare Tunnel routing.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `public_hostname` | str | Yes | - | Public-facing FQDN (must be subdomain of zone) |
| `local_service_url` | str | Yes | - | Internal URL (must use internal domain) |
| `no_tls_verify` | bool | No | False | Skip TLS verification for local service |
| `path_prefix` | str | No | None | Optional path prefix for routing |

**Validation Rules**:
- `local_service_url` must use internal domain (`.internal.lan`, `.local`, `.home`, `.home.arpa`, `.localdomain`)
- Prevents DNS resolution loops

**Examples**:
```kcl
# Basic tunnel service
tunnel_svc1 = TunnelService {
    public_hostname = "jellyfin.example.com"
    local_service_url = "http://jellyfin.internal.lan:8096"
}

# With self-signed cert
tunnel_svc2 = TunnelService {
    public_hostname = "nas.example.com"
    local_service_url = "https://nas.internal.lan:443"
    no_tls_verify = True
}

# With path prefix
tunnel_svc3 = TunnelService {
    public_hostname = "api.example.com"
    local_service_url = "http://api.internal.lan:8080"
    path_prefix = "/v1"
}
```

---

#### CloudflareTunnel

Cloudflare Zero Trust Tunnel configuration linked to a physical device.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `tunnel_name` | str | Yes | - | Unique tunnel identifier |
| `mac_address` | MACAddress | Yes | - | MAC address of device running cloudflared |
| `services` | [TunnelService] | No | [] | List of ingress rules |
| `credentials_path` | str | No | None | Path to tunnel credentials file |

**Validation Rules**:
- `tunnel_name` must be non-empty
- `mac_address` must be 17 characters (aa:bb:cc:dd:ee:ff format)
- Each MAC address can only have one tunnel

**Examples**:
```kcl
# Simple tunnel
tunnel1 = CloudflareTunnel {
    tunnel_name = "media-server"
    mac_address = "aa:bb:cc:dd:ee:ff"
    services = [
        TunnelService {
            public_hostname = "jellyfin.example.com"
            local_service_url = "http://jellyfin.internal.lan:8096"
        }
    ]
}

# Multi-service tunnel
tunnel2 = CloudflareTunnel {
    tunnel_name = "home-server"
    mac_address = "aa:bb:cc:dd:ee:ff"
    credentials_path = "/etc/cloudflared/home-server.json"
    services = [
        TunnelService {
            public_hostname = "media.example.com"
            local_service_url = "http://jellyfin.internal.lan:8096"
        }
        TunnelService {
            public_hostname = "files.example.com"
            local_service_url = "https://nas.internal.lan:443"
            no_tls_verify = True
        }
    ]
}
```

---

#### CloudflareConfig

Root configuration container for Cloudflare Tunnel integration.

**Schema Fields**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `zone_name` | str | Yes | - | Cloudflare DNS zone (e.g., "example.com") |
| `account_id` | str | Yes | - | Cloudflare account ID |
| `tunnels` | {str:CloudflareTunnel} | No | {} | Dictionary of tunnels keyed by MAC address |
| `default_no_tls_verify` | bool | No | False | Default TLS verification setting |

**Validation Rules**:
- `zone_name` must be non-empty
- `account_id` must be non-empty

**Examples**:
```kcl
# Complete Cloudflare configuration
cloudflare_config = CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:ff": CloudflareTunnel {
            tunnel_name = "home-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            services = [
                TunnelService {
                    public_hostname = "media.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
            ]
        }
    }
}
```

---

## Validation Rules

### MAC Address Validation

**What**: All MAC addresses are validated and normalized to lowercase colon format.

**Why**: Ensures consistent cross-provider matching. UniFi and Cloudflare configurations reference the same device by its unique MAC address.

**How It Works**:
1. Accepts three input formats (colon, hyphen, no separator)
2. Removes all separators and converts to lowercase
3. Reinserts colons in standard positions
4. Result: `aa:bb:cc:dd:ee:ff`

**Validation Errors**:
```
Error: MAC address must be 12 chars (aabbccddeeff) or 17 chars (aa:bb:cc:dd:ee:ff or aa-bb-cc-dd-ee-ff)
```

**Fix**: Check that your MAC address has exactly 6 octets (12 hex digits).

---

### Hostname Validation

**What**: Hostnames must comply with RFC 1123 DNS label requirements.

**Why**: DNS labels have strict rules for compatibility across all DNS implementations.

**Constraints**:
- 1-63 characters in length
- Start with letter or digit
- End with letter or digit
- Contain only letters, digits, and hyphens (no underscores!)

**Validation Errors**:
```
Error: Hostname must be 1-63 characters
Error: Hostname must not contain underscores, spaces, dots, or special characters
```

**Common Mistakes**:
| Invalid | Why | Valid Alternative |
|---------|-----|-------------------|
| `server_prod` | Underscore | `server-prod` |
| `-server` | Starts with hyphen | `server` |
| `server-` | Ends with hyphen | `server` |
| `server.local` | Contains dot | `server` (use domain field for `.local`) |

---

### DNS Loop Prevention

**What**: `local_service_url` in Cloudflare TunnelService must use internal domains only.

**Why**: Using a public zone name in `local_service_url` creates a DNS resolution loop:
1. User requests `service.example.com`
2. Cloudflare tunnel receives request
3. Tunnel tries to route to `service.example.com:8080`
4. DNS resolves to Cloudflare again → **infinite loop**

**Valid Internal Domain Suffixes**:
- `.internal.lan`
- `.local`
- `.home`
- `.home.arpa`
- `.localdomain`

**Validation Errors**:
```
Error: local_service_url must use an internal domain (.internal.lan, .local, .home, etc.) to prevent DNS resolution loops
```

**Fix**: Change `local_service_url` to use an internal hostname:
```kcl
# Wrong - creates DNS loop
local_service_url = "http://service.example.com:8080"

# Correct - uses internal domain
local_service_url = "http://service.internal.lan:8080"
```

---

### One Tunnel Per Device

**What**: Each physical device MAC address can have at most one Cloudflare tunnel.

**Why**: Enforces clear infrastructure mapping. One physical device = one tunnel = one cloudflared instance.

**How It's Enforced**: The `tunnels` dictionary in `CloudflareConfig` uses MAC addresses as keys. Dictionary keys must be unique.

**Handling Multiple Services**: Add multiple `TunnelService` entries within a single `CloudflareTunnel`:

```kcl
# Correct - one tunnel with multiple services
tunnels = {
    "aa:bb:cc:dd:ee:ff": CloudflareTunnel {
        tunnel_name = "home-server"
        mac_address = "aa:bb:cc:dd:ee:ff"
        services = [
            TunnelService { public_hostname = "media.example.com", ... }
            TunnelService { public_hostname = "files.example.com", ... }
            TunnelService { public_hostname = "admin.example.com", ... }
        ]
    }
}

# Wrong - multiple tunnels for same MAC
tunnels = {
    "aa:bb:cc:dd:ee:ff": CloudflareTunnel { ... }
    "aa:bb:cc:dd:ee:ff": CloudflareTunnel { ... }  # ERROR: duplicate key
}
```

---

### Port Range Validation

**What**: Service ports must be in the valid TCP/UDP port range.

**Why**: Ports are 16-bit unsigned integers (0-65535). Port 0 is reserved.

**Valid Range**: 1-65535

**Reserved Ports** (1-1023):
- Require root privileges to bind
- Include well-known services (22/SSH, 80/HTTP, 443/HTTPS)

**Common Ports**:
| Port | Service | Use Case |
|------|---------|----------|
| 22 | SSH | Remote administration |
| 80 | HTTP | Web services (usually proxied) |
| 443 | HTTPS | Secure web services |
| 8080 | Alt-HTTP | Development/proxy services |
| 8096 | Jellyfin | Media server |
| 32400 | Plex | Media server |
| 8989 | Sonarr | TV automation |

**Validation Errors**:
```
Error: Port must be between 1 and 65535
```

---

### Cross-Provider MAC Consistency

**What**: All MAC addresses referenced in Cloudflare tunnels must exist in UniFi device endpoints.

**Why**: Ensures that tunnel configurations point to actual managed devices. Prevents orphaned tunnels or typos.

**Validation Error**:
```
Error: MAC_CONSISTENCY_ERROR
Cloudflare tunnels reference MAC addresses not found in UniFi devices
missing_macs: ["aa:bb:cc:dd:ee:99"]
available_unifi_macs: ["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"]
```

**Fix Options**:
1. Add a UniFi device with the missing MAC address
2. Correct the MAC address in the Cloudflare tunnel config (typo)
3. Remove the Cloudflare tunnel if no longer needed

---

## Configuration Patterns

### Single Service Per Device

**Use Case**: A device hosting one service accessible both internally and externally.

**Pattern**:
- One `Entity` with one `Service`
- `distribution = "both"` for dual exposure
- Internal DNS via UniFi, external via Cloudflare Tunnel

**Example**:
```kcl
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# Device with single service
media_server = unifi.UniFiEntity {
    friendly_hostname = "media-server"
    domain = "internal.lan"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
        }
    ]
    services = [
        unifi.Service {
            name = "jellyfin"
            port = 8096
            protocol = "http"
            distribution = "both"
            internal_hostname = "jellyfin.internal.lan"
            public_hostname = "media.example.com"
        }
    ]
}

# UniFi configuration
unifi_config = unifi.UniFiConfig {
    devices = [media_server]
    default_domain = "internal.lan"
}

# Cloudflare tunnel
cloudflare_config = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "your-account-id"
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "media.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
            ]
        }
    }
}
```

**Result**:
- Internal: `jellyfin.internal.lan` → resolves via UniFi
- External: `media.example.com` → routes via Cloudflare Tunnel

See complete example: [`examples/single-service/`](../examples/single-service/)

---

### Multiple Services Per Device

**Use Case**: A device hosting several services with different exposure requirements.

**Pattern**:
- One `Entity` with multiple `Service` entries
- Varied `distribution` values per service
- All Cloudflare services in one tunnel

**Example**:
```kcl
home_server = unifi.UniFiEntity {
    friendly_hostname = "home-server"
    domain = "internal.lan"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
        }
    ]
    services = [
        # Internal-only: Management
        unifi.Service {
            name = "admin"
            port = 8080
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "admin.internal.lan"
        }
        # External-only: Public API
        unifi.Service {
            name = "api"
            port = 3000
            protocol = "https"
            distribution = "cloudflare_only"
            internal_hostname = "api.internal.lan"
            public_hostname = "api.example.com"
        }
        # Both: Media server
        unifi.Service {
            name = "jellyfin"
            port = 8096
            protocol = "http"
            distribution = "both"
            internal_hostname = "jellyfin.internal.lan"
            public_hostname = "media.example.com"
        }
    ]
}
```

**Service Organization Strategy**:
1. **Admin interfaces** → `unifi_only` (internal security boundary)
2. **Public APIs** → `cloudflare_only` (external access only)
3. **Media streaming** → `both` (bandwidth-efficient local access + remote)

See complete example: [`examples/multiple-services/`](../examples/multiple-services/)

---

### Internal-Only Services

**Use Case**: Services that should never be accessible from the internet.

**Pattern**:
- `distribution = "unifi_only"` for all services
- No Cloudflare tunnel entries for these services
- Only UniFi DNS records are created

**Example**:
```kcl
internal_services = unifi.UniFiEntity {
    friendly_hostname = "internal-tools"
    domain = "internal.lan"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
        }
    ]
    services = [
        unifi.Service {
            name = "prometheus"
            port = 9090
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "metrics.internal.lan"
        }
        unifi.Service {
            name = "grafana"
            port = 3000
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "dashboards.internal.lan"
        }
    ]
}
```

**Use Cases**:
- Monitoring dashboards (Prometheus, Grafana)
- Internal APIs and microservices
- Management interfaces without authentication
- Database admin tools
- Development/staging environments

**Security Benefits**:
- No public DNS entries
- No attack surface from internet
- Accessible only within network perimeter

See complete example: [`examples/internal-only/`](../examples/internal-only/)

---

### External-Only Services

**Use Case**: Services that should only be accessed via Cloudflare (no internal DNS).

**Pattern**:
- `distribution = "cloudflare_only"` for all services
- Minimal UniFi configuration (just device registration)
- Cloudflare tunnel provides all access

**Example**:
```kcl
public_services = unifi.UniFiEntity {
    friendly_hostname = "public-server"
    domain = "internal.lan"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
        }
    ]
    services = [
        unifi.Service {
            name = "website"
            port = 80
            protocol = "http"
            distribution = "cloudflare_only"
            internal_hostname = "website.internal.lan"
            public_hostname = "www.example.com"
        }
    ]
}

cloudflare_config = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "your-account-id"
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "public-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "www.example.com"
                    local_service_url = "http://website.internal.lan:80"
                }
            ]
        }
    }
}
```

**Routing Flow**:
1. User requests `www.example.com`
2. Cloudflare edge receives request
3. Tunnel routes to `http://website.internal.lan:80`
4. Internal DNS (UniFi) resolves `website.internal.lan` to server IP
5. Server responds through tunnel

**Use Cases**:
- Public-facing websites
- Customer portals
- External APIs
- Services requiring Cloudflare security features (WAF, Access)

See complete example: [`examples/external-only/`](../examples/external-only/)

---

### Mixed Distribution Device

**Use Case**: Single device hosting both sensitive internal services and public services.

**Pattern**:
- One `Entity` with services using different `distribution` values
- Internal services accessible only via UniFi
- Public services accessible via Cloudflare
- Database/internal on `unifi_only`, API on `cloudflare_only`

**Example**:
```kcl
app_server = unifi.UniFiEntity {
    friendly_hostname = "app-server"
    domain = "internal.lan"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
        }
    ]
    services = [
        # Database - internal only
        unifi.Service {
            name = "postgres"
            port = 5432
            protocol = "tcp"
            distribution = "unifi_only"
            internal_hostname = "db.internal.lan"
        }
        # API - external only
        unifi.Service {
            name = "api"
            port = 8080
            protocol = "https"
            distribution = "cloudflare_only"
            internal_hostname = "api.internal.lan"
            public_hostname = "api.example.com"
        }
        # Admin panel - internal only
        unifi.Service {
            name = "admin"
            port = 3000
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "admin.internal.lan"
        }
    ]
}
```

**Benefits**:
- Database has no external exposure
- API is globally accessible
- Admin panel protected by network boundary
- Single server, clear security zones

---

### Multi-NIC Device

**Use Case**: Server with multiple network interfaces for traffic separation.

**Pattern**:
- Multiple `Endpoint` entries in one `Entity`
- Each NIC has unique MAC address
- Services can be associated with specific interfaces via `service_cnames`

**Example**:
```kcl
multi_nic_server = unifi.UniFiEntity {
    friendly_hostname = "storage-server"
    domain = "internal.lan"
    endpoints = [
        # Management NIC (1GbE)
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:01"
            nic_name = "eth0-mgmt"
            service_cnames = ["admin.internal.lan"]
            query_unifi = True
        }
        # Storage NIC (10GbE)
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:02"
            nic_name = "eth1-storage"
            service_cnames = ["storage.internal.lan", "nfs.internal.lan"]
            query_unifi = True
        }
    ]
    services = [
        unifi.Service {
            name = "nfs"
            port = 2049
            protocol = "tcp"
            distribution = "unifi_only"
            internal_hostname = "nfs.internal.lan"
        }
        unifi.Service {
            name = "admin"
            port = 443
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "admin.internal.lan"
        }
    ]
}
```

**Benefits**:
- Management traffic isolated from data traffic
- Different subnets for different purposes
- Service discovery per interface
- Link aggregation or failover possibilities

---

## Debugging Guide

### Syntax Error Diagnosis

**Identifying Syntax Errors**:

When you run `kcl run` and see syntax errors, the error message includes:
- File path
- Line number
- Error description

```
error[E2C01]: InvalidSyntax
 --> /path/to/file.k:15:1
   |
15 |     name = "value"
   | ^^^
   | Invalid indentation
```

**Common Syntax Mistakes**:

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid indentation` | Mixed tabs/spaces or wrong indentation level | Use consistent 4-space indentation |
| `Unclosed bracket` | Missing closing `]`, `}`, or `)` | Check for matching brackets |
| `Unexpected token` | Typo in keyword or missing delimiter | Verify KCL syntax |
| `Invalid string` | Unclosed quote or invalid escape | Close strings with matching quotes |

**Using Editor Bracket Matching**:

Most editors highlight matching brackets:
- Place cursor on a bracket to see its match
- Use editor commands to jump between brackets
- Enable bracket pair colorization

**KCL Indentation Rules**:

- Use spaces, not tabs
- Standard: 4 spaces per indentation level
- Schema bodies are indented
- List items are indented

```kcl
# Correct indentation
schema Example:
    field1: str
    field2: int

entity = Example {
    field1 = "value"
    field2 = 42
}

# Incorrect - mixing tabs and spaces
schema Bad:
→   field1: str  # Tab
    field2: int  # Spaces
```

---

### Type Error Diagnosis

**Identifying Type Mismatches**:

Type errors occur when a value doesn't match the expected schema type.

```
error[E2L23]: TypeError
 --> /path/to/file.k:10:5
   |
10 |     port = "8080"
   |     ^^^^ expected int, got str
```

**Common Type Errors**:

| Error | Example | Correct |
|-------|---------|---------|
| String for int | `port = "8080"` | `port = 8080` |
| Int for string | `protocol = 8080` | `protocol = "http"` |
| Single value for list | `endpoints = endpoint` | `endpoints = [endpoint]` |
| Wrong schema type | Passing `Endpoint` where `UniFiEndpoint` expected | Use correct schema |

**Enum Type Errors**:

```
error[E2L23]: TypeError
 --> /path/to/file.k:12:9
   |
12 |     distribution = "all"
   |     ^^^^^^^^^^^^ expected "unifi_only" | "cloudflare_only" | "both"
```

Fix: Use one of the valid enum values.

**List Syntax**:

```kcl
# Correct - list of endpoints
endpoints = [
    UniFiEndpoint { mac_address = "aa:bb:cc:dd:ee:01" }
    UniFiEndpoint { mac_address = "aa:bb:cc:dd:ee:02" }
]

# Incorrect - missing brackets
endpoints = UniFiEndpoint { ... }

# Incorrect - wrong syntax (not KCL)
endpoints = (
    UniFiEndpoint { ... }
)
```

---

### Validation Error Diagnosis

**Check Block Failures**:

Validation errors come from schema `check` blocks.

```
Error: Check failed
 --> /path/to/file.k:25:1
   |
25 |     port = 0
   | ^^^^
   | Port must be between 1 and 65535
```

**Common Validation Errors**:

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Port must be between 1 and 65535` | Port 0 or >65535 | Use valid port number |
| `MAC address must be 12 or 17 chars` | Wrong MAC format | Check MAC address format |
| `Domain must end in .lan, .local, or .home` | Public domain in UniFi config | Use internal domain |
| `local_service_url must use internal domain` | DNS loop risk | Change to internal hostname |
| `Hostname must be 1-63 characters` | Hostname too long | Shorten hostname |

**MAC Consistency Error**:

```
Error: MAC_CONSISTENCY_ERROR
Cloudflare tunnels reference MAC addresses not found in UniFi devices
missing_macs: ["aa:bb:cc:dd:ee:99"]
available_unifi_macs: ["aa:bb:cc:dd:ee:01", "aa:bb:cc:dd:ee:02"]
```

**Steps to Fix**:
1. Compare `missing_macs` with `available_unifi_macs`
2. Check for typos in MAC address
3. Either:
   - Add UniFi device with missing MAC
   - Update Cloudflare tunnel to use correct MAC
   - Remove tunnel if device no longer exists

**Hostname Uniqueness Error**:

```
Error: DUPLICATE_HOSTNAME_ERROR
Duplicate friendly_hostname values found
duplicates: ["server"]
```

Fix: Ensure each device has a unique `friendly_hostname`.

---

### Generator Error Diagnosis

**Missing Output Issues**:

If a service doesn't appear in generated JSON:

1. **Check distribution filtering**:
   - UniFi generator: Only includes `unifi_only` and `both`
   - Cloudflare generator: Only includes `cloudflare_only` and `both`

2. **Verify service has required fields**:
   - For UniFi: `internal_hostname` must be set
   - For Cloudflare: both `internal_hostname` and `public_hostname` should be set

**Generator Validation**:

```bash
# Generate and validate JSON
kcl run main.k > output.json

# Check JSON structure
jq '.unifi' output.json
jq '.cloudflare' output.json

# Validate UniFi output has devices
jq '.unifi.devices | length' output.json

# Validate Cloudflare has tunnels
jq '.cloudflare.tunnels | keys' output.json
```

---

### Common Mistakes Reference

| Symptom | Cause | Solution |
|---------|-------|----------|
| `MAC consistency error` | Cloudflare MAC not in UniFi | Add device or fix MAC typo |
| `DNS loop error` | Public domain in local_service_url | Use internal domain |
| `Hostname too long` | >63 characters | Shorten hostname |
| `Service not in output` | Wrong distribution or missing hostname | Check distribution value |
| `Port validation error` | Port 0 or >65535 | Use valid port |
| `Domain validation error` | UniFi domain not .lan/.local/.home | Use internal domain suffix |
| `Type error: expected int` | Port in quotes | Remove quotes from port |
| `Unclosed bracket` | Missing `]` or `}` | Add closing bracket |
| `Invalid enum value` | Typo in distribution | Use valid enum value |
| `Duplicate key` | Same MAC in multiple tunnels | Use one tunnel per MAC |

---

### Step-by-Step Debugging Workflow

When your configuration fails, follow this order:

**Step 1: Fix Syntax Errors**
```bash
kcl run main.k
```
- Fix all syntax errors first
- Use line numbers from error messages
- Check bracket matching

**Step 2: Fix Type Errors**
```bash
kcl run main.k
```
- Ensure values match expected types
- Remove quotes from numbers
- Check enum values

**Step 3: Fix Validation Errors**
```bash
kcl run main.k
```
- Address check block failures
- Fix MAC addresses
- Correct hostnames
- Verify domains

**Step 4: Verify Generation**
```bash
kcl run main.k > output.json
jq '.' output.json
```
- Check output structure
- Verify all services present
- Validate JSON is well-formed

**Incremental Testing**:

Add configuration incrementally to isolate errors:

```kcl
# Start with minimal config
entity = UniFiEntity {
    friendly_hostname = "test"
    domain = "internal.lan"
    endpoints = [
        UniFiEndpoint { mac_address = "aa:bb:cc:dd:ee:ff" }
    ]
}
```

Validate, then add services one at a time:

```kcl
# Add one service
services = [
    Service { name = "test", port = 8080, protocol = "http" }
]
```

Validate again, continue adding.

---

## Testing and Validation

### Validation Commands

**Basic Syntax Check**:
```bash
kcl run main.k
```
Validates syntax, types, and check blocks. Shows errors if invalid.

**Schema Validation**:
```bash
kcl run schemas/base.k
kcl run schemas/unifi.k
kcl run schemas/cloudflare.k
```

**Generator Testing**:

```bash
# Generate UniFi JSON
kcl run generators/unifi.k > unifi.json

# Generate Cloudflare JSON
kcl run generators/cloudflare.k > cloudflare.json
```

### Output Verification

**Validate JSON Structure**:
```bash
# Check UniFi output
jq '.devices' unifi.json
jq '.default_domain' unifi.json
jq '.site' unifi.json  # UniFi site name (default: "default")

# Check Cloudflare output
jq '.zone_name' cloudflare.json
jq '.tunnels' cloudflare.json
jq '.tunnels | keys' cloudflare.json  # List tunnel MACs
```

**Count Resources**:
```bash
# Count devices
jq '.devices | length' unifi.json

# Count tunnels
jq '.tunnels | length' cloudflare.json

# Count services per tunnel
jq '.tunnels[].services | length' cloudflare.json
```

**Validate Service Distribution**:
```bash
# Check UniFi services (should have unifi_only + both)
jq '.devices[].services' unifi.json

# Check Cloudflare services (should have cloudflare_only + both)
jq '.tunnels[].services[].public_hostname' cloudflare.json
```

### Integration Testing

**Full Configuration Test**:
```bash
# Run unified config
kcl run main.k > output.json

# Verify both sections present
jq 'has("_unifi")' output.json
jq 'has("_cloudflare")' output.json
```

**Error Linking**:

| Error Type | Debugging Section |
|------------|-------------------|
| Syntax errors | [Syntax Error Diagnosis](#syntax-error-diagnosis) |
| Type mismatches | [Type Error Diagnosis](#type-error-diagnosis) |
| Validation failures | [Validation Error Diagnosis](#validation-error-diagnosis) |
| Missing output | [Generator Error Diagnosis](#generator-error-diagnosis) |

---

## Examples

Complete working examples are provided for common use cases:

| Example | Description | Location |
|---------|-------------|----------|
| **Single Service** | One service, dual exposure (internal + external) | [`examples/single-service/`](../examples/single-service/) |
| **Multiple Services** | Device with 3+ services using varied distributions | [`examples/multiple-services/`](../examples/multiple-services/) |
| **Internal-Only** | Services accessible only within local network | [`examples/internal-only/`](../examples/internal-only/) |
| **External-Only** | Services accessible only via Cloudflare Tunnel | [`examples/external-only/`](../examples/external-only/) |
| **Homelab Media Stack** | Complex real-world media server setup | [`examples/homelab-media-stack/`](../examples/homelab-media-stack/) |

Each example includes:
- Complete working `main.k` configuration
- README with explanation and customization guide
- Validation commands and expected output
- Testing instructions

---

## See Also

### Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](getting-started.md) | Installation and first deployment |
| [Dagger Reference](dagger-reference.md) | Dagger module function reference |
| [Terraform Modules](terraform-modules.md) | Standalone Terraform module usage |
| [State Management](state-management.md) | State backends and persistence |
| [Security](security.md) | Security best practices |
| [Troubleshooting](troubleshooting.md) | Common issues and solutions |

### Project Files

| File | Description |
|------|-------------|
| [`kcl/README.md`](../kcl/README.md) | KCL module overview and quick reference |
| [`schemas/`](../schemas/) | Schema source code |
| [`generators/`](../generators/) | Generator source code |
| [`examples/`](../examples/) | Working configuration examples |

### External Resources

- [KCL Documentation](https://kcl-lang.io/docs/) - Official KCL language reference
- [UniFi Controller API](https://ubntwiki.com/products/software/unifi-controller/api) - UniFi API documentation
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) - Cloudflare Tunnel documentation
- [RFC 1123](https://tools.ietf.org/html/rfc1123) - DNS hostname requirements

---

*Generated for unifi-cloudflare-glue. For issues or improvements, see [CONTRIBUTING.md](../CONTRIBUTING.md).*