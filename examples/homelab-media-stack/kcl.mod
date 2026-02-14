[package]
name = "homelab_media_stack"
edition = "v0.11.1"
version = "0.1.0"
description = "Example homelab media stack configuration using unifi-cloudflare-glue"

[dependencies]
unifi_cloudflare_glue = { git = "https://github.com/SolomonHD/unifi-cloudflare-glue", tag = "v0.7.2" }