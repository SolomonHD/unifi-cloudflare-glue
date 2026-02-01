# Input variables for UniFi DNS module
# These will be populated from KCL-generated configuration

variable "config" {
  description = "Configuration object containing devices, domain settings, and controller configuration. Either config or config_file must be provided."
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
  default = null
}

variable "config_file" {
  description = "Path to a JSON file containing the UniFi DNS configuration. Either config or config_file must be provided."
  type        = string
  default     = ""
}

variable "strict_mode" {
  description = "If true, the module will fail if any MAC addresses are not found in UniFi. If false, missing MACs will be tracked in missing_devices output."
  type        = bool
  default     = false
}
