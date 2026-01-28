# Input variables for Cloudflare Tunnel module
# These will be populated from KCL-generated configuration

variable "config" {
  description = "Cloudflare Tunnel configuration object containing zone settings, account ID, and tunnel definitions"
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

  validation {
    condition     = length(var.config.zone_name) > 0
    error_message = "zone_name cannot be empty"
  }

  validation {
    condition     = length(var.config.account_id) > 0
    error_message = "account_id cannot be empty"
  }

  # DNS loop prevention: local_service_url cannot contain zone_name
  validation {
    condition = alltrue(flatten([
      for mac, tunnel in var.config.tunnels : [
        for svc in tunnel.services :
        !can(regex(lower(var.config.zone_name), lower(svc.local_service_url)))
      ]
    ]))
    error_message = "local_service_url cannot contain zone_name - this would cause a DNS resolution loop. Use internal domains only (.internal.lan, .local, .home, etc.)"
  }
}
