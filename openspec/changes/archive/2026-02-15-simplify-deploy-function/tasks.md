## 1. Update deploy() Function Signature

- [x] 1.1 Add `unifi_only: bool = False` parameter to `deploy()` function
- [x] 1.2 Add `cloudflare_only: bool = False` parameter to `deploy()` function
- [x] 1.3 Make `cloudflare_token`, `cloudflare_account_id`, and `zone_name` Optional when `unifi_only=True`
- [x] 1.4 Make UniFi credentials optional when `cloudflare_only=True`
- [x] 1.5 Update function docstring with new parameters and examples

## 2. Implement Flag Validation

- [x] 2.1 Add validation: error if both `unifi_only` and `cloudflare_only` are True
- [x] 2.2 Implement credential requirement validation based on deployment scope
- [x] 2.3 Add clear error messages for missing credentials based on selected mode

## 3. Implement Combined Module Deployment

- [x] 3.1 Modify `deploy()` to mount `terraform/modules/glue/` instead of separate modules
- [x] 3.2 Set up environment variables for combined module (TF_VAR_unifi_url, TF_VAR_cloudflare_token, etc.)
- [x] 3.3 Handle conditional config generation based on deployment scope
- [x] 3.4 Implement single Terraform init/apply cycle
- [x] 3.5 Preserve container reference after execution for potential state export

## 4. Remove Deprecated Functions

- [x] 4.1 Remove `deploy_unifi()` function (lines ~356-588)
- [x] 4.2 Remove `deploy_cloudflare()` function (lines ~589-841)
- [x] 4.3 Clean up any orphaned imports or helper functions only used by removed functions
- [x] 4.4 Verify no other functions reference the removed functions

## 5. Update KCL Generation Logic

- [x] 5.1 Modify config generation to skip Cloudflare when `unifi_only=True`
- [x] 5.2 Modify config generation to skip UniFi when `cloudflare_only=True`
- [x] 5.3 Ensure both configs are generated for default (full) deployment

## 6. Testing

- [ ] 6.1 Test `deploy()` with `--unifi-only` flag (UniFi deployment only)
- [ ] 6.2 Test `deploy()` with `--cloudflare-only` flag (Cloudflare deployment only)
- [ ] 6.3 Test `deploy()` without flags (full deployment)
- [ ] 6.4 Test error case: both flags set simultaneously
- [ ] 6.5 Test error case: missing credentials for selected scope
- [x] 6.6 Verify `dagger functions` lists only the updated `deploy()` function
- [ ] 6.7 Run integration tests if available

## 7. Documentation

- [x] 7.1 Update function docstrings with new usage examples
- [x] 7.2 Document breaking change in CHANGELOG.md
- [x] 7.3 Add migration notes from old `deploy_unifi()`/`deploy_cloudflare()` to new flags

## 8. Validation

- [x] 8.1 Run `dagger functions` to verify module loads correctly
- [x] 8.2 Run `dagger call deploy --help` to verify new parameters appear
- [x] 8.3 Verify no syntax errors in `src/main/main.py`
- [x] 8.4 Confirm `deploy_unifi` and `deploy_cloudflare` no longer appear in function list
