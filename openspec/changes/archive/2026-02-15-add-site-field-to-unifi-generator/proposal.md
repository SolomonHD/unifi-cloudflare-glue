## Why

The UniFi Terraform module requires a `site` field in the JSON configuration to specify which UniFi site manages the DNS records, but the KCL generator function `generate_unifi_config()` does not include this field in its output. This causes Terraform to fail with "Unsupported attribute" errors when attempting to reference `local.effective_config.site` in the UniFi DNS module. The field already exists in the schema (`unifi_controller.site`) but is simply not being passed through to the generated output.

## What Changes

- Modify [`generators/unifi.k`](../../generators/unifi.k) `generate_unifi_config()` function to include `site` field in the generated JSON output
- Source the `site` value from `config.unifi_controller.site` (already defined in schema with default value "default")
- Ensure generated JSON structure matches Terraform module expectations

## Capabilities

### New Capabilities
- `unifi-site-field-generation`: KCL UniFi generator includes site field in output JSON, sourced from unifi_controller.site configuration

### Modified Capabilities
<!-- No existing requirement changes - this is a bugfix that completes the generator implementation -->

## Impact

**Affected Code:**
- [`generators/unifi.k`](../../generators/unifi.k) - `generate_unifi_config()` function (lines 52-56)

**Affected Systems:**
- UniFi DNS Terraform module - will now receive the expected `site` field
- Existing examples continue to work (all already set `unifi_controller.site = "default"`)

**Dependencies:**
- No breaking changes
- No new dependencies
- Backward compatible (adds missing field that was already in schema)
