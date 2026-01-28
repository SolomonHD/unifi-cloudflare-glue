# Change: KCL Cross-Provider Integration and Validation

## Why

The KCL layer needs to validate that UniFi and Cloudflare configurations are consistent with each other before Terraform applies them. Without cross-provider validation, configuration errors (like referencing a MAC address in Cloudflare that doesn't exist in UniFi) would only surface during Terraform apply, causing partial deployments and infrastructure inconsistency. This change implements fail-fast validation that catches errors at configuration time.

## What Changes

- **ADDED**: `UnifiedConfig` schema that combines UniFi and Cloudflare configurations into a single source of truth
- **ADDED**: Cross-MAC validation ensuring all Cloudflare tunnel MAC addresses exist in UniFi device list
- **ADDED**: Hostname uniqueness validation preventing duplicate friendly_hostnames across devices
- **ADDED**: Public hostname uniqueness validation preventing duplicate public_hostnames across tunnels
- **ADDED**: Internal domain validation for all Cloudflare local_service_url values
- **ADDED**: `generate()` function that validates then produces both `unifi_json` and `cloudflare_json` outputs
- **ADDED**: Comprehensive validation error messages with context and suggestions

## Impact

- **Affected specs**: kcl-module (new unified configuration capability)
- **Affected code**:
  - `kcl/main.k` (new - unified config entrypoint and validation)
  - `kcl/README.md` (update with validation documentation)
- **Dependencies**: 003-kcl-unifi-schemas, 004-kcl-cloudflare-schemas, 005-kcl-unifi-generator, 006-kcl-cloudflare-generator

## Validation Strategy

All validation runs before any generation occurs (fail-fast behavior):

1. **MAC Consistency Check**: Every MAC address referenced in Cloudflare tunnels must exist in at least one UniFi device endpoint
2. **Hostname Uniqueness**: No two devices can share the same friendly_hostname
3. **Public Hostname Uniqueness**: No two tunnel services can share the same public_hostname
4. **Internal Domain Check**: All Cloudflare local_service_url values must use internal domains (.lan, .local, .home, etc.)

Error messages include:
- Clear description of the validation failure
- The specific value(s) causing the issue
- Available valid options (e.g., list of valid MACs)
- Suggested fixes
