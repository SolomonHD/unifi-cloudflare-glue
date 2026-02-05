# Terraform Modules

The Terraform modules in this repository can be consumed directly from external projects using Git-based module sourcing. This allows you to use these modules as infrastructure dependencies without cloning the entire repository.

## Module Source

Terraform supports fetching modules directly from Git repositories using the following syntax:

```hcl
source = "github.com/OWNER/REPOSITORY//SUBDIR?ref=VERSION"
```

For this project:
- **Repository**: `github.com/SolomonHD/unifi-cloudflare-glue`
- **Module paths**: `//terraform/modules/unifi-dns` or `//terraform/modules/cloudflare-tunnel`
- **Version**: Use `?ref=v0.1.0` to pin to a specific release (recommended)

## Module: unifi-dns

Manages UniFi DNS records for local network resolution.

```hcl
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"

  config = {
    devices = [
      {
        friendly_hostname = "media-server"
        domain            = "internal.lan"
        nics = [
          {
            mac_address = "aa:bb:cc:dd:ee:01"
          }
        ]
      }
    ]
    default_domain = "internal.lan"
    site           = "default"
  }

  strict_mode = false
}
```

### Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `config` | object | ✅ | Device and DNS configuration |
| `strict_mode` | bool | ❌ | Enable strict validation (default: false) |

## Module: cloudflare-tunnel

Manages Cloudflare Tunnels and DNS records for remote access.

```hcl
module "cloudflare_tunnel" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/cloudflare-tunnel?ref=v0.1.0"

  config = {
    zone_name  = "example.com"
    account_id = "your-cloudflare-account-id"
    tunnels = {
      "aa:bb:cc:dd:ee:ff" = {
        tunnel_name = "home-server"
        mac_address = "aa:bb:cc:dd:ee:ff"
        services = [
          {
            public_hostname   = "media.example.com"
            local_service_url = "http://jellyfin.internal.lan:8096"
            no_tls_verify     = false
          }
        ]
      }
    }
  }
}
```

### Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `config` | object | ✅ | Tunnel and service configuration |

## Version Pinning

Always pin to specific versions in production:

```hcl
# ✅ Recommended - pinned version
source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"

# ⚠️ Not recommended - latest main (unpredictable changes)
source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns"
```

### Finding Available Versions

- Check [GitHub releases](https://github.com/SolomonHD/unifi-cloudflare-glue/releases)
- Review [CHANGELOG.md](../CHANGELOG.md) for version changes
- Test new versions in non-production environments first

## Authentication

### UniFi Authentication

The `unifi-dns` module requires UniFi credentials via environment variables:

```bash
# Option 1: API Key (recommended)
export UNIFI_API_KEY="your-api-key"

# Option 2: Username/Password
export UNIFI_USERNAME="admin"
export UNIFI_PASSWORD="your-password"
```

### Cloudflare Authentication

The `cloudflare-tunnel` module requires a Cloudflare API token:

```bash
export CLOUDFLARE_API_TOKEN="your-api-token"
```

**Required token permissions:**
- Zone:Read
- DNS:Edit
- Cloudflare Tunnel:Edit

## Using with Local State

For development or testing, you can use local state:

```hcl
# No backend configuration needed (local state default)
```

## Using with Remote Backends

For production, configure a remote backend:

```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "unifi-cloudflare/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

## Complete Example

```hcl
terraform {
  required_version = ">= 1.5.0"
  
  backend "s3" {
    bucket = "my-terraform-state"
    key    = "homelab/dns.tfstate"
    region = "us-east-1"
  }
}

# UniFi DNS for local resolution
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"

  config = {
    devices = [
      {
        friendly_hostname = "nas"
        domain            = "internal.lan"
        nics = [
          { mac_address = "aa:bb:cc:dd:ee:01" }
        ]
      },
      {
        friendly_hostname = "media-server"
        domain            = "internal.lan"
        nics = [
          { mac_address = "aa:bb:cc:dd:ee:02" }
        ]
      }
    ]
    default_domain = "internal.lan"
    site           = "default"
  }
}

# Cloudflare Tunnel for remote access
module "cloudflare_tunnel" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/cloudflare-tunnel?ref=v0.1.0"

  config = {
    zone_name  = "example.com"
    account_id = "your-account-id"
    tunnels = {
      "aa:bb:cc:dd:ee:02" = {
        tunnel_name = "media-server"
        mac_address = "aa:bb:cc:dd:ee:02"
        services = [
          {
            public_hostname   = "media.example.com"
            local_service_url = "http://media-server.internal.lan:8096"
            no_tls_verify     = false
          }
        ]
      }
    }
  }
}
```

## Integration with Dagger

While these modules can be used standalone, they are also used internally by the Dagger module for containerized deployments. See [Dagger Reference](dagger-reference.md) for orchestrated deployment options.
