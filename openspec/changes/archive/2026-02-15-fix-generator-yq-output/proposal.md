## Why

The KCL generator files (`generators/unifi.k` and `generators/cloudflare.k`) currently output both `sample_config` and `result` variables, producing multi-document YAML. When Dagger pipes this output to `yq eval -o=json '.'`, yq fails with "mapping values are not allowed in this context" because it cannot parse multi-document YAML from stdin. This prevents the Dagger module from successfully converting KCL output to JSON for Terraform consumption.

## What Changes

- **Modify `generators/unifi.k`**: Remove `sample_config` variable from direct output; only output the `result` variable
- **Modify `generators/cloudflare.k`**: Remove `sample_config` variable from direct output; only output the `result` variable
- **Create test file for unifi generator**: Move `sample_config` from `generators/unifi.k` to a new test file that outputs both sample and result for testing purposes
- **Create test file for cloudflare generator**: Move `sample_config` from `generators/cloudflare.k` to a new test file for testing purposes

## Capabilities

### New Capabilities

- `kcl-generator-unifi`: UniFi KCL generator outputs single-document YAML that can be parsed by yq
- `kcl-generator-cloudflare`: Cloudflare KCL generator outputs single-document YAML that can be parsed by yq
- `kcl-generator-tests`: Sample configurations remain testable via dedicated test files

### Modified Capabilities

- None (this is a bug fix with no spec-level requirement changes)

## Impact

- **KCL Generator Files**: `generators/unifi.k`, `generators/cloudflare.k`
- **New Test Files**: `generators/test_unifi.k`, `generators/test_cloudflare.k` (or similar)
- **Dagger Module**: `generate-unifi-config` and `generate-cloudflare-config` functions will work correctly
- **User Impact**: None for users importing generators; sample configs move to test files for standalone testing
