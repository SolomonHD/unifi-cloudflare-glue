# Output values for UniFi DNS module
# These expose useful information after apply

# ==============================================================================
# DNS Records Output
# ==============================================================================

output "dns_records" {
  description = "Map of device hostname to DNS record FQDN"
  value = {
    for name, record in unifi_dns_record.dns_record : name => record.name
  }
}

# ==============================================================================
# CNAME Records Output
# ==============================================================================

output "cname_records" {
  description = "Map of CNAME record name to target FQDN"
  value = {
    for key, record in unifi_dns_record.cname_record : key => {
      name   = record.name
      type   = record.type
      target = record.record
    }
  }
}

# ==============================================================================
# Device IPs Output
# ==============================================================================

output "device_ips" {
  description = "Map of MAC address to assigned IP address (only includes found devices)"
  value       = { for mac, info in local.found_macs : mac => info.ip }
}

# ==============================================================================
# Missing Devices Output
# ==============================================================================

output "missing_devices" {
  description = "List of MAC addresses not found in the UniFi Controller (these devices were skipped)"
  value       = local.missing_macs_unique
}

# ==============================================================================
# Duplicate MACs Warning Output
# ==============================================================================

output "duplicate_macs" {
  description = "List of MAC addresses that appear multiple times in the configuration (warning)"
  value       = length(local.duplicate_macs) > 0 ? local.duplicate_macs : []
}

# ==============================================================================
# Summary Output
# ==============================================================================

output "summary" {
  description = "Summary of DNS records created and any issues"
  value = {
    records_created = length(unifi_dns_record.dns_record)
    cnames_created  = length(unifi_dns_record.cname_record)
    devices_found   = length(local.found_macs)
    devices_missing = length(local.missing_macs_unique)
    duplicate_macs  = length(local.duplicate_macs) > 0 ? local.duplicate_macs : []
    warnings        = length(local.missing_macs_unique) > 0 ? ["Some MAC addresses were not found in UniFi Controller"] : []
  }
}

# ==============================================================================
# Service CNAMEs Reference
# ==============================================================================
# The filipowm/unifi provider supports DNS records including CNAMEs.
# These are now created as actual DNS records instead of just being tracked.

output "service_cnames_created" {
  description = "Service CNAMEs from configuration that were created as DNS records"
  value = flatten([
    for device in local.effective_config.devices : concat(
      coalesce(device.service_cnames, []),
      flatten([for nic in device.nics : coalesce(nic.service_cnames, [])])
    )
    if contains(keys(local.devices_with_found_macs), device.friendly_hostname)
  ])
}
