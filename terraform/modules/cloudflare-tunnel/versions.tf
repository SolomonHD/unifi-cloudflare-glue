# unifi-cloudflare-glue Terraform Module
# Version: 0.9.3
# Source: https://github.com/SolomonHD/unifi-cloudflare-glue/releases/tag/v0.9.3
#
# This module is part of the unifi-cloudflare-glue project.
# All components (KCL, Terraform, Dagger) share the same version.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}
