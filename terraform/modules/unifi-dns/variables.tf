# Input variables for UniFi DNS module
# These will be populated from KCL-generated configuration

variable "config" {
  description = "Configuration object containing devices, domain settings, and controller configuration. Either config or config_file must be provided."
  type        = any
  default     = null
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

# ==============================================================================
# UniFi Provider Configuration
# ==============================================================================

variable "unifi_url" {
  description = "URL of the UniFi controller (e.g., https://unifi.local:8443)"
  type        = string
}

variable "api_url" {
  description = "URL of the UniFi API (defaults to unifi_url)"
  type        = string
  default     = ""
}

variable "unifi_api_key" {
  description = "UniFi API key for authentication (mutually exclusive with username/password)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "unifi_username" {
  description = "UniFi username for authentication (use with password)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "unifi_password" {
  description = "UniFi password for authentication (use with username)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "unifi_insecure" {
  description = "Skip TLS certificate verification for UniFi controller (useful for self-signed certificates)"
  type        = bool
  default     = false
}
