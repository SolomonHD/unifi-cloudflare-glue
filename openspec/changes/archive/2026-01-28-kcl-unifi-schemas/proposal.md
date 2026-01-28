# Change: KCL UniFi Schema Extensions

## Why

Building on the base schemas, the UniFi schema extensions add UniFi Controller-specific configuration for managing local DNS. This includes properties for local DNS management, internal domain handling, UniFi site support, and UniFi-specific validations. These extensions enable the generation of UniFi-specific JSON configurations from the unified entity model.

## What Changes

- Extend base [`Entity`](kcl/schemas/base.k:95) schema with UniFi-specific fields (service_cnames, unifi_site)
- Extend base [`Endpoint`](kcl/schemas/base.k:50) schema with UniFi-specific properties (query_unifi, static_ip)
- Create [`UniFiConfig`](kcl/schemas/unifi.k:22) root configuration schema
- Add UniFi-specific validation rules:
  - Each device must have at least one endpoint
  - Each endpoint must have MAC address or static_ip
  - friendly_hostname must be valid DNS label
  - Domain must end in .lan, .local, or .home for safety
- Replace placeholder [`UniFiClient`](kcl/schemas/unifi.k:6) and [`UniFiDNSRecord`](kcl/schemas/unifi.k:14) schemas

## Impact

- Affected specs: `kcl-module` capability
- Affected code:
  - `kcl/schemas/unifi.k` - Complete implementation of UniFi schemas
  - `kcl/schemas/base.k` - Import references (no changes to base)

## Dependencies

- Depends on: Base schemas (`add-kcl-base-schemas` / 002) must be completed
