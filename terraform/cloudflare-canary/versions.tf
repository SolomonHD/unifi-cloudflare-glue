terraform {
  required_version = ">= 1.13.5, < 2.0.0"

  backend "s3" {}

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}

# Authentication is supplied at runtime through CLOUDFLARE_API_TOKEN.
provider "cloudflare" {}
