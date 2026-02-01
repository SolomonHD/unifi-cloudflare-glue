# Cloudflare Tunnel Module
# This module manages Cloudflare Tunnels and edge DNS records

# ==============================================================================
# Locals
# ==============================================================================

locals {
  # Load config from file if config_file is provided, otherwise use config
  effective_config = var.config_file != "" ? jsondecode(file(var.config_file)) : var.config

  # Validate that at least one of config or config_file is provided
  _validate_config = local.effective_config != null ? true : tobool("ERROR: Either config or config_file must be provided")
}

# Query existing Cloudflare Zone by name
data "cloudflare_zone" "this" {
  filter = {
    name = local.effective_config.zone_name
  }
}

# Create a Cloudflare Tunnel for each MAC address
resource "cloudflare_zero_trust_tunnel_cloudflared" "this" {
  for_each = local.effective_config.tunnels

  account_id    = local.effective_config.account_id
  name          = each.value.tunnel_name
  tunnel_secret = base64encode(random_password.tunnel_secret[each.key].result)
}

# Generate random secrets for each tunnel
resource "random_password" "tunnel_secret" {
  for_each = local.effective_config.tunnels

  length  = 32
  special = false
}

# Configure tunnel ingress rules
resource "cloudflare_zero_trust_tunnel_cloudflared_config" "this" {
  for_each = local.effective_config.tunnels

  account_id = local.effective_config.account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id

  config = {
    ingress = concat(
      # Service ingress rules
      [
        for svc in each.value.services : {
          hostname = svc.public_hostname
          service  = svc.local_service_url
          origin_request = svc.no_tls_verify ? {
            no_tls_verify = true
          } : {}
        }
      ],
      # Catch-all rule
      [{
        service = "http_status:404"
      }]
    )
  }
}

# Create DNS CNAME records for each service public_hostname
resource "cloudflare_dns_record" "tunnel" {
  # Create a unique key for each MAC + service combination
  for_each = {
    for pair in setproduct(
      keys(local.effective_config.tunnels),
      flatten([
        for mac, tunnel in local.effective_config.tunnels : [
          for idx, svc in tunnel.services : {
            mac      = mac
            index    = idx
            hostname = svc.public_hostname
          }
        ]
      ])
      ) : "${pair[0]}-${pair[1].index}" => {
      mac      = pair[0]
      hostname = pair[1].hostname
    }
  }

  zone_id = data.cloudflare_zone.this.id
  name    = each.value.hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id}.cfargotunnel.com"
  proxied = true
  ttl     = 1 # 1 = automatic TTL
}
