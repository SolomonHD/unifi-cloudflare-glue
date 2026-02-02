# Tasks: Fix Test Config Domain Parameter

## 1. Implementation

- [x] 1.1 Modify `_generate_test_configs()` signature to add `unifi_domain: str = ""` parameter
- [x] 1.2 Add logic to default `unifi_domain` to `cloudflare_zone` when empty
- [x] 1.3 Update UniFi config `domain` field to use `unifi_domain` variable (line 811)
- [x] 1.4 Update UniFi config `default_domain` field to use `unifi_domain` variable (line 822)
- [x] 1.5 Update `_generate_test_configs()` docstring to document the new parameter
- [x] 1.6 Modify `test_integration()` call to pass `cloudflare_zone` as `unifi_domain` (line 1019)

## 2. Validation

- [x] 2.1 Run `dagger functions` to ensure module loads correctly
- [x] 2.2 Verify no syntax errors in modified code
- [x] 2.3 Review test report output format shows correct FQDN

## 3. Documentation

- [x] 3.1 Update function docstrings with new parameter description
- [x] 3.2 Verify examples in docstrings reflect correct behavior

## Summary of Changes

### Modified Files
- `src/main/main.py` - Updated `_generate_test_configs()` and `test_integration()` functions

### Key Changes
1. Added `unifi_domain: str = ""` parameter to `_generate_test_configs()` method
2. Added logic to default `unifi_domain` to `cloudflare_zone` when not provided
3. Updated UniFi config generation to use `effective_unifi_domain` instead of hardcoded "local"
4. Updated `test_integration()` to pass `cloudflare_zone` as `unifi_domain` parameter
5. Updated test report output to show correct FQDN (e.g., `test-abc12.sghd.io` instead of `test-abc12.local`)

### Backward Compatibility
- The new parameter has a default value of empty string, ensuring backward compatibility
- Existing code calling `_generate_test_configs()` without the new parameter will continue to work
- When `unifi_domain` is empty, it defaults to `cloudflare_zone` value
