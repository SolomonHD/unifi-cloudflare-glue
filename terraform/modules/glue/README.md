# Combined Glue Module

A Terraform module that combines the [`unifi-dns`](../unifi-dns/) and [`cloudflare-tunnel`](../cloudflare-tunnel/) modules into a single atomic deployment. This eliminates provider conflicts when using shared Terraform state.

## Purpose

When using the `deploy()` function with persistent local state (`--state-dir`), both the UniFi DNS and Cloudflare Tunnel deployments share the same state file, causing provider conflicts. The Cloudflare deployment tries to initialize the UniFi provider because it sees UniFi resources in the shared state, and vice versa.

This combined module solves that problem by:

1. **Configuring both providers at the root level** - Both `filipowm/unifi` and `cloudflare/cloudflare` providers are initialized once
2. **Calling both sub-modules** - The module wraps both `unifi-dns` and `cloudflare-tunnel`
3. **Enforcing deployment order** - Cloudflare Tunnel waits for UniFi DNS completion via explicit `depends_on`
4. **Exposing all outputs** - All outputs from both sub-modules are available

## Prerequisites

Before using this module, you need:

- **UniFi Controller Access**:
  - URL of your UniFi controller (e.g., `https://unifi.local:8443`)
  - Either an API key OR username/password credentials
  - Site name where DNS records will be created

- **Cloudflare Access**:
  - Cloudflare API token with permissions:
    - `Zone:Read`
    - `DNS:Edit`
    - `Cloudflare Tunnel:Edit`
  - Zone name (e.g., `example.com`)
  - Account ID

- **Configuration Files** (or objects):
  - UniFi DNS configuration (devices, MAC addresses, domains)
  - Cloudflare Tunnel configuration (tunnels, services, public hostnames)

## Usage

### Basic Usage with Config Files

```hcl
module "glue" {
  source = "path/to/unifi-cloudflare-glue/terraform/modules/glue"

  # UniFi configuration file
  unifi_config_file = "${path.module}/unifi-config.json"

  # Cloudflare configuration file
  cloudflare_config_file = "${path.module}/cloudflare-config.json"

  # UniFi provider settings
  unifi_url     = "https://unifi.local:8443"
  unifi_api_key = var.unifi_api_key  # Or use unifi_username/unifi_password

  # Cloudflare provider settings
  cloudflare_token = var.cloudflare_token
}
```

### Usage with Config Objects

```hcl
module "glue" {
  source = "path/to/unifi-cloudflare-glue/terraform/modules/glue"

  # UniFi configuration object
  unifi_config = {
    version       = "1.0"
    default_domain = "home.local"
    site          = "default"
    devices = [
      {
        friendly_hostname = "nas"
        domain            = "home.local"
        nics = [
          {
            nic_name    = "eth0"
            mac_address = "aa:bb:cc:dd:ee:ff"
            service_cnames = ["storage.home.local", "backup.home.local"]
          }
        ]
        service_cnames = ["files.home.local"]
      }
    ]
  }

  # Cloudflare configuration object
  cloudflare_config = {
    zone_name  = "example.com"
    account_id = "your-account-id"
    tunnels = {
      "aa:bb:cc:dd:ee:ff" = {
        tunnel_name = "nas-tunnel"
        mac_address = "aa:bb:cc:dd:ee:ff"
        services = [
          {
            public_hostname   = "nas.example.com"
            local_service_url = "http://nas.home.local:5000"
            no_tls_verify     = false
          }
        ]
      }
    }
  }

  # Provider settings
  unifi_url        = "https://unifi.local:8443"
  unifi_api_key    = var.unifi_api_key
  cloudflare_token = var.cloudflare_token
}
```

### Complete Example with All Options

```hcl
module "glue" {
  source = "path/to/unifi-cloudflare-glue/terraform/modules/glue"

  # Configuration (using files)
  unifi_config_file      = "${path.module}/config/unifi.json"
  cloudflare_config_file = "${path.module}/config/cloudflare.json"

  # UniFi provider settings
  unifi_url      = "https://unifi.local:8443"
  api_url        = ""  # Optional: defaults to unifi_url
  unifi_api_key  = var.unifi_api_key
  unifi_username = ""  # Alternative to API key
  unifi_password = ""  # Alternative to API key
  unifi_insecure = true  # For self-signed certificates

  # Module behavior
  strict_mode = false  # Set true to fail on missing MAC addresses

  # Cloudflare provider settings
  cloudflare_token = var.cloudflare_token
}

# Access outputs
output "dns_records" {
  value = module.glue.unifi_dns_records
}

output "tunnel_credentials" {
  value     = module.glue.cloudflare_credentials_json
  sensitive = true
}
```

## Input Variables

### UniFi Configuration

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `unifi_config` | `any` | `null` | UniFi DNS configuration object. Either this or `unifi_config_file` must be provided. |
| `unifi_config_file` | `string` | `""` | Path to JSON file with UniFi DNS configuration. Either this or `unifi_config` must be provided. |

### Cloudflare Configuration

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `cloudflare_config` | `object` | `null` | Cloudflare Tunnel configuration object. Either this or `cloudflare_config_file` must be provided. |
| `cloudflare_config_file` | `string` | `""` | Path to JSON file with Cloudflare Tunnel configuration. Either this or `cloudflare_config` must be provided. |

