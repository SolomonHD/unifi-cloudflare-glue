[package]
name = "staging_environment_example"
edition = "v0.11.1"
version = "0.1.0"
description = "Staging environment example with S3 backend and state locking"

[dependencies]
unifi_cloudflare_glue = { git = "https://github.com/SolomonHD/unifi-cloudflare-glue", tag = "v0.7.2" }