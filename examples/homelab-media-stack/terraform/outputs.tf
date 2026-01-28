# Output Values for Homelab Media Stack
#
# These outputs provide information about the deployed resources
# for verification and configuration of connected services.

# ============================================================================
# UNIFI DNS OUTPUTS
# ============================================================================

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
  description = <<EOF
List of MAC addresses not found in UniFi (if strict_mode is false).
These devices must be connected to the UniFi network before DNS records can be created.
EOF
  value       = module.unifi_dns.missing_devices
}

output "unifi_duplicate_macs" {
  description = "List of MAC addresses that appear multiple times in the configuration"
  value       = module.unifi_dns.duplicate_macs
}

output "unifi_summary" {
  description = "Summary of DNS records created and any issues"
  value       = module.unifi_dns.summary
}

# ============================================================================
# CLOUDFLARE TUNNEL OUTPUTS
# ============================================================================

output "cloudflare_tunnel_ids" {
  description = "Map of MAC address to Cloudflare Tunnel ID"
  value       = module.cloudflare_tunnel.tunnel_ids
}

output "cloudflare_tunnel_tokens" {
  description = <<EOF
Map of MAC address to Cloudflare Tunnel token (sensitive).
Used for cloudflared authentication.

Setup command:
  cloudflared service install <token>
EOF
  value       = module.cloudflare_tunnel.tunnel_tokens
  sensitive   = true
}

output "cloudflare_credentials_json" {
  description = "Map of MAC address to credentials file content (JSON format for cloudflared)"
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

# ============================================================================
# SUMMARY OUTPUT
# ============================================================================

output "deployment_summary" {
  description = "Human-readable summary of the deployment"
  value       = <<EOF

================================================================================
HOMELAB MEDIA STACK - DEPLOYMENT SUMMARY
================================================================================

UNIFI DNS RECORDS:
  - DNS Records: See unifi_dns_records output for full list
  - CNAME Records: See unifi_cname_records output for full list
  - Device IPs: See unifi_device_ips output for assigned IPs
  - Missing Devices: See unifi_missing_devices output (if any)

CLOUDFLARE TUNNELS:
  - Tunnel IDs: See cloudflare_tunnel_ids output
  - Tunnel Names: See cloudflare_tunnel_names output
  - Public Hostnames: See cloudflare_public_hostnames output
  - Zone ID: See cloudflare_zone_id output

NEXT STEPS:
  1. Review UniFi DNS records in UniFi Controller
  2. Retrieve tunnel tokens from the cloudflare_tunnel_tokens output
  3. Configure cloudflared on your media server:
     
     # Install cloudflared (Debian/Ubuntu)
     wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
     sudo dpkg -i cloudflared-linux-amd64.deb
     
     # Install the tunnel service (run for each tunnel)
     sudo cloudflared service install <tunnel_token>

SECURITY NOTES:
  - Tunnel tokens are sensitive - keep them secure!
  - Use 'terraform output -json cloudflare_tunnel_tokens' to retrieve them
  - Never commit tokens to version control

================================================================================
EOF
}
