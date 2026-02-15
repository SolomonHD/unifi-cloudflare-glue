[package]
name = "external_only_example"
edition = "v0.11.1"
version = "0.1.0"
description = "Example external-only services configuration using unifi-cloudflare-glue"

[dependencies]
unifi_cloudflare_glue = { git = "https://github.com/SolomonHD/unifi-cloudflare-glue", tag = "v0.11.2" }