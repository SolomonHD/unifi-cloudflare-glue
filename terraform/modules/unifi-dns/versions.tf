# unifi-cloudflare-glue Terraform Module
# Version: 0.1.0
# Source: https://github.com/yourusername/unifi-cloudflare-glue/releases/tag/v0.1.0
#
# This module is part of the unifi-cloudflare-glue project.
# All components (KCL, Terraform, Dagger) share the same version.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    unifi = {
      source  = "filipowm/unifi"
      version = "~> 1.0"
    }
  }
}
