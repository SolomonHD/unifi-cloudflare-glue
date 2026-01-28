# Change: Terraform Cloudflare Tunnel Module

## Why

The Cloudflare Tunnel module bridges the KCL-generated configuration with Cloudflare's Zero Trust Tunnel infrastructure. It creates secure tunnels from internal services to Cloudflare's edge network, enabling external access without opening firewall ports or exposing IP addresses. This module manages tunnel creation, ingress rule configuration, and DNS record management for public hostnames.

## What Changes

- Define complete input variable schema matching KCL Cloudflare generator output
- Create data source to query existing Cloudflare Zone by name
- Implement `cloudflare_tunnel` resource creation for each MAC address (one tunnel per device)
- Implement `cloudflare_tunnel_config` resource with ingress rules for each service
- Implement `cloudflare_record` CNAME resources pointing public hostnames to tunnels
- Define outputs for tunnel IDs, tokens (sensitive), credentials JSON, and public hostnames
- Add DNS loop prevention validation (local_service_url cannot contain zone_name)
- Mark tunnel tokens as sensitive in outputs
- Update module README with complete usage documentation

## Impact

- Affected specs: `terraform-module` capability
- Affected code:
  - `terraform/modules/cloudflare-tunnel/variables.tf` - Complete input variable definitions
  - `terraform/modules/cloudflare-tunnel/main.tf` - Data sources, tunnel resources, and DNS records
  - `terraform/modules/cloudflare-tunnel/outputs.tf` - Output definitions with sensitive markings
  - `terraform/modules/cloudflare-tunnel/README.md` - Usage documentation

## Dependencies

- Depends on: Project scaffolding (`project-scaffolding` / 001) must exist
- Soft Depends on: KCL Cloudflare generator (`kcl-cloudflare-generator` / 006) for input format compatibility

## Expected JSON Input Format

The module consumes JSON output from the KCL Cloudflare generator with this structure:

```json
{
  "zone_name": "example.com",
  "account_id": "1234567890abcdef1234567890abcdef",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "home-server",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "services": [
        {
          "public_hostname": "media.example.com",
          "local_service_url": "http://jellyfin.internal.lan:8096",
          "no_tls_verify": false
        },
        {
          "public_hostname": "files.example.com",
          "local_service_url": "https://nas.internal.lan:443",
          "no_tls_verify": true
        }
      ]
    }
  }
}
```
