# Input variables for Combined Glue Module
# This module wraps both unifi-dns and cloudflare-tunnel modules
# All variables from both sub-modules are exposed at this level

# ==============================================================================
# UniFi Configuration
# ==============================================================================

variable "unifi_config" {
  description = "UniFi DNS configuration object containing devices, domain settings, and controller configuration. Either unifi_config or unifi_config_file must be provided."
  type        = any
  default     = null
}

variable "unifi_config_file" {
  description = "Path to a JSON file containing the UniFi DNS configuration. Either unifi_config or unifi_config_file must be provided."
  type        = string
  default     = ""
}

# ==============================================================================
# Cloudflare Configuration
# ==============================================================================

variable "cloudflare_config" {
  description = "Cloudflare Tunnel configuration object containing zone settings, account ID, and tunnel definitions. Either cloudflare_config or cloudflare_config_file must be provided."
  type = object({
    zone_name  = string
    account_id = string
    tunnels = map(object({
      tunnel_name = string
      mac_address = string
      services = list(object({
        public_hostname   = string
        local_service_url = string
        no_tls_verify     = optional(bool, false)
      }))
    }))
  })
  default = null
}

variable "cloudflare_config_file" {
  description = "Path to a JSON file containing the Cloudflare Tunnel configuration. Either cloudflare_config or cloudflare_config_file must be provided."
  type        = string
  default     = ""
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

# ==============================================================================
# Module Behavior
# ==============================================================================

variable "strict_mode" {
  description = "If true, the module will fail if any MAC addresses are not found in UniFi. If false, missing MACs will be tracked in missing_devices output."
  type        = bool
  default     = false
}

# ==============================================================================
# Cloudflare Provider Configuration
# ==============================================================================

variable "cloudflare_token" {
  description = "Cloudflare API token with permissions: Zone:Read, DNS:Edit, Cloudflare Tunnel:Edit"
  type        = string
  sensitive   = true
}
