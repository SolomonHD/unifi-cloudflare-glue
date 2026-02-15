## 1. Modify Generator Function

- [x] 1.1 Add site field to generate_unifi_config() return dictionary in generators/unifi.k
- [x] 1.2 Source site value from config.unifi_controller.site parameter

## 2. Test Generated Output

- [x] 2.1 Run `kcl run generators/unifi.k` and verify output includes "site": "default"
- [x] 2.2 Verify JSON structure has devices, default_domain, and site at root level
- [x] 2.3 Run `kcl run examples/homelab-media-stack/main.k` and verify site field is present
- [x] 2.4 Run `kcl run examples/internal-only/main.k` and verify site field is present
- [x] 2.5 Run `kcl run examples/external-only/main.k` and verify site field is present

## 3. Validation Tests

- [x] 3.1 Verify existing validation tests still pass with new field
- [ ] 3.2 Test with non-default site value (e.g., "production") to ensure parameter flows through correctly
- [x] 3.3 Confirm schema default value "default" is used when site not explicitly configured

## 4. Integration Verification

- [ ] 4.1 Test generated JSON with Terraform module to ensure it can read local.effective_config.site
- [ ] 4.2 Verify no Terraform errors about "Unsupported attribute" for site field
- [ ] 4.3 Confirm existing Terraform resources are not affected by new field (no recreates)

## 5. Documentation

- [x] 5.1 Add note to CHANGELOG.md about fixed missing site field in UniFi generator
- [x] 5.2 Update any generator documentation if it references output structure
