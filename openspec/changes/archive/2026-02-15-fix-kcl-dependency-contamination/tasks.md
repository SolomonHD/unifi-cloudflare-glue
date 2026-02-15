## 1. Modify `generate_unifi_config()` in `src/main/main.py`

- [x] 1.1 Add `kcl mod update` execution before `kcl run` in `generate_unifi_config()`
- [x] 1.2 Implement error handling for `kcl mod update` failures (network issues, invalid kcl.mod)
- [x] 1.3 Ensure container reference is preserved after `kcl mod update` execution
- [x] 1.4 Test that `generate_unifi_config()` produces valid JSON for modules with git dependencies
- [x] 1.5 Test that `generate_unifi_config()` works for modules without git dependencies

## 2. Modify `generate_cloudflare_config()` in `src/main/main.py`

- [x] 2.1 Add `kcl mod update` execution before `kcl run` in `generate_cloudflare_config()`
- [x] 2.2 Implement error handling for `kcl mod update` failures (network issues, invalid kcl.mod)
- [x] 2.3 Ensure container reference is preserved after `kcl mod update` execution
- [x] 2.4 Test that `generate_cloudflare_config()` produces valid JSON for modules with git dependencies
- [x] 2.5 Test that `generate_cloudflare_config()` works for modules without git dependencies

## 3. Validation and Error Handling

- [x] 3.1 Verify error messages are clear when `kcl mod update` fails due to network issues
- [x] 3.2 Verify error messages include original KCL stderr output
- [x] 3.3 Test error handling for invalid kcl.mod syntax
- [x] 3.4 Confirm `KCLGenerationError` is raised appropriately with helpful hints

## 4. Integration Testing

- [x] 4.1 Run `dagger functions` to verify module loads correctly
- [x] 4.2 Test with example KCL module that has git dependencies
- [x] 4.3 Verify generated `unifi.json` contains valid JSON without git clone messages
- [x] 4.4 Verify generated `cloudflare.json` contains valid JSON without git clone messages
- [x] 4.5 Test full deployment workflow with `generate-unifi-config` and `generate-cloudflare-config`

## 5. Documentation Updates

- [x] 5.1 Update CHANGELOG.md with fix description
- [x] 5.2 Add any troubleshooting notes for dependency download issues
