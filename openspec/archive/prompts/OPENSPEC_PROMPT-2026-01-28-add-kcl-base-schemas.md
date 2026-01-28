# OpenSpec Prompt: KCL Base Schema Definitions

## Context

KCL (Kusion Configuration Language) serves as the unified configuration layer that bridges UniFi and Cloudflare configurations. The base schemas define shared structures that both provider-specific extensions will build upon.

This change establishes the foundational schema types that represent the core domain model: Entities (physical devices), Endpoints (network interfaces), and Services (applications running on devices).

## Goal

Define the base KCL schemas that capture the shared concepts across UniFi DNS and Cloudflare Tunnel configurations. These schemas provide the type foundation for the unified configuration layer.

## Scope

### In Scope
- Define `Entity` schema - represents a physical device/server
- Define `Endpoint` schema - represents a network interface/NIC
- Define `Service` schema - represents an application/service
- Define `MACAddress` type with validation
- Define `Hostname` type with validation
- Define `Distribution` enum for service visibility (unifi_only, cloudflare_only, both)

### Out of Scope
- UniFi-specific schema extensions (covered in next prompt)
- Cloudflare-specific schema extensions (covered in later prompt)
- JSON generators (covered in later prompts)
- Validation logic for cross-reference checks

## Desired Behavior

The base schemas should provide:

1. **Entity Schema**:
   - `friendly_hostname`: Hostname for the device (creates round-robin A-records)
   - `domain`: Base domain for the device (e.g., "internal.lan")
   - `endpoints`: List of Endpoint objects (NICs)
   - `services`: List of Service objects running on this device

2. **Endpoint Schema**:
   - `mac_address`: MACAddress type with format validation
   - `nic_name`: Optional name for this NIC (e.g., "eth0", "mgmt")
   - `service_cnames`: Additional CNAMEs specific to this NIC

3. **Service Schema**:
   - `name`: Service identifier (e.g., "jellyfin", "sonarr")
   - `port`: Port number the service listens on
   - `protocol`: Protocol (http/https/tcp)
   - `distribution`: Distribution enum for visibility control
   - `internal_hostname`: Optional override for internal DNS
   - `public_hostname`: Optional override for public DNS

4. **MACAddress Type**:
   - Validate format: supports aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff
   - Normalize to lowercase colon format internally

5. **Distribution Enum**:
   - `unifi_only`: Service only in UniFi DNS
   - `cloudflare_only`: Service only in Cloudflare Tunnel
   - `both`: Service in both providers

## Constraints & Assumptions

1. **KCL Syntax**: Use KCL v0.9+ schema definition syntax
2. **Validation**: Use KCL's built-in regex validation for MAC addresses and hostnames
3. **Extensibility**: Base schemas must support extension via mixin patterns
4. **Defaults**: Provide sensible defaults where applicable

## Acceptance Criteria

- [ ] `kcl/schemas/base.k` contains Entity schema with all required fields
- [ ] `kcl/schemas/base.k` contains Endpoint schema with MAC validation
- [ ] `kcl/schemas/base.k` contains Service schema with Distribution enum
- [ ] MACAddress validation accepts all three formats and normalizes to lowercase colons
- [ ] Hostname validation ensures valid DNS labels
- [ ] Distribution enum has exactly three variants: unifi_only, cloudflare_only, both
- [ ] All schemas have appropriate doc comments explaining usage
- [ ] KCL module validates without errors (`kcl run` or equivalent)

## Dependencies

- **Depends On**: 001-project-scaffolding (directory structure must exist)

## Expected Files/Areas Touched

- `kcl/schemas/base.k` (new/complete implementation)
