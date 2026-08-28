# UniFi DNS Module
# This module manages DNS records in UniFi controllers using the filipowm/unifi provider
# The provider supports native DNS record resources (unifi_dns_record)

# ==============================================================================
# Provider Configuration
# ==============================================================================
# Provider configuration is inherited from parent module or configured locally
# When called from glue module: provider is passed explicitly from parent
# When used standalone: provider is configured via required_providers in versions.tf
# No provider block here - allows both usage patterns

# ==============================================================================
# Locals
# ==============================================================================

locals {
  # Load config from file if config_file is provided, otherwise use config
  effective_config = var.config_file != "" ? jsondecode(file(var.config_file)) : var.config

  # Validate that at least one of config or config_file is provided
  _validate_config = local.effective_config != null ? true : tobool("ERROR: Either config or config_file must be provided")

  # Create a flat list of all MAC addresses to look up with their device context
  mac_lookups = flatten([
    for device in local.effective_config.devices : [
      for idx, nic in device.nics : {
        key = "${device.friendly_hostname}-${idx}"
        # Normalize MAC to lowercase colon format
        mac_normalized = lower(
          length(regexall("^[0-9a-fA-F]{12}$", nic.mac_address)) > 0
          ? join(":", regexall("[0-9a-fA-F]{2}", nic.mac_address))
          : replace(lower(nic.mac_address), "-", ":")
        )
        device_name = device.friendly_hostname
        domain      = coalesce(device.domain, local.effective_config.default_domain)
        nic_name    = nic.nic_name
        nic_index   = idx
      }
    ]
  ])

  # Build a map of MAC lookups by their unique key
  mac_lookup_map = { for lookup in local.mac_lookups : lookup.key => lookup }

  # Build list of found MACs and their IPs
  found_macs = {
    for key, lookup in local.mac_lookup_map : lookup.mac_normalized => {
      ip          = data.unifi_user.device[key].ip
      device_name = lookup.device_name
      domain      = lookup.domain
    }
    if data.unifi_user.device[key].ip != null
  }

  # Build list of missing MACs
  missing_macs = [
    for key, lookup in local.mac_lookup_map : lookup.mac_normalized
    if data.unifi_user.device[key].ip == null
  ]

  # Unique missing MACs (remove duplicates)
  missing_macs_unique = distinct(local.missing_macs)

  # Check for duplicate MACs in configuration
  all_macs = [for lookup in local.mac_lookups : lookup.mac_normalized]
  duplicate_macs = distinct([
    for mac in local.all_macs : mac
    if length([for m in local.all_macs : m if m == mac]) > 1
  ])

  # Build device to MAC mapping (use first NIC's MAC for DNS if device has multiple)
  device_primary_mac = {
    for device in local.effective_config.devices : device.friendly_hostname => lower(
      length(regexall("^[0-9a-fA-F]{12}$", device.nics[0].mac_address)) > 0
      ? join(":", regexall("[0-9a-fA-F]{2}", device.nics[0].mac_address))
      : replace(lower(device.nics[0].mac_address), "-", ":")
    )
  }

  # Determine which devices have at least one found MAC
  devices_with_found_macs = {
    for device in local.effective_config.devices : device.friendly_hostname => device
    if length(setintersection(
      [for nic in device.nics : lower(
        length(regexall("^[0-9a-fA-F]{12}$", nic.mac_address)) > 0
        ? join(":", regexall("[0-9a-fA-F]{2}", nic.mac_address))
        : replace(lower(nic.mac_address), "-", ":")
      )],
      local.missing_macs_unique
    )) < length(device.nics)
  }

  # Build DNS A-records for all configured devices. The keys remain static while
  # IP values are read after the corresponding client has been registered.
  dns_records = {
    for device in local.effective_config.devices : device.friendly_hostname => {
      hostname = device.friendly_hostname
      domain   = coalesce(device.domain, local.effective_config.default_domain)
      ip       = data.unifi_user.device["${device.friendly_hostname}-0"].ip
    }
  }
}

# ==============================================================================
# UniFi Client Registration and Lookup
# ==============================================================================

# Register or adopt every normalized MAC before querying its current IP. Network
# 10.x can report UnknownUser for active clients that are not yet remembered.
resource "unifi_user" "device" {
  for_each = local.mac_lookup_map

  mac                    = each.value.mac_normalized
  name                   = each.value.device_name
  site                   = local.effective_config.site
  allow_existing         = true
  skip_forget_on_destroy = true
}

# Read the registered client after resource adoption. The explicit dependency is
# required because the data source otherwise races the Network 10.x registration.
data "unifi_user" "device" {
  for_each = local.mac_lookup_map

  site       = local.effective_config.site
  mac        = each.value.mac_normalized
  depends_on = [unifi_user.device]
}

# ==============================================================================
# DNS Record Resources
# ==============================================================================

# Create DNS A-records using unifi_dns_record resource
# The filipowm/unifi provider supports native DNS record management
resource "unifi_dns_record" "dns_record" {
  for_each = local.dns_records

  site    = local.effective_config.site
  name    = "${each.value.hostname}.${each.value.domain}"
  record  = each.value.ip
  type    = "A"
  enabled = true
}

# Create DNS CNAME records for service aliases if supported
# The filipowm/unifi provider supports CNAME records
# We create CNAMEs pointing to the primary hostname for each device
locals {
  # Flatten all service_cnames from devices and NICs
  # KCL now provides fully-qualified CNAMEs, so we use them as-is
  # No filter is needed because every configured client is registered above.
  cname_records = flatten([
    for device in local.effective_config.devices : concat(
      # Device-level CNAMEs
      [
        for cname in coalesce(device.service_cnames, []) : {
          key      = "${device.friendly_hostname}-${cname}"
          name     = cname
          hostname = device.friendly_hostname
          domain   = coalesce(device.domain, local.effective_config.default_domain)
        }
      ],
      # NIC-level CNAMEs
      flatten([
        for nic in device.nics : [
          for cname in coalesce(nic.service_cnames, []) : {
            key      = "${device.friendly_hostname}-${nic.nic_name}-${cname}"
            name     = cname
            hostname = device.friendly_hostname
            domain   = coalesce(device.domain, local.effective_config.default_domain)
          }
        ]
      ])
    )
  ])

  cname_records_map = { for rec in local.cname_records : rec.key => rec }
}

resource "unifi_dns_record" "cname_record" {
  for_each = local.cname_records_map

  site    = local.effective_config.site
  name    = each.value.name
  record  = "${each.value.hostname}.${each.value.domain}"
  type    = "CNAME"
  enabled = true
}

# ==============================================================================
# Strict Mode Check
# ==============================================================================

resource "null_resource" "strict_mode_check" {
  count = var.strict_mode && length(local.missing_macs_unique) > 0 ? 1 : 0

  triggers = {
    missing_macs = join(", ", local.missing_macs_unique)
  }

  provisioner "local-exec" {
    command = <<EOT
      echo "ERROR: Strict mode enabled but the following MAC addresses were not found in UniFi Controller:"
      echo "${join("\\n", local.missing_macs_unique)}"
      exit 1
    EOT
  }
}
