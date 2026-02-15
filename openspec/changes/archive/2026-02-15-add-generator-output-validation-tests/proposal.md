## Why

The KCL generators in [`generators/unifi.k`](../../generators/unifi.k) and [`generators/cloudflare.k`](../../generators/cloudflare.k) produce JSON output for Terraform consumption. However, there are currently no automated tests to verify that:

1. The generated JSON structure matches what Terraform modules expect
2. Required fields (like `site`, `devices`, `zone_name`, `tunnels`, etc.) are present
3. Field types are correct (strings, arrays, objects, etc.)
4. The generators handle edge cases properly (empty devices, multiple NICs, etc.)

A recent bug where the `site` field was missing from UniFi generator output caused Terraform errors like:

```
Error: Unsupported attribute
  This object does not have an attribute named "devices".
```

These types of issues should be caught by proper output validation tests before the code reaches production.

## What Changes

- Create comprehensive test suite for generator output validation in `tests/unit/test_generator_output.py`
- Add validation tests for UniFi generator output structure matching [`terraform/modules/unifi-dns/variables.tf`](../../terraform/modules/unifi-dns/variables.tf) expectations
- Add validation tests for Cloudflare generator output structure matching [`terraform/modules/cloudflare-tunnel/variables.tf`](../../terraform/modules/cloudflare-tunnel/variables.tf) expectations
- Test required field presence: `devices`, `default_domain`, `site` (UniFi); `zone_name`, `account_id`, `tunnels` (Cloudflare)
- Test field types and nested structure (NICs, services, tunnel configurations)
- Test edge cases: empty devices array, devices with no services, multiple NICs, MAC address normalization
- Provide clear, actionable error messages when validation fails
- Update CI pipeline to run generator validation tests automatically
- Document expected output schema for both generators

## Capabilities

### New Capabilities
- `generator-output-validation`: Automated testing of KCL generator output structure and content

### Modified Capabilities
- None - This is a testing enhancement that validates existing generator behavior

## Impact

**Affected Code:**
- New file: `tests/unit/test_generator_output.py` - Comprehensive generator validation tests
- Potential updates to `pyproject.toml` for test configuration
- CI pipeline configuration for automated test execution

**API Compatibility:**
- No breaking changes - tests validate existing behavior
- No changes to generator function signatures or output format

**Dependencies:**
- Uses existing pytest testing framework
- No new runtime dependencies required
- Tests run against actual KCL generator output

**User Experience:**
- Developers will have confidence that generator changes don't break Terraform compatibility
- CI will catch generator output mismatches before merge
- Clear test failure messages indicate exactly which fields are missing or incorrect
**Documentation:**
- Test documentation will clarify expected generator output format
- README updates may be needed to describe how to run generator tests
