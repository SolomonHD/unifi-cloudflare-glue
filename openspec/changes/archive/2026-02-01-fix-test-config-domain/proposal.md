# Change: Fix Test Config Domain Parameter

## Why

The `test_integration()` function generates test configurations for UniFi and Cloudflare using `_generate_test_configs()`. Currently, the UniFi configuration hardcodes `domain = "local"` and `default_domain = "local"`, which causes DNS records to be created with the wrong FQDN (e.g., `test-q3prv.local` instead of `test-q3prv.sghd.io`). This makes the integration test report misleading and doesn't match the actual expected behavior where test DNS records should use the Cloudflare zone as the domain.

## What Changes

- Modify `_generate_test_configs()` method to accept a new `unifi_domain` parameter
- Update `test_integration()` function to pass the `cloudflare_zone` as the `unifi_domain`
- Update docstrings to document the new parameter
- Ensure backward compatibility with default parameter value

## Impact

- **Affected specs**: dagger-module (test configuration generation)
- **Affected code**: `src/main/main.py` - `_generate_test_configs()` and `test_integration()` methods
- **No breaking changes**: New parameter has a default value for backward compatibility
