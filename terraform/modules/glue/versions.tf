# unifi-cloudflare-glue Terraform Module - Combined Glue Module
# Version: 0.9.3
# Source: https://github.com/SolomonHD/unifi-cloudflare-glue/releases/tag/v0.9.3
#
# This module combines the unifi-dns and cloudflare-tunnel modules into a single
# atomic deployment, eliminating provider conflicts when using shared state.
# All components (KCL, Terraform, Dagger) share the same version.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    unifi = {
      source  = "filipowm/unifi"
      version = "~> 1.0"
    }
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
