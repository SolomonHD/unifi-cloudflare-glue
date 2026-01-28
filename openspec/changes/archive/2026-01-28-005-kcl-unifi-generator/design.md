# Design: KCL UniFi JSON Generator

## Overview

The UniFi generator transforms high-level KCL configuration into Terraform-compatible JSON. This document describes the architecture, data flow, and key algorithms.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     UniFiConfig (KCL)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ UniFiEntity │  │ UniFiEntity │  │   UniFiController   │  │
│  │  (device 1) │  │  (device 2) │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘  │
└─────────┼────────────────┼──────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              generate_unifi_config()                         │
│                      (transform)                             │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    UniFi JSON Output                         │
│  {                                                           │
│    "devices": [{...}, {...}],                               │
│    "default_domain": "internal.lan"                         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Data Transformations

### 1. Entity to Device Mapping

Each [`UniFiEntity`](../../kcl/schemas/unifi.k:98) becomes a device record:

```kcl
{
    friendly_hostname: entity.friendly_hostname
    domain: entity.domain
    service_cnames: entity.service_cnames  # Device-level CNAMEs
    nics: [...]  # From entity.endpoints
}
```

### 2. Endpoint to NIC Mapping

Each [`UniFiEndpoint`](../../kcl/schemas/unifi.k:34) becomes a NIC record:

```kcl
{
    mac_address: normalize_mac(endpoint.mac_address)
    nic_name: endpoint.nic_name
    service_cnames: endpoint.service_cnames
}
```

### 3. Service Filtering

Services are filtered based on distribution:

```kcl
# Include services for UniFi DNS
unifi_services = [
    svc for svc in entity.services
    if svc.distribution in ["unifi_only", "both"]
]
```

## Key Algorithms

### MAC Address Normalization

Reuse the existing [`normalize_mac()`](../../kcl/schemas/base.k:37) function:

```kcl
normalize_mac = lambda mac: str -> str {
    no_colons = mac.replace(":", "")
    no_hyphens = no_colons.replace("-", "")
    cleaned = no_hyphens.lower()
    "${cleaned[0:2]}:${cleaned[2:4]}:${cleaned[4:6]}:${cleaned[6:8]}:${cleaned[8:10]}:${cleaned[10:12]}"
}
```

### Service CNAME Generation

Device-level CNAMEs come from `entity.service_cnames`. These are passed through as-is, assuming they already include the domain suffix if needed.

### FQDN Construction

Full DNS names are constructed by appending the domain:

```kcl
fqdn = "${hostname}.${domain}"
```

## Output Schema

The generator produces JSON matching this structure:

```json
{
  "devices": [{
    "friendly_hostname": "media-server",
    "domain": "internal.lan",
    "service_cnames": ["storage.internal.lan"],
    "nics": [{
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "nic_name": "eth0",
      "service_cnames": ["nas.internal.lan"]
    }]
  }],
  "default_domain": "internal.lan"
}
```

## Error Handling

The generator relies on KCL schema validation:

1. **MAC Validation**: Handled by [`UniFiEndpoint`](../../kcl/schemas/unifi.k:34) check blocks
2. **Hostname Validation**: Handled by [`UniFiEntity`](../../kcl/schemas/unifi.k:98) check blocks
3. **Domain Safety**: Handled by [`UniFiConfig`](../../kcl/schemas/unifi.k:187) check blocks

Runtime errors (during generation) should not occur if schemas are valid.

## Testing Strategy

1. **Unit Tests**: Test transformation functions with sample data
2. **Integration Tests**: Run `kcl run` and validate JSON output
3. **Schema Validation**: Verify output matches expected Terraform input
