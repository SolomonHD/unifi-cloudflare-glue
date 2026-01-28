# Input variables for UniFi DNS module
# These will be populated from KCL-generated configuration

variable "config" {
  description = "Configuration object containing devices, domain settings, and controller configuration"
  type = object({
    devices = list(object({
      friendly_hostname = string
      domain            = optional(string, null)
      service_cnames    = optional(list(string), [])
      nics = list(object({
        mac_address    = string
        nic_name       = optional(string, null)
        service_cnames = optional(list(string), [])
      }))
    }))
    default_domain = string
    site           = optional(string, "default")
  })

  validation {
    condition = alltrue([
      for device in var.config.devices : length(device.nics) > 0
    ])
    error_message = "Each device must have at least one NIC."
  }

  validation {
    condition = alltrue([
      for device in var.config.devices : can(regex("^[a-zA-Z0-9]([a-zA-Z0-9\\-]{0,61}[a-zA-Z0-9])?$", device.friendly_hostname))
    ])
    error_message = "friendly_hostname must be a valid DNS label (alphanumeric, hyphens, 1-63 chars, no underscores)."
  }

  validation {
    condition = alltrue([
      for device in var.config.devices : alltrue([
        for nic in device.nics : can(regex("^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$|^[0-9a-fA-F]{12}$", nic.mac_address))
      ])
    ])
    error_message = "MAC addresses must be in format aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, or aabbccddeeff."
  }
}

variable "strict_mode" {
  description = "If true, the module will fail if any MAC addresses are not found in UniFi. If false, missing MACs will be tracked in missing_devices output."
  type        = bool
  default     = false
}
