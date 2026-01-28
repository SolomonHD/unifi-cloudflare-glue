# OpenSpec Prompt: KCL UniFi Schema Extensions

## Context

Building on the base schemas, the UniFi schema extensions add UniFi Controller-specific configuration. This includes properties for local DNS management, internal domain handling, and UniFi-specific validations.

## Goal

Extend the base schemas with UniFi-specific fields and validation logic needed for generating UniFi DNS configurations.

## Scope

### In Scope
- Define `UniFiEntity` schema extending base Entity
- Define `UniFiEndpoint` schema extending base Endpoint  
- Define `UniFiConfig` schema for the root configuration
- Add UniFi-specific validation rules
- Define internal domain constraints

### Out of Scope
- Cloudflare-specific extensions (covered separately)
- JSON generator logic (covered in later prompt)
- Cross-provider validation (covered in later prompt)

## Desired Behavior

1. **UniFiEntity Schema** (extends Entity):
   - Inherits all base Entity fields
   - `service_cnames`: Additional device-level CNAMEs for services
   - `unifi_site`: Optional UniFi site name (defaults to "default")

2. **UniFiEndpoint Schema** (extends Endpoint):
   - Inherits all base Endpoint fields
   - `query_unifi`: Boolean to query UniFi Controller for current IP
   - `static_ip`: Optional static IP if not querying UniFi

3. **UniFiConfig Schema** (root configuration):
   - `devices`: List of UniFiEntity objects
   - `default_domain`: Default domain for internal DNS (e.g., "internal.lan")
   - `unifi_controller`: Connection details (host, port, credentials reference)

4. **Validation Rules**:
   - Each device must have at least one endpoint
   - Each endpoint must have MAC address or static_ip
   - friendly_hostname must be valid DNS label
   - Domain must end in .lan, .local, or .home for safety

## Constraints & Assumptions

1. **Extension Pattern**: Use KCL mixin/extension syntax to build on base schemas
2. **Safe Domains**: Only allow internal TLDs (.lan, .local, .home) for UniFi DNS
3. **MAC Priority**: MAC address takes precedence over static IP if both provided
4. **Site Support**: Support multiple UniFi sites, default to "default"

## Acceptance Criteria

- [ ] `kcl/schemas/unifi.k` contains UniFiEntity extending base Entity
- [ ] `kcl/schemas/unifi.k` contains UniFiEndpoint extending base Endpoint
- [ ] `kcl/schemas/unifi.k` contains UniFiConfig as root configuration schema
- [ ] Validation ensures at least one endpoint per device
- [ ] Validation ensures safe internal domain suffixes only
- [ ] UniFi site defaults to "default" if not specified
- [ ] Schema properly imports and references base.k
- [ ] KCL module validates without errors

## Dependencies

- **Depends On**: 002-kcl-base-schemas (base schemas must exist)

## Expected Files/Areas Touched

- `kcl/schemas/unifi.k` (new/complete implementation)
