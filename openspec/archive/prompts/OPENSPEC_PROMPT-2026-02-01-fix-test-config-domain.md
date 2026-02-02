# OpenSpec Prompt: Fix Test Config Domain Parameter

## Context

The `test_integration()` function in `src/main/main.py` generates test configurations for UniFi and Cloudflare using `_generate_test_configs()`. Currently, the UniFi configuration hardcodes `domain = "local"` and `default_domain = "local"`, which causes DNS records to be created with the wrong FQDN (e.g., `test-q3prv.local` instead of `test-q3prv.sghd.io`).

## Goal

Modify the test configuration generation to accept a configurable UniFi domain parameter that defaults to the Cloudflare zone name, ensuring test DNS records are created with the correct FQDN.

## Scope

### In Scope
- Modify `_generate_test_configs()` method to accept `unifi_domain` parameter
- Update `test_integration()` function to pass the domain parameter
- Update docstrings and examples
- Ensure backward compatibility

### Out of Scope
- Changes to KCL generators
- Changes to Terraform modules
- Changes to the actual DNS provider logic

## Desired Behavior

1. The `_generate_test_configs()` method should accept a new `unifi_domain` parameter
2. If `unifi_domain` is not provided, it should default to the `cloudflare_zone` value
3. The UniFi config should use this domain for both `domain` field on devices and `default_domain`
4. Test DNS records should be created as `{test_id}.{unifi_domain}` (e.g., `test-q3prv.sghd.io`)

## Constraints & Assumptions

- The Cloudflare zone name (e.g., "sghd.io") is the same as the UniFi domain
- This is for test configuration generation only
- The change must not break existing functionality
- The method signature change should be backward compatible (default parameter)

## Acceptance Criteria

- [ ] `_generate_test_configs()` accepts `unifi_domain: str = ""` parameter
- [ ] When `unifi_domain` is empty, it defaults to `cloudflare_zone`
- [ ] UniFi config uses `unifi_domain` for device `domain` field
- [ ] UniFi config uses `unifi_domain` for `default_domain` field
- [ ] `test_integration()` passes `cloudflare_zone` as `unifi_domain`
- [ ] Docstrings are updated to document the new parameter
- [ ] Test hostname in reports shows correct FQDN (e.g., `test-q3prv.sghd.io`)

## Files to Modify

- `src/main/main.py`: Update `_generate_test_configs()` and `test_integration()` methods

## Dependencies

None - this is the first change in the sequence.
