# Cloudflare Tunnel Terraform Module

This Terraform module manages Cloudflare Tunnels and edge DNS records.

## Purpose

The `cloudflare-tunnel` module provides infrastructure-as-code management for Cloudflare Tunnels and their associated DNS records. It works in conjunction with the KCL configuration layer to apply tunnel configurations generated from a unified service definition.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| cloudflare provider | ~> 4.0 |

## Usage

```hcl
module "cloudflare_tunnel" {
  source = "./terraform/modules/cloudflare-tunnel"

  # Configuration will be loaded from KCL-generated JSON
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| (TBD) | (To be defined) | - | - | - |

## Outputs

| Name | Description |
|------|-------------|
| (TBD) | (To be defined) |

## Notes

- This module uses the `cloudflare/cloudflare` provider
- Configuration is generated from KCL schemas and applied via Terraform
- Each physical device gets exactly one tunnel
- `local_service_url` uses internal domains only to prevent DNS loops
