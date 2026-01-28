# UniFi DNS Terraform Module

This Terraform module manages DNS records in UniFi network controllers.

## Purpose

The `unifi-dns` module provides infrastructure-as-code management for UniFi's local DNS records. It works in conjunction with the KCL configuration layer to apply DNS entries generated from a unified service definition.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| unifi provider | ~> 0.41 |

## Usage

```hcl
module "unifi_dns" {
  source = "./terraform/modules/unifi-dns"

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

- This module uses the `paultyng/unifi` provider
- Configuration is generated from KCL schemas and applied via Terraform
- MAC addresses are normalized to lowercase colon format
