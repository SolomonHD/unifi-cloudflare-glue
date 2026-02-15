## 1. Create Test Infrastructure

- [x] 1.1 Create `tests/unit/test_generator_output.py` test file
- [x] 1.2 Set up pytest fixtures for loading KCL generator output
- [x] 1.3 Create helper functions for running KCL generators in test mode
- [x] 1.4 Add test configuration to `pyproject.toml` if needed

## 2. UniFi Generator Validation Tests

- [x] 2.1 Test `test_unifi_has_required_top_level_fields` - devices, default_domain, site
- [x] 2.2 Test `test_unifi_devices_is_array` - verify devices field type
- [x] 2.3 Test `test_unifi_default_domain_is_string` - verify default_domain type
- [x] 2.4 Test `test_unifi_site_is_string` - verify site field type
- [x] 2.5 Test `test_unifi_device_has_friendly_hostname` - each device has hostname
- [x] 2.6 Test `test_unifi_device_has_domain` - each device has domain
- [x] 2.7 Test `test_unifi_device_has_service_cnames` - each device has cnames array
- [x] 2.8 Test `test_unifi_device_has_nics` - each device has nics array
- [x] 2.9 Test `test_unifi_nic_has_mac_address` - each NIC has MAC
- [x] 2.10 Test `test_unifi_nic_mac_is_normalized` - MAC in aa:bb:cc:dd:ee:ff format
- [x] 2.11 Test `test_unifi_nic_has_optional_name` - nic_name is optional
- [x] 2.12 Test `test_unifi_nic_has_service_cnames` - NIC has cnames array

## 3. Cloudflare Generator Validation Tests

- [x] 3.1 Test `test_cloudflare_has_required_top_level_fields` - zone_name, account_id, tunnels
- [x] 3.2 Test `test_cloudflare_zone_name_is_string` - verify zone_name type
- [x] 3.3 Test `test_cloudflare_account_id_is_string` - verify account_id type
- [x] 3.4 Test `test_cloudflare_tunnels_is_object` - verify tunnels is dict/object
- [x] 3.5 Test `test_cloudflare_tunnel_has_tunnel_name` - each tunnel has name
- [x] 3.6 Test `test_cloudflare_tunnel_has_mac_address` - each tunnel has MAC
- [x] 3.7 Test `test_cloudflare_tunnel_mac_is_normalized` - MAC in normalized format
- [x] 3.8 Test `test_cloudflare_tunnel_has_services` - each tunnel has services array
- [x] 3.9 Test `test_cloudflare_service_has_public_hostname` - service has hostname
- [x] 3.10 Test `test_cloudflare_service_has_local_service_url` - service has URL
- [x] 3.11 Test `test_cloudflare_service_has_no_tls_verify` - service has TLS verify flag

## 4. Edge Case Tests

- [x] 4.1 Test `test_unifi_empty_devices_array` - handles empty devices
- [x] 4.2 Test `test_unifi_device_with_no_services` - device with empty services
- [x] 4.3 Test `test_unifi_device_with_multiple_nics` - multiple NIC handling
- [x] 4.4 Test `test_mac_normalization_various_formats` - AA:BB:CC, aa-bb-cc, AABBCC
- [x] 4.5 Test `test_cloudflare_empty_tunnels` - handles empty tunnels object
- [x] 4.6 Test `test_cloudflare_tunnel_with_no_services` - tunnel with empty services
- [x] 4.7 Test `test_service_distribution_filtering` - unifi_only, cloudflare_only, both

## 5. Error Message Tests

- [x] 5.1 Test `test_missing_field_error_message` - clear message on missing field
- [x] 5.2 Test `test_wrong_type_error_message` - clear message on type mismatch
- [x] 5.3 Test `test_invalid_mac_format_error_message` - clear MAC format error
- [x] 5.4 Test `test_validation_error_includes_path` - error shows field path

## 6. Integration with Test Suite

- [x] 6.1 Ensure tests run with `pytest tests/unit/test_generator_output.py`
- [x] 6.2 Ensure tests run with `pytest tests/unit/` (all unit tests)
- [x] 6.3 Add test markers if needed (e.g., `@pytest.mark.generator`)
- [x] 6.4 Verify test coverage reporting includes generator tests

## 7. CI/CD Integration

- [x] 7.1 Update CI pipeline to run generator validation tests
- [x] 7.2 Ensure tests run on PR creation
- [x] 7.3 Ensure tests run on merge to main
- [x] 7.4 Configure test failure to block merge

## 8. Documentation

- [x] 8.1 Document how to run generator tests in README
- [x] 8.2 Document expected generator output format
- [x] 8.3 Add example of test failure output
- [x] 8.4 Update CHANGELOG.md with testing improvements

## 9. Validation

- [x] 9.1 Verify all tests pass with current generator implementation
- [x] 9.2 Verify tests would have caught missing `site` field bug
- [x] 9.3 Verify tests would catch type mismatches
- [x] 9.4 Verify tests provide actionable error messages
- [x] 9.5 Run full test suite to ensure no regressions

## Bug Fix

- [x] Fixed missing `mac_address` field in Cloudflare generator output
  - Added `mac_address = normalize_mac(tunnel.mac_address)` to `generate_cloudflare_config()`
  - Tests now pass (40/40)
  - This demonstrates the value of the generator validation tests
