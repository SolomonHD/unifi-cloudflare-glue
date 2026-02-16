# Output values for Cloudflare Tunnel module
# These expose useful information after apply

output "tunnel_ids" {
  description = "Map of MAC address to Cloudflare Tunnel ID"
  value = {
    for mac, tunnel in cloudflare_zero_trust_tunnel_cloudflared.this : mac => tunnel.id
  }
}

output "credentials_json" {
  description = "Map of MAC address to credentials file content (sensitive) - JSON format for cloudflared"
  value = {
    for mac, tunnel in cloudflare_zero_trust_tunnel_cloudflared.this : mac => jsonencode({
      AccountTag   = local.effective_config.account_id
      TunnelID     = tunnel.id
      TunnelName   = tunnel.name
      TunnelSecret = base64encode(random_password.tunnel_secret[mac].result)
    })
  }
  sensitive = true
}

output "public_hostnames" {
  description = "List of all public hostnames created for tunnel services"
  value = distinct([
    for record in cloudflare_dns_record.tunnel : record.name
  ])
}

output "zone_id" {
  description = "The Cloudflare zone ID used for DNS records"
  value       = data.cloudflare_zone.this.id
}

output "tunnel_names" {
  description = "Map of MAC address to tunnel name"
  value = {
    for mac, tunnel in cloudflare_zero_trust_tunnel_cloudflared.this : mac => tunnel.name
  }
}

output "record_ids" {
  description = "Map of record keys to Cloudflare record IDs"
  value = {
    for key, record in cloudflare_dns_record.tunnel : key => record.id
  }
}

output "tunnel_tokens" {
  description = "Map of MAC address to tunnel token (base64-encoded tunnel_secret for cloudflared service install)"
  value = {
    for mac, tunnel in cloudflare_zero_trust_tunnel_cloudflared.this : mac => base64encode(random_password.tunnel_secret[mac].result)
  }
  sensitive = true
}
