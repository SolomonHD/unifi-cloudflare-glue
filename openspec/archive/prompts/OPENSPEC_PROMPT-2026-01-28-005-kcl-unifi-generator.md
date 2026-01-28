# OpenSpec Prompt: KCL UniFi JSON Generator

## Context

With schemas defined, we need generators to convert KCL configurations into Terraform-compatible JSON format. The UniFi generator transforms UniFiConfig into the JSON format expected by the Terraform UniFi DNS module.

## Goal

Implement the KCL generator that converts UniFiConfig schema instances into JSON output suitable for the Terraform UniFi DNS module.

## Scope

### In Scope
- Implement `generate_unifi_config()` function
- Transform entities to device records with NICs
- Generate service CNAMEs based on distribution settings
- Normalize MAC addresses to lowercase colon format
- Handle round-robin A-record generation for multi-NIC devices

### Out of Scope
- Cloudflare generator (separate prompt)
- Terraform module implementation (separate prompts)
- Cross-provider validation (covered in later prompt)

## Desired Behavior

1. **Input**: UniFiConfig schema instance
2. **Output**: JSON matching the UniFi Terraform module input schema:

```json
{
  "devices": [{
    "friendly_hostname": "media-server",
    "domain": "internal.lan",
    "service_cnames": ["shared.internal.lan"],
    "nics": [{
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "nic_name": "mgmt",
      "service_cnames": ["specific.internal.lan"]
    }]
  }]
}
```

3. **Generation Rules**:
   - MAC addresses normalized to `aa:bb:cc:dd:ee:ff` format
   - Services with `unifi_only` or `both` distribution create CNAMEs
   - Device-level CNAMEs from `service_cnames` field
   - NIC-level CNAMEs from each endpoint's `service_cnames`
   - Full FQDNs constructed as `{hostname}.{domain}`

4. **Filtering**:
   - Only include services where distribution != cloudflare_only
   - Skip endpoints without MAC or static IP

## Constraints & Assumptions

1. **JSON Output**: Must be valid JSON with proper escaping
2. **MAC Normalization**: Accept any format, output lowercase colons
3. **Null Handling**: Omit null/empty fields from output
4. **FQDN Construction**: Always include domain suffix

## Acceptance Criteria

- [ ] `kcl/generators/unifi.k` contains `generate_unifi_config()` function
- [ ] Generator outputs valid JSON matching UniFi module input schema
- [ ] MAC addresses are normalized to lowercase colon format
- [ ] Services filtered by distribution (excludes cloudflare_only)
- [ ] CNAMEs correctly generated for device and NIC levels
- [ ] Generator handles empty/optional fields gracefully
- [ ] Generator can be called from KCL with `generate_unifi_config(config)`

## Dependencies

- **Depends On**: 003-kcl-unifi-schemas (UniFi schemas must exist)

## Expected Files/Areas Touched

- `kcl/generators/unifi.k` (new/complete implementation)
