# Terraform Version Constraints
#
# This file pins Terraform and provider versions for reproducible deployments.
# Version constraints ensure that the same versions are used across different
# environments and over time.

terraform {
  # Pin Terraform to the 1.5.x series for stability
  # 1.5.0 introduced important features for module testing and moved some
  # experimental features to stable. It's a good baseline for production.
  required_version = "~> 1.5"

  required_providers {
    # UniFi Provider
    # Source: filipowm/unifi
    # Used for: Managing UniFi DNS records, querying client devices
    # Version ~> 1.0: Use latest 1.x for bug fixes but not 2.x (breaking changes)
    unifi = {
      source  = "filipowm/unifi"
      version = "~> 1.0"
    }

    # Cloudflare Provider
    # Source: cloudflare/cloudflare
    # Used for: Managing Cloudflare Tunnels, DNS records
    # Version ~> 4.0: Use latest 4.x for new features and bug fixes
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  # ============================================================================
  # REMOTE STATE CONFIGURATION (Optional)
  # ============================================================================
  #
  # Uncomment and configure this section to use remote state storage.
  # Remote state is recommended for team environments and production.
  #
  # backend "s3" {
  #   bucket         = "my-terraform-state-bucket"
  #   key            = "homelab-media-stack/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
  #
  # Alternative: Use Terraform Cloud
  # backend "remote" {
  #   organization = "my-org"
  #   workspaces {
  #     name = "homelab-media-stack"
  #   }
  # }
}
