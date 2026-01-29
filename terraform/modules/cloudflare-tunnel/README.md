# Cloudflare Tunnel Terraform Module

This Terraform module manages Cloudflare Zero Trust Tunnels and their associated DNS records. It works in conjunction with the KCL configuration layer to apply tunnel configurations generated from a unified service definition.

## Purpose

The `cloudflare-tunnel` module provides infrastructure-as-code management for:
- **Cloudflare Tunnels**: Creates secure tunnels from internal services to Cloudflare's edge network
- **Tunnel Configuration**: Manages ingress rules for routing traffic to internal services
- **DNS Records**: Creates CNAME records pointing public hostnames to tunnels

This module bridges the KCL-generated configuration with Cloudflare's infrastructure, enabling external access to internal services without opening firewall ports or exposing IP addresses.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| cloudflare provider | ~> 5.0 |
| random provider | ~> 3.0 |

## Provider Authentication

This module requires authentication with the Cloudflare provider. Configure one of:

1. **Environment variables** (recommended for CI/CD):
   ```bash
   export CLOUDFLARE_API_TOKEN="your-api-token"
   export CLOUDFLARE_ACCOUNT_ID="your-account-id"
   ```

2. **Provider configuration** in your root module:
   ```hcl
   provider "cloudflare" {
     api_token = var.cloudflare_api_token
   }
   ```

**Required API Token Permissions:**
- Zone:Read (for querying zone)
- Zone Settings:Edit (for DNS records)
- Cloudflare Tunnel:Edit (for tunnel management)

## Usage

### Basic Usage with KCL-Generated JSON

```hcl
# Read KCL-generated configuration
locals {
  config = jsondecode(file("${path.module}/cloudflare-config.json"))
}

module "cloudflare_tunnel" {
  source = "./terraform/modules/cloudflare-tunnel"

  config = local.config
}
```

### Example Configuration Structure

The module expects a configuration object matching the KCL Cloudflare generator output:

```hcl
config = {
  zone_name   = "example.com"
  account_id  = "1234567890abcdef1234567890abcdef"
  tunnels     = {
    "aa:bb:cc:dd:ee:ff" = {
      tunnel_name = "home-server"
      mac_address = "aa:bb:cc:dd:ee:ff"
      services    = [
        {
          public_hostname   = "media.example.com"
          local_service_url = "http://jellyfin.internal.lan:8096"
          no_tls_verify     = false
        },
        {
          public_hostname   = "files.example.com"
          local_service_url = "https://nas.internal.lan:443"
          no_tls_verify     = true  # For self-signed certs
        }
      ]
    }
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|----------|
| `config` | Cloudflare Tunnel configuration object | `object` | n/a | yes |
| `config.zone_name` | The Cloudflare DNS zone name | `string` | n/a | yes |
| `config.account_id` | Cloudflare account ID | `string` | n/a | yes |
| `config.tunnels` | Map of MAC addresses to tunnel configurations | `map(object)` | n/a | yes |
| `config.tunnels[mac].tunnel_name` | Name for the tunnel | `string` | n/a | yes |
| `config.tunnels[mac].mac_address` | MAC address of the device | `string` | n/a | yes |
| `config.tunnels[mac].services` | List of services to expose | `list(object)` | n/a | yes |
| `config.tunnels[mac].services[*].public_hostname` | Public-facing hostname | `string` | n/a | yes |
| `config.tunnels[mac].services[*].local_service_url` | Internal service URL | `string` | n/a | yes |
| `config.tunnels[mac].services[*].no_tls_verify` | Skip TLS verification | `bool` | `false` | no |

## Outputs

| Name | Description | Sensitive |
|------|-------------|-----------|
| `tunnel_ids` | Map of MAC address to tunnel ID | no |
| `tunnel_tokens` | Map of MAC address to tunnel token for cloudflared | **yes** |
| `credentials_json` | Map of MAC address to credentials file content | **yes** |
| `public_hostnames` | List of all created public hostnames | no |
| `zone_id` | Cloudflare zone ID | no |
| `tunnel_names` | Map of MAC address to tunnel name | no |
| `record_ids` | Map of record keys to Cloudflare record IDs | no |

## Security Considerations

### Sensitive Data

**Tunnel tokens and credentials are marked as sensitive** to prevent them from appearing in:
- Terraform plan/apply output
- Console logs
- State file diffs (when using remote state)

Access sensitive outputs programmatically:

```hcl
# Write credentials to files for cloudflared
resource "local_file" "tunnel_credentials" {
  for_each = module.cloudflare_tunnel.tunnel_tokens

  filename = "/etc/cloudflared/${each.key}.json"
  content  = module.cloudflare_tunnel.credentials_json[each.key]
}
```

### DNS Loop Prevention

The module validates that `local_service_url` does not contain the `zone_name`. This prevents DNS resolution loops where traffic would route through the public hostname back to the tunnel.

**Valid internal domains:**
- `.internal.lan`
- `.local`
- `.home`
- `.home.arpa`
- `.localdomain`

## Resources Created

### cloudflare_tunnel
Creates one tunnel per MAC address in the configuration.

### cloudflare_tunnel_config
Configures ingress rules for each tunnel:
- One ingress rule per service (maps public_hostname → local_service_url)
- Optional `no_tls_verify` for self-signed certificates
- Catch-all rule returning HTTP 404

### cloudflare_dns_record
Creates CNAME records for each service:
- Points `public_hostname` to `${tunnel_id}.cfargotunnel.com`
- Records are proxied through Cloudflare
- Uses automatic TTL (ttl = 1)

## Error Handling

### Missing Zone
If the specified `zone_name` does not exist in Cloudflare, the data source query will fail with a clear error message.

### DNS Loop Detection
If `local_service_url` contains the `zone_name`, validation will fail with:
```
Error: Invalid value for variable
local_service_url cannot contain zone_name - this would cause a DNS resolution loop
```

## Example: Complete Homelab Setup

```hcl
# Generate config with KCL
resource "null_resource" "kcl_generate" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "cd ${path.root}/../kcl && kcl run main.k > ${path.module}/cloudflare.json"
  }
}

locals {
  cloudflare_config = jsondecode(file("${path.module}/cloudflare.json"))
}

module "cloudflare_tunnel" {
  source = "./terraform/modules/cloudflare-tunnel"

  config = local.cloudflare_config
}

# Example: Output tunnel tokens (sensitive)
output "tunnel_tokens" {
  value     = module.cloudflare_tunnel.tunnel_tokens
  sensitive = true
}
```

## Notes

- Each physical device gets exactly one tunnel (identified by MAC address)
- Multiple services can share the same tunnel
- Tunnel secrets are generated automatically using the `random` provider
- DNS records are automatically created for all service public hostnames
- The module uses `distinct()` to prevent duplicate DNS records when multiple tunnels share a hostname
