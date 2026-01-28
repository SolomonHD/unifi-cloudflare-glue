# Change: Add KCL Cloudflare Schema Extensions

## Why

The Cloudflare schema extensions build on base schemas to add Cloudflare Tunnel-specific configuration. This includes tunnel definitions, ingress rules, and public DNS settings. These schemas are necessary to define and validate Cloudflare Zero Trust Tunnel configurations that bridge physical devices (identified by MAC address) with public DNS entries through Cloudflare Tunnels.

## What Changes

- Add `CloudflareTunnel` schema for tunnel configuration with tunnel_name, mac_address, services, and credentials_path
- Add `TunnelService` schema for ingress rules with public_hostname, local_service_url, no_tls_verify, and path_prefix
- Add `CloudflareConfig` schema as root configuration container with zone_name, account_id, tunnels dictionary, and default_no_tls_verify
- Implement validation rules:
  - local_service_url must use internal domain (.internal.lan, .local, etc.) to prevent DNS loops
  - public_hostname must belong to the configured zone_name
  - Each MAC address can have only one tunnel (one-to-one mapping)
  - Warnings when no_tls_verify is enabled

## Impact

- Affected specs: kcl-module
- Affected code: `kcl/schemas/cloudflare.k`
- Dependencies: Requires base schemas from `kcl/schemas/base.k` (MACAddress, Hostname types)
