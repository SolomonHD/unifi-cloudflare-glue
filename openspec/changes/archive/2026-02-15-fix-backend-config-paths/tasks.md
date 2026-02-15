## 1. Fix Backend Config Paths in plan() Function

- [x] 1.1 Fix line 1106 in `plan()` function (UniFi plan): Changed to use `_process_backend_config()` and `with_new_file()` with `/root/.terraform/backend.tfbackend`
- [x] 1.2 Fix line 1201 in `plan()` function (Cloudflare plan): Changed to use `_process_backend_config()` and `with_new_file()` with `/root/.terraform/backend.tfbackend`
- [x] 1.3 Verified both mount paths match the terraform init command reference (`-backend-config=/root/.terraform/backend.tfbackend`)

## 2. Fix Backend Config Path in get_tunnel_secrets() Function

- [x] 2.1 Fix line 2821 in `get_tunnel_secrets()` function: Changed to use `_process_backend_config()` and `with_new_file()` with `/root/.terraform/backend.tfbackend`
- [x] 2.2 Verified mount path matches the terraform init command reference

## 3. Verify deploy_* Functions (No Changes Expected)

- [x] 3.1 Verified `deploy_unifi()` function already uses correct path (`/root/.terraform/backend.tfbackend`) via `with_new_file()`
- [x] 3.2 Verified `deploy_cloudflare()` function already uses correct path (`/root/.terraform/backend.tfbackend`) via `with_new_file()`
- [x] 3.3 Documented that `deploy_*` functions already have correct implementation using `_process_backend_config()` pattern

## 4. Validation and Testing

- [x] 4.1 Ran `dagger functions` to verify module loads without errors - ✓ SUCCESS
- [x] 4.2 Reviewed all three changed locations to confirm consistent `.tfbackend` extension usage - All use `.tfbackend`
- [x] 4.3 Checked that no `.hcl` extension is used for mounted backend config files - All use `.tfbackend`
- [x] 4.4 Verified the `_process_backend_config()` function returns `.tfbackend` extension (line 37)

## 5. Documentation Update (if needed)

- [x] 5.1 Reviewed CHANGELOG.md and added entry for this bug fix
- [x] 5.2 Updated inline code comments to be consistent across all functions
