# Combined Glue Module - Main Configuration
# This module wraps both unifi-dns and cloudflare-tunnel modules
# to enable atomic deployment from a single Terraform configuration.
#
# Wrapper Pattern:
# - Providers are configured at the root level to avoid provider conflicts
# - Both sub-modules are called with explicit dependency (UniFi before Cloudflare)
# - All inputs are passed through from this module's variables
# - All outputs are exposed from sub-modules

# ==============================================================================
# Provider Configuration
# ==============================================================================

provider "unifi" {
  api_url        = var.api_url != "" ? var.api_url : var.unifi_url
  api_key        = var.unifi_api_key != "" ? var.unifi_api_key : null
  username       = var.unifi_username != "" ? var.unifi_username : null
  password       = var.unifi_password != "" ? var.unifi_password : null
  allow_insecure = var.unifi_insecure
}

provider "cloudflare" {
  api_token = var.cloudflare_token
}

# ==============================================================================
# UniFi DNS Module
# ==============================================================================
# Deploy UniFi DNS records first. This ensures all internal hostnames
# are resolvable before Cloudflare Tunnel attempts to use them.

module "unifi_dns" {
  source = "../unifi-dns/"

  # Configuration inputs (either object or file path)
  config      = var.unifi_config
  config_file = var.unifi_config_file

  # UniFi provider settings
  unifi_url      = var.unifi_url
  api_url        = var.api_url
  unifi_api_key  = var.unifi_api_key
  unifi_username = var.unifi_username
  unifi_password = var.unifi_password
  unifi_insecure = var.unifi_insecure

  # Module behavior
  strict_mode = var.strict_mode
}

# ==============================================================================
# Cloudflare Tunnel Module
# ==============================================================================
# Deploy Cloudflare Tunnel after UniFi DNS is complete.
# The explicit depends_on ensures tunnel services can resolve internal hostnames.

module "cloudflare_tunnel" {
  source = "../cloudflare-tunnel/"

  # Configuration inputs (either object or file path)
  config      = var.cloudflare_config
  config_file = var.cloudflare_config_file

  # Cloudflare provider settings
  cloudflare_token = var.cloudflare_token

  # Explicit dependency: Wait for UniFi DNS to complete
  # This ensures all internal hostnames are resolvable before
  # Cloudflare Tunnel services attempt to use them.
  depends_on = [module.unifi_dns]
}
