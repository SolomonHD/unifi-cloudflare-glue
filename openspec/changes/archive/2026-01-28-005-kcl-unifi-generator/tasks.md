# Tasks: KCL UniFi Generator

## Implementation Tasks

- [x] Import schemas in generator file
  - Add imports for `kcl/schemas/base.k` and `kcl/schemas/unifi.k`
  - Verify schema types are accessible

- [x] Implement `normalize_mac()` wrapper (if needed)
  - Reuse existing function from base.k
  - Ensure it's accessible within generator scope

- [x] Implement endpoint transformation function
  - Create lambda to transform `UniFiEndpoint` to NIC record
  - Handle MAC normalization
  - Handle optional `nic_name` field

- [x] Implement entity transformation function
  - Create lambda to transform `UniFiEntity` to device record
  - Transform all endpoints using endpoint function
  - Include device-level `service_cnames`

- [x] Implement service filtering logic
  - Filter services by distribution (exclude `cloudflare_only`)
  - Generate CNAMEs from filtered services

- [x] Implement `generate_unifi_config()` function
  - Accept `UniFiConfig` parameter
  - Transform all devices
  - Return dictionary with `devices` and `default_domain`

- [x] Add sample configuration for testing
  - Create test `UniFiConfig` instance
  - Include multiple devices with various configurations
  - Include services with different distributions

- [x] Validate generator output
  - Run `kcl run generators/unifi.k`
  - Verify JSON is valid
  - Check output matches expected schema

- [x] Test MAC normalization
  - Test various MAC formats (colon, hyphen, no-separator)
  - Verify lowercase output

- [x] Test service filtering
  - Verify `cloudflare_only` services are excluded
  - Verify `unifi_only` and `both` services are included

- [x] Update README documentation
  - Document generator usage
  - Add example invocation

## Definition of Done

- [x] `kcl/generators/unifi.k` contains complete implementation
- [x] Generator outputs valid JSON matching UniFi module schema
- [x] All MAC addresses normalized to lowercase colon format
- [x] Services correctly filtered by distribution
- [x] Generator can be called with `generate_unifi_config(config)`
- [x] Sample configuration demonstrates all features

## Dependencies

- Requires: `003-kcl-unifi-schemas` (completed - archived)
- Blocks: `007-kcl-integration-validation`
