# Cloudflare Tunnel Module
# This module manages Cloudflare Tunnels and edge DNS records

# ==============================================================================
# Provider Configuration
# ==============================================================================
# Provider configuration is inherited from parent module or configured locally
# When called from glue module: providers (cloudflare, random) are passed explicitly from parent
# When used standalone: providers are configured via required_providers in versions.tf
# No provider blocks here - allows both usage patterns

# ==============================================================================
# Locals
# ==============================================================================

locals {
  # Load config from file if config_file is provided, otherwise use config
  effective_config = var.config_file != "" ? jsondecode(file(var.config_file)) : var.config

  # Validate that at least one of config or config_file is provided
  _validate_config = local.effective_config != null ? true : tobool("ERROR: Either config or config_file must be provided")

  # Allow override of account_id and zone_name from variables (takes precedence over config)
  effective_account_id = var.account_id_override != "" ? var.account_id_override : local.effective_config.account_id
  effective_zone_name  = var.zone_name_override != "" ? var.zone_name_override : local.effective_config.zone_name
}

# Query existing Cloudflare Zone by name
data "cloudflare_zone" "this" {
  filter = {
    name = local.effective_zone_name
  }
}

# Create a Cloudflare Tunnel for each MAC address
resource "cloudflare_zero_trust_tunnel_cloudflared" "this" {
  for_each = local.effective_config.tunnels

  account_id    = local.effective_account_id
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

  account_id = local.effective_account_id
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
    for item in flatten([
      for mac, tunnel in local.effective_config.tunnels : [
        for idx, svc in tunnel.services : {
          key      = "${mac}-${idx}"
          mac      = mac
          hostname = svc.public_hostname
        }
      ]
      ]) : item.key => {
      mac      = item.mac
      hostname = item.hostname
    }
  }

  zone_id = data.cloudflare_zone.this.id
  name    = each.value.hostname
  type    = "CNAME"
  content = "${cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id}.cfargotunnel.com"
  proxied = true
  ttl     = 1 # 1 = automatic TTL

  # Prevent unnecessary recreation when zone_id appears as "known after apply"
  # The zone_id doesn't actually change, but the data source makes it appear computed
  lifecycle {
    ignore_changes = [zone_id]
  }
}
