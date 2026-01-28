terraform {
  required_version = ">= 1.5.0"

  required_providers {
    unifi = {
      source  = "paultyng/unifi"
      version = "~> 0.41"
    }
  }
}
