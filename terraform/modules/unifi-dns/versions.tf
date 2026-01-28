terraform {
  required_version = ">= 1.5.0"

  required_providers {
    unifi = {
      source  = "filipowm/unifi"
      version = "~> 1.0"
    }
  }
}
