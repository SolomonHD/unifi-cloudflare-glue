# Input variables for Cloudflare Tunnel module
# These will be populated from KCL-generated configuration

variable "config" {
  description = "Cloudflare Tunnel configuration object containing zone settings, account ID, and tunnel definitions. Either config or config_file must be provided."
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

variable "config_file" {
  description = "Path to a JSON file containing the Cloudflare Tunnel configuration. Either config or config_file must be provided."
  type        = string
  default     = ""
}

variable "cloudflare_token" {
  description = "Cloudflare API token with permissions: Zone:Read, DNS:Edit, Cloudflare Tunnel:Edit"
  type        = string
  sensitive   = true
}
