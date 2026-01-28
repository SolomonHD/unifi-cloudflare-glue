Here is a comprehensive prompt for **Kilocode/OpenSpec** to generate the technical specifications for `unifi-cloudflare-glue`:

---

**Prompt for Kilocode/OpenSpec:**

```
Create technical specifications for the repository "unifi-cloudflare-glue" - a hybrid DNS infrastructure tool that bridges local UniFi network DNS with Cloudflare Tunnel edge DNS using a unified configuration layer.

## Project Overview

Build a monorepo containing:
1. A Terraform module for UniFi local DNS management (multi-NIC device support)
2. A Terraform module for Cloudflare Zero Trust Tunnel management (one tunnel per MAC address)
3. A KCL (Kusion Configuration Language) schema layer that unifies both providers into a single source of truth

The goal is "define once, deploy everywhere" - users describe their infrastructure in KCL (services, MAC addresses, internal hostnames), and the system generates Terraform-compatible JSON for both UniFi local resolution and Cloudflare public exposure.

## Core Architecture Requirements

### 1. UniFi DNS Module (terraform/modules/unifi-dns/)
- Accept JSON input describing devices with multiple NICs
- Each device has a "friendly_hostname" that creates round-robin A-records across all NIC IPs
- Each NIC can have its own hostname (nic_name) and service-specific CNAMEs
- Must query existing UniFi Controller for current IP assignments via data source
- Support validation: fail if MAC not found in UniFi
- Output: DNS records created, missing devices

### 2. Cloudflare Tunnel Module (terraform/modules/cloudflare-tunnel/)
- Accept JSON input mapping MAC addresses to tunnels (one tunnel per MAC)
- Each tunnel has multiple services with:
  - public_hostname (e.g., media.example.com) - creates CNAME to tunnel
  - local_service_url (MUST resolve via UniFi DNS, e.g., http://jellyfin.internal.lan:8096)
- MUST use existing Cloudflare Zone data source (do not create zone)
- Create cloudflare_tunnel resource with remote config (cloudflare_tunnel_config)
- Output: tunnel_id, tunnel_token (for external cloudflared containers), credentials JSON
- CRITICAL: Ingress rules must route to UniFi local hostnames, never to Cloudflare public hostnames (prevent DNS loops)

### 3. KCL Schema Layer (kcl/)
- Define base schema for Entities, Endpoints, Services
- Extend for UniFi-specific (MAC addresses, NICs, internal domains)
- Extend for Cloudflare-specific (tunnels, public hostnames, local_service_urls)
- Validation logic: Ensure all Cloudflare MACs exist in UniFi config
- Generators: Convert unified KCL to UniFi JSON format and Cloudflare JSON format
- Support service categorization: 
  - Both providers (jellyfin, jellyseerr)
  - UniFi-only internal (*arr stack: sonarr, radarr, prowlarr)
  - Cloudflare-only external (paperless-ngx, immich)

## Directory Structure (Stack-Separation Layout)

unifi-cloudflare-glue/
├── terraform/
│   └── modules/
│       ├── unifi-dns/          # Independent TF module
│       └── cloudflare-tunnel/  # Independent TF module
├── kcl/
│   ├── kcl.mod                 # KCL module manifest
│   ├── schemas/
│   │   ├── base.k              # Shared base schemas
│   │   ├── unifi.k             # UniFi extensions
│   │   └── cloudflare.k        # Cloudflare extensions
│   └── generators/
│       ├── unifi.k             # JSON generator for UniFi
│       └── cloudflare.k        # JSON generator for Cloudflare
└── examples/
    └── homelab-media-stack/    # Working example (jellyfin, *arr suite, etc.)

## Data Flow

1. User writes KCL defining servers, MACs, NICs, services with distribution flags (unifi_only, cloudflare_only, both)
2. KCL validation ensures: all Cloudflare MACs exist in UniFi, local_service_urls use internal domains
3. KCL generates:
   - unifi.json: Devices with NICs and internal CNAMEs
   - cloudflare.json: Tunnels keyed by MAC with services pointing to local hostnames
4. Terraform applies unifi.json first (creates local DNS)
5. Terraform applies cloudflare.json (creates tunnels pointing to now-resolvable local hostnames)

## Key Constraints & Safety Requirements

- **No DNS Loops**: Cloudflare local_service_url must use .internal.lan (UniFi) domains, never .example.com (public)
- **MAC Normalization**: Support aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff formats, normalize to lowercase colons
- **One Tunnel Per MAC**: Each physical host gets its own cloudflared tunnel for isolation
- **External Deployment**: Cloudflared containers run outside Terraform (just output tokens), not as Terraform resources
- **Existing Resources**: Both modules must use data sources for existing infrastructure (UniFi site, Cloudflare zone)

## Input/Output Specifications

UniFi Input Schema:
{
  "devices": [{
    "friendly_hostname": "media-server",
    "domain": "internal.lan",
    "service_cnames": ["shared.internal.lan"],
    "nics": [{
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "nic_name": "mgmt",
      "service_cnames": ["specific.internal.lan"]
    }]
  }]
}

Cloudflare Input Schema:
{
  "zone_name": "example.com",
  "cloudflare_account_id": "xxx",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "tunnel-media",
      "services": [{
        "public_hostname": "media.example.com",
        "local_service_url": "http://jellyfin.internal.lan:8096",
        "no_tls_verify": true
      }]
    }
  }
}

## Deliverables to Specify

1. Detailed variable schemas for both Terraform modules
2. KCL schema definitions with validation rules
3. JSON transformation logic (KCL generators)
4. Error handling strategy (missing MACs, duplicate hostnames)
5. Security considerations (tunnel token handling, secret management)
6. Example configurations for the homelab-media-stack (jellyfin, jellyseerr, sonarr, radarr, prowlarr, paperless-ngx, immich)

Generate specifications that are implementation-ready, including type constraints, validation rules, and output formats.
```

---

Use this as the root prompt in Kilocode/OpenSpec, and it will generate the detailed technical specifications for each component (Terraform module specs, KCL schema specs, and integration specs).