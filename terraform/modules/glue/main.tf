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
# When glue is used as the root module (full deployment), it needs provider blocks
# The child modules inherit these provider configurations

provider "unifi" {
  # Conditionally configure UniFi provider with placeholder values when not used
  # This allows cloudflare-only deployments without valid UniFi credentials
  api_url        = var.unifi_url != "" ? (var.api_url != "" ? var.api_url : var.unifi_url) : "https://unifi.placeholder.local:8443"
  api_key        = var.unifi_api_key != "" ? var.unifi_api_key : null
  username       = var.unifi_username != "" ? var.unifi_username : (var.unifi_url != "" ? null : "placeholder")
  password       = var.unifi_password != "" ? var.unifi_password : (var.unifi_url != "" ? null : "placeholder")
  allow_insecure = var.unifi_insecure
}

provider "cloudflare" {
  # Use environment variable CLOUDFLARE_API_TOKEN for authentication
  # This is set by the Dagger module as a secret for secure handling
}

# ==============================================================================
# UniFi DNS Module
# ==============================================================================
# Deploy UniFi DNS records first. This ensures all internal hostnames
# are resolvable before Cloudflare Tunnel attempts to use them.
# Only called when UniFi configuration is provided (for full or unifi-only deploys).

locals {
  # Determine if UniFi module should be deployed
  deploy_unifi = var.unifi_config != null || var.unifi_config_file != ""

  # Determine if Cloudflare module should be deployed
  deploy_cloudflare = var.cloudflare_config != null || var.cloudflare_config_file != ""
}

module "unifi_dns" {
  count  = local.deploy_unifi ? 1 : 0
  source = "../unifi-dns/"

  # Pass provider configuration explicitly to override child module's provider block
  providers = {
    unifi = unifi
  }

  # Configuration inputs (either object or file path)
  config      = var.unifi_config
  config_file = var.unifi_config_file

  # UniFi provider settings
  unifi_url      = var.unifi_url != "" ? var.unifi_url : "https://placeholder.local"
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
# Only called when Cloudflare configuration is provided (for full or cloudflare-only deploys).

module "cloudflare_tunnel" {
  count  = local.deploy_cloudflare ? 1 : 0
  source = "../cloudflare-tunnel/"

  # Pass provider configuration explicitly to override child module's provider block
  providers = {
    cloudflare = cloudflare
    random     = random
  }

  # Configuration inputs (either object or file path)
  config      = var.cloudflare_config
  config_file = var.cloudflare_config_file

  # Override account_id and zone_name if provided (CLI parameters take precedence over config)
  account_id_override = var.cloudflare_account_id
  zone_name_override  = var.zone_name

  # NOTE: Cloudflare authentication is handled via CLOUDFLARE_API_TOKEN environment variable
  # This is set by the Dagger module as a secret for secure handling

  # Explicit dependency: Wait for UniFi DNS to complete (if it was deployed)
  # This ensures all internal hostnames are resolvable before
  # Cloudflare Tunnel services attempt to use them.
  depends_on = [module.unifi_dns]
}
