# Cloudflare Tunnel Module
# This module manages Cloudflare Tunnels and edge DNS records

# Query existing Cloudflare Zone by name
data "cloudflare_zone" "this" {
  name = var.config.zone_name
}

# Create a Cloudflare Tunnel for each MAC address
resource "cloudflare_tunnel" "this" {
  for_each = var.config.tunnels

  account_id = var.config.account_id
  name       = each.value.tunnel_name
  secret     = base64encode(random_password.tunnel_secret[each.key].result)
}

# Generate random secrets for each tunnel
resource "random_password" "tunnel_secret" {
  for_each = var.config.tunnels

  length  = 32
  special = false
}

# Configure tunnel ingress rules
resource "cloudflare_tunnel_config" "this" {
  for_each = var.config.tunnels

  account_id = var.config.account_id
  tunnel_id  = cloudflare_tunnel.this[each.key].id

  config {
    # Ingress rules for each service
    dynamic "ingress_rule" {
      for_each = each.value.services
      content {
        hostname = ingress_rule.value.public_hostname
        service  = ingress_rule.value.local_service_url

        dynamic "origin_request" {
          for_each = ingress_rule.value.no_tls_verify ? [true] : []
          content {
            no_tls_verify = true
          }
        }
      }
    }

    # Catch-all rule returning 404
    ingress_rule {
      service = "http_status:404"
    }
  }
}

# Create DNS CNAME records for each service public_hostname
resource "cloudflare_record" "tunnel" {
  # Create a unique key for each MAC + service combination
  for_each = {
    for pair in setproduct(
      keys(var.config.tunnels),
      flatten([
        for mac, tunnel in var.config.tunnels : [
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
  value   = "${cloudflare_tunnel.this[each.value.mac].id}.cfargotunnel.com"
  proxied = true
}