### UniFi Provider Settings

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `unifi_url` | `string` | (required) | URL of the UniFi controller (e.g., `https://unifi.local:8443`) |
| `api_url` | `string` | `""` | URL of the UniFi API. Defaults to `unifi_url` if not set. |
| `unifi_api_key` | `string` | `""` | UniFi API key for authentication. Mutually exclusive with username/password. |
| `unifi_username` | `string` | `""` | UniFi username for authentication. Use with `unifi_password`. |
| `unifi_password` | `string` | `""` | UniFi password for authentication. Use with `unifi_username`. |
| `unifi_insecure` | `bool` | `false` | Skip TLS certificate verification. Useful for self-signed certificates. |

### Module Behavior

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `strict_mode` | `bool` | `false` | If `true`, fail if any MAC addresses are not found in UniFi. If `false`, track missing MACs in output. |

### Cloudflare Provider Settings

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `cloudflare_token` | `string` | (required) | Cloudflare API token with Zone:Read, DNS:Edit, and Cloudflare Tunnel:Edit permissions. |

## Outputs

### UniFi DNS Outputs

| Name | Type | Description |
|------|------|-------------|
| `unifi_dns_records` | `map(string)` | Map of device hostname to DNS record FQDN |
| `unifi_cname_records` | `map(object)` | Map of CNAME record name to target FQDN |
| `unifi_device_ips` | `map(string)` | Map of MAC address to assigned IP address (only found devices) |
| `unifi_missing_devices` | `list(string)` | List of MAC addresses not found in UniFi Controller |
| `unifi_duplicate_macs` | `list(string)` | List of MAC addresses that appear multiple times in configuration |
| `unifi_summary` | `object` | Summary of DNS records created and any issues |
| `unifi_service_cnames_created` | `list(string)` | Service CNAMEs that were created as DNS records |

### Cloudflare Tunnel Outputs

| Name | Type | Description |
|------|------|-------------|
| `cloudflare_tunnel_ids` | `map(string)` | Map of MAC address to Cloudflare Tunnel ID |
| `cloudflare_credentials_json` | `map(string)` | Map of MAC address to credentials file content (sensitive) |
| `cloudflare_public_hostnames` | `list(string)` | List of all public hostnames created for tunnel services |
| `cloudflare_zone_id` | `string` | The Cloudflare zone ID used for DNS records |
| `cloudflare_tunnel_names` | `map(string)` | Map of MAC address to tunnel name |
| `cloudflare_record_ids` | `map(string)` | Map of record keys to Cloudflare record IDs |

## When to Use This Module vs Individual Modules

### Use the Combined Module (glue) When:

- **You want atomic deployment** - Both UniFi DNS and Cloudflare Tunnel are deployed together
- **You're using shared Terraform state** - This avoids provider conflicts
- **You want explicit dependency management** - Cloudflare Tunnel waits for UniFi DNS
- **You're using the KCL-generated configuration** - The natural output is to deploy both together

### Use Individual Modules When:

- **You need selective deployment** - Only deploy UniFi DNS or only Cloudflare Tunnel
- **Different teams manage each component** - Separate responsibilities
- **Different credentials/permissions** - Can't use a single Terraform run
- **Testing/debugging** - Troubleshoot one component at a time

## Deployment Order

The combined module enforces this deployment order:

1. **UniFi DNS First**:
   - Lookup devices by MAC address in UniFi Controller
   - Create DNS A-records for each device
   - Create CNAME records for service aliases
   - Output resolved IP addresses

2. **Cloudflare Tunnel Second** (depends on UniFi DNS):
   - Create Cloudflare Tunnels for each MAC address
   - Create public DNS records pointing to tunnels
   - Tunnel services reference internal hostnames that now resolve

This order ensures that when Cloudflare Tunnel services start, they can resolve internal hostnames to IP addresses.

## Configuration File Format

### UniFi Configuration (JSON)

```json
{
  "version": "1.0",
  "default_domain": "home.local",
  "site": "default",
  "devices": [
    {
      "friendly_hostname": "nas",
      "domain": "home.local",
      "nics": [
        {
          "nic_name": "eth0",
          "mac_address": "aa:bb:cc:dd:ee:ff",
          "service_cnames": ["storage.home.local"]
        }
      ],
      "service_cnames": ["files.home.local"]
    }
  ]
}
```

### Cloudflare Configuration (JSON)

```json
{
  "zone_name": "example.com",
  "account_id": "your-account-id",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "nas-tunnel",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "services": [
        {
          "public_hostname": "nas.example.com",
          "local_service_url": "http://nas.home.local:5000",
          "no_tls_verify": false
        }
      ]
    }
  }
}
```

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.5.0 |
| filipowm/unifi | ~> 1.0 |
| cloudflare/cloudflare | ~> 5.0 |
| hashicorp/random | ~> 3.0 |

## Notes

- **Provider Configuration**: Both providers are configured at the root module level to avoid conflicts
- **Relative Paths**: The module uses relative paths (`../unifi-dns/` and `../cloudflare-tunnel/`) for sub-modules
- **Passthrough Pattern**: This is a thin wrapper module - all logic remains in the sub-modules
- **Sensitive Outputs**: Cloudflare credentials are marked as sensitive and won't be displayed in plain text
