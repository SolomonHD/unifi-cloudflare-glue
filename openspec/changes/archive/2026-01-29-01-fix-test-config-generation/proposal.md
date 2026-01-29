# Proposal: Fix Test Config Generation

## Change ID
`01-fix-test-config-generation`

## Summary

Replace the KCL-based test config generation with direct JSON generation that matches the Terraform module variable structures. The current `_generate_test_kcl_config()` method outputs raw KCL code, but the Terraform modules expect JSON configuration files.

## Motivation

The `test_integration` function currently generates test configuration using `_generate_test_kcl_config()` which outputs KCL code. However, the Terraform modules expect JSON configuration files:

- **Cloudflare module** (`terraform/modules/cloudflare-tunnel/`): Expects `cloudflare.json` with `zone_name`, `account_id`, and `tunnels` map
- **UniFi module** (`terraform/modules/unifi-dns/`): Expects `unifi.json` with `devices` list containing MAC addresses

This mismatch prevents the integration test from properly creating Terraform-compatible configurations.

## Goals

1. Modify `_generate_test_kcl_config()` method to generate JSON instead of KCL
2. Rename method to `_generate_test_configs()` for clarity
3. Generate both Cloudflare and UniFi JSON configs in one call
4. Return a dict with both config strings

## Non-Goals

- Changing how the configs are used in `test_integration`
- Adding Terraform execution logic
- Modifying the test phases
- Changing the actual test logic (validation, cleanup)

## Related Changes

This is **Prompt 01** in a sequence of 5 prompts to transform `test_integration` from a simulated/mock test into a real integration test:

| Order | Change | Description |
|-------|--------|-------------|
| 01 | `01-fix-test-config-generation` | **This change** - Fix test config generation to output proper Terraform-compatible JSON |
| 02 | `02-implement-cloudflare-creation` | Implement real Cloudflare tunnel and DNS creation via Terraform |
| 03 | `03-implement-unifi-creation` | Implement real UniFi DNS record creation via Terraform |
| 04 | `04-implement-real-validation` | Implement real validation via Cloudflare and UniFi API calls |
| 05 | `05-implement-real-cleanup` | Implement real cleanup via terraform destroy |

## Target File

- `src/main/main.py` - Lines 710-750 (current `_generate_test_kcl_config()` method)

## Success Criteria

- [ ] `_generate_test_kcl_config()` is renamed to `_generate_test_configs()`
- [ ] Method returns a dict with "cloudflare" and "unifi" keys
- [ ] Cloudflare config JSON matches the module's variable structure
- [ ] UniFi config JSON matches the module's variable structure
- [ ] `test_id` is used consistently in tunnel names and hostnames
- [ ] Both configs use the same fake MAC address
- [ ] Method has proper docstring explaining return format

## Dependencies

None - this is the foundational change for the integration test sequence.

## Risks

- **Low risk**: This is a private method change that doesn't affect the public API
- The method is only used within `test_integration`, so impact is isolated

## Notes

- The generated JSON must match the variable types defined in:
  - `terraform/modules/cloudflare-tunnel/variables.tf`
  - `terraform/modules/unifi-dns/variables.tf`
- Use `json.dumps()` to generate valid JSON
- MAC address format must match the regex in variables.tf: `^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$|^[0-9a-fA-F]{12}$`
