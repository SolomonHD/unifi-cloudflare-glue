# OpenSpec Prompt: KCL Cross-Provider Integration and Validation

## Context

The KCL layer needs to validate that UniFi and Cloudflare configurations are consistent with each other. This ensures all Cloudflare MAC addresses exist in UniFi and prevents configuration errors before Terraform applies.

## Goal

Implement cross-provider validation logic that ensures the unified configuration is internally consistent and safe to deploy.

## Scope

### In Scope
- Create unified configuration schema combining UniFi and Cloudflare
- Implement validation that all Cloudflare MACs exist in UniFi
- Validate no hostname collisions between providers
- Create main entrypoint that generates both JSON outputs
- Add comprehensive error messages for validation failures

### Out of Scope
- Individual schema definitions (covered in previous prompts)
- Individual generators (covered in previous prompts)
- Terraform modules (covered in subsequent prompts)

## Desired Behavior

1. **UnifiedConfig Schema**:
   - Combines UniFiConfig and CloudflareConfig
   - Single source of truth for entire infrastructure
   - Support for device-level distribution annotations

2. **Cross-Validation Rules**:
   - Every MAC in Cloudflare.tunnels must exist in UniFi.devices.endpoints
   - No duplicate friendly_hostnames across devices
   - No duplicate public_hostnames across tunnels
   - All local_service_url domains must be internal

3. **Generation Entrypoint**:
   - `generate()` function takes UnifiedConfig
   - Returns object with both `unifi_json` and `cloudflare_json`
   - Runs all validations before generation
   - Fails fast with clear error messages

4. **Validation Error Format**:
   ```
   Validation Error: MAC address "aa:bb:cc:dd:ee:ff" referenced in Cloudflare tunnel
   "tunnel-media" does not exist in UniFi device list.
   
   Available devices: ["media-server", "storage-server"]
   Available MACs: ["11:22:33:44:55:66", "77:88:99:aa:bb:cc"]
   ```

## Constraints & Assumptions

1. **Fail Fast**: Stop on first validation error with clear message
2. **MAC Normalization**: Compare MACs in normalized format
3. **Hostname Uniqueness**: Check across all devices/tunnels
4. **Internal Domains**: .lan, .local, .home considered internal

## Acceptance Criteria

- [ ] `kcl/` contains unified configuration schema
- [ ] Cross-MAC validation ensures all Cloudflare MACs exist in UniFi
- [ ] Hostname uniqueness validation prevents duplicates
- [ ] Main `generate()` function produces both JSON outputs
- [ ] Validation errors include helpful context and suggestions
- [ ] Validation runs before any generation
- [ ] KCL module can be run to produce both output files
- [ ] Documentation explains validation rules

## Dependencies

- **Depends On**: 003-kcl-unifi-schemas, 004-kcl-cloudflare-schemas, 005-kcl-unifi-generator, 006-kcl-cloudflare-generator

## Expected Files/Areas Touched

- `kcl/main.k` or `kcl/unified.k` (new - unified config and validation)
- `kcl/README.md` (update with validation documentation)
