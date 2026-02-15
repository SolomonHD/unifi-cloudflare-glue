# OpenSpec Prompt: Add site Field to UniFi Generator Output

**Change ID**: `add-site-field-to-unifi-generator`

## Context

The UniFi Terraform module expects a `site` field in the JSON configuration at `local.effective_config.site`, but the KCL generator in [`generators/unifi.k`](../../generators/unifi.k) does not include this field in its output. This causes Terraform plan/apply to fail with errors like:

```
Error: Unsupported attribute
  on main.tf line 118: local.effective_config is object with no attributes
```

The `site` field is referenced in multiple places in [`terraform/modules/unifi-dns/main.tf`](../../terraform/modules/unifi-dns/main.tf):
- Line 118: `data.unifi_user.device` resource
- Line 131: `resource.unifi_dns_record.dns_record`
- Line 176: `resource.unifi_dns_record.cname_record`

The [`unifi.UniFiConfig`](../../schemas/unifi.k) schema includes a `unifi_controller.site` field (default: "default"), but the generator function [`generate_unifi_config()`](../../generators/unifi.k:52) only outputs `devices` and `default_domain`.

## Goal

Modify the UniFi generator to include the `site` field in its JSON output, sourced from `config.unifi_controller.site`.

## Scope

**In Scope:**
- Modify [`generators/unifi.k`](../../generators/unifi.k) to add `site` field to generated output
- Ensure `site` value comes from `config.unifi_controller.site`
- Verify the output matches what Terraform expects

**Out of Scope:**
- Changing the UniFi schema structure
- Modifying Terraform module expectations
- Adding validation for `site` values

## Desired Behavior

When `generate_unifi_config()` is called, the JSON output should include:

```json
{
  "devices": [...],
  "default_domain": "internal.lan",
  "site": "default"
}
```

The `site` value should be extracted from `config.unifi_controller.site`.

## Constraints & Assumptions

- The `site` field already exists in the [`unifi.UniFiController`](../../schemas/unifi.k) schema with default value `"default"`
- All existing examples in `examples/*/main.k` set `unifi_controller.site = "default"`
- The Terraform module expects `site` to be a string at the root level of the JSON config
- Do not break existing functionality for `devices` and `default_domain` fields

## Acceptance Criteria

- [ ] [`generators/unifi.k`](../../generators/unifi.k) `generate_unifi_config()` function outputs `site` field
- [ ] `site` value is populated from `config.unifi_controller.site`
- [ ] Running `kcl run main.k` produces JSON with `site` field
- [ ] Existing examples continue to work
- [ ] The generated JSON structure matches Terraform module expectations

## Expected Files/Areas Touched

- [`generators/unifi.k`](../../generators/unifi.k) - Modify `generate_unifi_config()` function (lines 52-56)

## Dependencies

None. This is a standalone fix.
