# Output values for Combined Glue Module
# All outputs from both unifi-dns and cloudflare-tunnel sub-modules are exposed here
# This allows consumers of the combined module to access all information from both deployments

# ==============================================================================
# UniFi DNS Outputs
# ==============================================================================

output "unifi_dns_records" {
  description = "Map of device hostname to DNS record FQDN"
  value       = module.unifi_dns.dns_records
}

output "unifi_cname_records" {
  description = "Map of CNAME record name to target FQDN"
  value       = module.unifi_dns.cname_records
}

output "unifi_device_ips" {
  description = "Map of MAC address to assigned IP address (only includes found devices)"
  value       = module.unifi_dns.device_ips
}

output "unifi_missing_devices" {
  description = "List of MAC addresses not found in the UniFi Controller (these devices were skipped)"
  value       = module.unifi_dns.missing_devices
}

output "unifi_duplicate_macs" {
  description = "List of MAC addresses that appear multiple times in the configuration (warning)"
  value       = module.unifi_dns.duplicate_macs
}

output "unifi_summary" {
  description = "Summary of DNS records created and any issues"
  value       = module.unifi_dns.summary
}

output "unifi_service_cnames_created" {
  description = "Service CNAMEs from configuration that were created as DNS records"
  value       = module.unifi_dns.service_cnames_created
}

# ==============================================================================
# Cloudflare Tunnel Outputs
# ==============================================================================

output "cloudflare_tunnel_ids" {
  description = "Map of MAC address to Cloudflare Tunnel ID"
  value       = module.cloudflare_tunnel.tunnel_ids
}

output "cloudflare_credentials_json" {
  description = "Map of MAC address to credentials file content (sensitive) - JSON format for cloudflared"
  value       = module.cloudflare_tunnel.credentials_json
  sensitive   = true
}

output "cloudflare_public_hostnames" {
  description = "List of all public hostnames created for tunnel services"
  value       = module.cloudflare_tunnel.public_hostnames
}

output "cloudflare_zone_id" {
  description = "The Cloudflare zone ID used for DNS records"
  value       = module.cloudflare_tunnel.zone_id
}

output "cloudflare_tunnel_names" {
  description = "Map of MAC address to tunnel name"
  value       = module.cloudflare_tunnel.tunnel_names
}

output "cloudflare_record_ids" {
  description = "Map of record keys to Cloudflare record IDs"
  value       = module.cloudflare_tunnel.record_ids
}
