# OpenSpec Prompt: Add Generator Output Validation Tests

**Change ID**: `add-generator-output-validation-tests`

## Context

The KCL generators in [`generators/unifi.k`](../../generators/unifi.k) and [`generators/cloudflare.k`](../../generators/cloudflare.k) produce JSON output for Terraform consumption. However, there are no automated tests to verify that:

1. The generated JSON structure matches what Terraform expects
2. Required fields (like `site`, `devices`, etc.) are present
3. Field types are correct (strings, arrays, objects, etc.)
4. The generators handle edge cases properly

The recent bug where the `site` field was missing from UniFi generator output would have been caught by proper output validation tests. Terraform module errors like:

```
Error: Unsupported attribute
  This object does not have an attribute named "devices".
```

should be prevented by validating generator output structure before it reaches Terraform.

## Goal

Add comprehensive tests that validate the structure and content of generator output to catch mismatches between KCL generators and Terraform module expectations.

## Scope

**In Scope:**
- Create tests for [`generators/unifi.k`](../../generators/unifi.k) output validation
- Create tests for [`generators/cloudflare.k`](../../generators/cloudflare.k) output validation
- Validate required fields are present
- Validate field types are correct
- Test with various input scenarios (single device, multiple devices, edge cases)
- Document the expected output schema that matches Terraform requirements

**Out of Scope:**
- Testing the Terraform modules themselves
- Testing KCL validation logic (already in [`main.k`](../../main.k))
- Integration tests that run actual Terraform

## Desired Behavior

When tests run (e.g., via `pytest` or KCL test framework), they should:

1. **Validate UniFi generator output** has all required fields:
   - `devices` (array)
   - `default_domain` (string)
   - `site` (string)
   - Each device has: `friendly_hostname`, `domain`, `nics`, `service_cnames`
   - Each NIC has: `mac_address`, optional `nic_name`, `service_cnames`

2. **Validate Cloudflare generator output** has all required fields:
   - `zone_name` (string)
   - `account_id` (string)
   - `tunnels` (object/dict)
   - Each tunnel has: `tunnel_name`, `mac_address`, `services`
   - Each service has: `public_hostname`, `local_service_url`, optional `no_tls_verify`

3. **Test edge cases**:
   - Empty devices array
   - Devices with no services
   - Devices with multiple NICs
   - Services with various distribution modes
   - MAC address normalization

4. **Provide clear error messages** when validation fails, showing:
   - What field is missing or incorrect
   - What was expected vs. what was found

## Constraints & Assumptions

- Tests should be runnable locally and in CI/CD
- Tests should not require external services (UniFi controller, Cloudflare API)
- Tests should integrate with existing test framework (if Python-based, use existing `tests/` structure)
- Tests should be fast (no network calls, no heavy computation)

## Acceptance Criteria

- [ ] Tests validate UniFi generator output structure matches Terraform module expectations
- [ ] Tests validate Cloudflare generator output structure matches Terraform module expectations
- [ ] Tests cover both success cases and edge cases
- [ ] Tests provide clear error messages on failure
- [ ] Tests are documented and easy to run
- [ ] CI pipeline runs tests automatically
- [ ] Test coverage includes all required fields from Terraform modules

## Expected Files/Areas Touched

- Create or modify [`tests/test_generators.py`](../../tests/) (if Python-based tests)
- Or create KCL-based tests in [`tests/`](../../tests/) directory
- Potentially update [`README.md`](../../README.md) with test documentation
- Potentially add test configuration to [`pyproject.toml`](../../pyproject.toml) or test runner config

## Dependencies

- Should be implemented **after** prompt 11 (add-site-field-to-unifi-generator) is completed
- Tests should validate the fixed generator output

## Test Cases to Include

### UniFi Generator Tests

```python
def test_unifi_generator_has_required_fields():
    """Validate UniFi output has devices, default_domain, and site."""
    
def test_unifi_generator_device_structure():
    """Validate each device has correct fields and types."""
    
def test_unifi_generator_nic_structure():
    """Validate each NIC has correct MAC address format."""
    
def test_unifi_generator_empty_devices():
    """Test behavior with empty devices array."""
    
def test_unifi_generator_multiple_nics():
    """Test device with multiple network interfaces."""
```

### Cloudflare Generator Tests

```python
def test_cloudflare_generator_has_required_fields():
    """Validate Cloudflare output has zone_name, account_id, tunnels."""
    
def test_cloudflare_generator_tunnel_structure():
    """Validate each tunnel has correct fields and types."""
    
def test_cloudflare_generator_service_structure():
    """Validate each service has correct fields."""
    
def test_cloudflare_generator_mac_normalization():
    """Test MAC addresses are normalized consistently."""
```

### Integration Tests

```python
def test_generators_match_terraform_module_expectations():
    """Run sample configs through generators and validate against Terraform variable schemas."""
```
