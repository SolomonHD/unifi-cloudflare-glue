# Output values for Combined Glue Module
# All outputs from both unifi-dns and cloudflare-tunnel sub-modules are exposed here
# This allows consumers of the combined module to access all information from both deployments
# Outputs are conditional based on which modules were deployed

# ==============================================================================
# UniFi DNS Outputs
# ==============================================================================

output "unifi_dns_records" {
  description = "Map of device hostname to DNS record FQDN (empty if unifi not deployed)"
  value       = length(module.unifi_dns) > 0 ? module.unifi_dns[0].dns_records : {}
}

output "unifi_cname_records" {
  description = "Map of CNAME record name to target FQDN (empty if unifi not deployed)"
  value       = length(module.unifi_dns) > 0 ? module.unifi_dns[0].cname_records : {}
}

output "unifi_device_ips" {
  description = "Map of MAC address to assigned IP address (empty if unifi not deployed)"
  value       = length(module.unifi_dns) > 0 ? module.unifi_dns[0].device_ips : {}
}

output "unifi_missing_devices" {
  description = "List of MAC addresses not found in the UniFi Controller (empty if unifi not deployed)"
  value       = length(module.unifi_dns) > 0 ? module.unifi_dns[0].missing_devices : []
}

output "unifi_duplicate_macs" {
  description = "List of MAC addresses that appear multiple times in the configuration (empty if unifi not deployed)"
  value       = length(module.unifi_dns) > 0 ? module.unifi_dns[0].duplicate_macs : []
}

output "unifi_summary" {
  description = "Summary of DNS records created and any issues (empty if unifi not deployed)"
  value = length(module.unifi_dns) > 0 ? module.unifi_dns[0].summary : {
    records_created = 0
    cnames_created  = 0
    devices_found   = 0
    devices_missing = 0
    duplicate_macs  = []
    warnings        = []
  }
}

output "unifi_service_cnames_created" {
  description = "Service CNAMEs from configuration that were created as DNS records (empty if unifi not deployed)"
  value       = length(module.unifi_dns) > 0 ? module.unifi_dns[0].service_cnames_created : []
}

# ==============================================================================
# Cloudflare Tunnel Outputs
# ==============================================================================

output "cloudflare_tunnel_ids" {
  description = "Map of MAC address to Cloudflare Tunnel ID (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].tunnel_ids : {}
}

output "cloudflare_credentials_json" {
  description = "Map of MAC address to credentials file content (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].credentials_json : {}
  sensitive   = true
}

output "cloudflare_public_hostnames" {
  description = "List of all public hostnames created for tunnel services (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].public_hostnames : []
}

output "cloudflare_zone_id" {
  description = "The Cloudflare zone ID used for DNS records (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].zone_id : ""
}

output "cloudflare_tunnel_names" {
  description = "Map of MAC address to tunnel name (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].tunnel_names : {}
}

output "cloudflare_tunnel_tokens" {
  description = "Map of MAC address to tunnel token (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].tunnel_tokens : {}
  sensitive   = true
}

output "cloudflare_record_ids" {
  description = "Map of record keys to Cloudflare record IDs (empty if cloudflare not deployed)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].record_ids : {}
}

# ==============================================================================
# Alias Outputs (for backward compatibility with standalone module naming)
# ==============================================================================
# These outputs provide the same values as the cloudflare_* outputs above
# but with the standalone cloudflare-tunnel module naming convention.
# This allows get_tunnel_secrets to work regardless of which module created the state.

output "tunnel_ids" {
  description = "Alias for cloudflare_tunnel_ids (standalone module naming)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].tunnel_ids : {}
}

output "tunnel_tokens" {
  description = "Alias for cloudflare_tunnel_tokens (standalone module naming)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].tunnel_tokens : {}
  sensitive   = true
}

output "credentials_json" {
  description = "Alias for cloudflare_credentials_json (standalone module naming)"
  value       = length(module.cloudflare_tunnel) > 0 ? module.cloudflare_tunnel[0].credentials_json : {}
  sensitive   = true
}
