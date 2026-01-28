# Homelab Media Stack Example

This example demonstrates a complete homelab media stack configuration using `unifi-cloudflare-glue`.

## Overview

This example configures:
- Media services (Plex, Sonarr, Radarr, etc.)
- Network-attached storage (NAS)
- Download clients
- Monitoring tools

Each service is configured with:
- Local DNS resolution via UniFi
- Remote access via Cloudflare Tunnel
- Proper categorization and organization

## Structure

```
homelab-media-stack/
├── README.md           # This file
├── main.k              # Main KCL configuration
├── services/           # Service definitions
│   ├── media.k         # Media services (Plex, Jellyfin)
│   ├── automation.k    # Automation (Sonarr, Radarr)
│   └── monitoring.k    # Monitoring tools
└── terraform/          # Terraform configurations
    ├── unifi/          # UniFi-specific terraform
    └── cloudflare/     # Cloudflare-specific terraform
```

## Prerequisites

- UniFi controller with existing network setup
- Cloudflare account with Tunnel credentials
- KCL installed
- Terraform >= 1.5.0

## Usage

1. Define your services in `main.k`
2. Generate configurations:
   ```bash
   kcl run main.k
   ```
3. Apply to UniFi:
   ```bash
   cd terraform/unifi
   terraform init
   terraform apply
   ```
4. Apply to Cloudflare:
   ```bash
   cd terraform/cloudflare
   terraform init
   terraform apply
   ```

## Notes

- MAC addresses must be in lowercase colon format (e.g., `aa:bb:cc:dd:ee:ff`)
- Each device gets exactly one Cloudflare Tunnel
- Internal domains are used for `local_service_url` to prevent DNS loops
