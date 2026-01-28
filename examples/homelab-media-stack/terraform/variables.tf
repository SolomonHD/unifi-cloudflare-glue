# Input Variables for Homelab Media Stack
#
# These variables allow customization of the deployment without modifying
# the main Terraform code. Values can be provided via:
#   - terraform.tfvars file
#   - Environment variables (TF_VAR_*)
#   - Command line: -var="name=value"
#   - Interactive prompts (if not provided)

# ============================================================================
# UNIFI CONTROLLER CREDENTIALS
# ============================================================================

variable "unifi_controller_host" {
  description = "Hostname or IP address of the UniFi Controller"
  type        = string

  validation {
    condition     = length(var.unifi_controller_host) > 0
    error_message = "UniFi Controller host cannot be empty."
  }
}

variable "unifi_username" {
  description = "Username for UniFi Controller authentication"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.unifi_username) > 0
    error_message = "UniFi username cannot be empty."
  }
}

variable "unifi_password" {
  description = "Password for UniFi Controller authentication"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.unifi_password) > 0
    error_message = "UniFi password cannot be empty."
  }
}

variable "unifi_site" {
  description = "UniFi site name where devices are managed"
  type        = string
  default     = "default"
}

# ============================================================================
# CLOUDFLARE CREDENTIALS
# ============================================================================

variable "cloudflare_api_token" {
  description = <<EOF
Cloudflare API token with the following permissions:
  - Zone:Read (for zone lookup)
  - DNS:Edit (for DNS record management)
  - Cloudflare Tunnel:Edit (for tunnel management)
  - Account:Read (for account ID verification)

Create at: https://dash.cloudflare.com/profile/api-tokens
EOF
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.cloudflare_api_token) > 0
    error_message = "Cloudflare API token cannot be empty."
  }
}

# ============================================================================
# KCL GENERATED FILES PATH
# ============================================================================

variable "generated_files_path" {
  description = <<EOF
Path to the directory containing KCL-generated JSON files.
These files are created by running `kcl run main.k` in the parent directory.
Expected files:
  - unifi.json: UniFi DNS configuration
  - cloudflare.json: Cloudflare Tunnel configuration
EOF
  type        = string
  default     = "../outputs"

  validation {
    condition     = length(var.generated_files_path) > 0
    error_message = "Generated files path cannot be empty."
  }
}

# ============================================================================
# MODULE BEHAVIOR OPTIONS
# ============================================================================

variable "unifi_strict_mode" {
  description = <<EOF
If true, the UniFi module will fail if any MAC addresses are not found in UniFi.
If false, missing MACs will be tracked in missing_devices output.

Recommended: false for initial setup, true for production
EOF
  type        = bool
  default     = false
}

variable "cloudflare_tunnel_secret" {
  description = <<EOF
Optional secret for Cloudflare Tunnel authentication.
If not provided, a random secret will be generated.
This secret is used to authenticate the cloudflared daemon.
EOF
  type        = string
  sensitive   = true
  default     = null
}
