## Context

The current [`generate_unifi_config()`](../../generators/unifi.k:52-57) function only outputs `devices` and `default_domain` fields, but the UniFi Terraform module expects a `site` field at `local.effective_config.site` to determine which UniFi site to manage DNS records within. The schema already includes `site` in [`UniFiController`](../../schemas/unifi.k:171) with a default value of `"default"`, but it's not being passed through to the generated JSON output.

The UniFi Terraform module references the `site` field in multiple places:
- Line 118: `data.unifi_user.device` data source
- Line 131: `resource.unifi_dns_record.dns_record` resource
- Line 176: `resource.unifi_dns_record.cname_record` resource

This is a simple generator completion fix - the plumbing already exists in the schema, it just needs to be included in the output.

## Goals / Non-Goals

**Goals:**
- Add `site` field to the JSON output of [`generate_unifi_config()`](../../generators/unifi.k)
- Source the value from `config.unifi_controller.site`
- Maintain backward compatibility with existing examples
- Match Terraform module's expected JSON structure

**Non-Goals:**
- Changing the schema or adding new fields
- Modifying how Terraform consumes the JSON
- Adding validation for site values (exists in schema already)
- Changing any existing field generation logic

## Decisions

### Decision: Add site as root-level field in generator output

**Rationale**: The Terraform module expects `site` at the same level as `devices` and `default_domain`. This matches the existing pattern where `default_domain` is also sourced from the config root.

**Alternatives considered**:
- **Nest under a controller object**: Would require Terraform module changes (breaking). Rejected.
- **Use per-device site from UniFiEntity.unifi_site**: More flexible but requires aggregation logic and Terraform changes. The current module uses a single global site. Future enhancement if needed.

**Implementation**:
```kcl
generate_unifi_config = lambda config: unifi.UniFiConfig {
    {
        devices = [transform_entity(device) for device in config.devices]
        default_domain = config.default_domain
        site = config.unifi_controller.site  # Add this line
    }
}
```

### Decision: Use global site from unifi_controller

**Rationale**: The Terraform module currently uses a single site for all DNS operations. While individual devices have `unifi_site` fields in the schema, the Terraform integration operates at the controller level.

**Future consideration**: If per-device site management is needed, that would be a separate change requiring Terraform module updates to iterate devices and group by site.

### Decision: No migration needed

**Rationale**: This is purely additive. The field was missing, causing errors. Adding it fixes the errors without changing any existing behavior. All examples already specify `unifi_controller.site = "default"` in their configurations, so they'll work immediately.

## Risks / Trade-offs

**[Risk] Device-level site field (unifi_site) is ignored**  
→ **Mitigation**: This is documented behavior. The Terraform module operates at the controller level. If per-device site support is needed, file a separate feature request. For now, all devices in a config must use the same site (enforced by using `config.unifi_controller.site`).

**[Risk] Existing Terraform state might be sensitive to JSON structure changes**  
→ **Mitigation**: Adding a new field to the JSON doesn't affect existing resources since they're all using data sources and resource IDs. Terraform will see the new field and use it, but existing resources won't be recreated.

**[Trade-off] Consistency between generator functions**  
→ The Cloudflare generator doesn't have any similar missing fields. This fix is isolated to UniFi generator only. Verified by reviewing [`generators/cloudflare.k`](../../generators/cloudflare.k).

## Implementation Notes

**File to modify**: [`generators/unifi.k`](../../generators/unifi.k), specifically lines 52-56

**One-line change** to the return dictionary:
- Add: `site = config.unifi_controller.site`

**Testing approach**:
1. Run `kcl run generators/unifi.k` to test the sample config
2. Verify output includes `"site": "default"`
3. Run all example configs (`kcl run examples/*/main.k`)
4. Verify each generates JSON with `site` field
5. Test with Terraform module to ensure it can read the field

**Validation**: The existing KCL schema validation will ensure `site` is always present and is a valid string.
