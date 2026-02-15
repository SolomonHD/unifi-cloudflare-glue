## 1. Fix Terraform Module Loading in deploy_unifi()

- [x] 1.1 Locate `deploy_unifi()` function in [`src/main/main.py`](src/main/main.py:406)
- [x] 1.2 Replace `dagger.dag.directory().directory("terraform/modules/unifi-dns")` with `dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")`
- [x] 1.3 Verify error handling is preserved

## 2. Fix Terraform Module Loading in deploy_cloudflare()

- [x] 2.1 Locate `deploy_cloudflare()` function in [`src/main/main.py`](src/main/main.py:565)
- [x] 2.2 Replace `dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")` with `dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")`
- [x] 2.3 Verify error handling is preserved

## 3. Fix Terraform Module Loading in plan() - UniFi Path

- [x] 3.1 Locate `plan()` function's UniFi module loading in [`src/main/main.py`](src/main/main.py:1094)
- [x] 3.2 Replace `dagger.dag.directory().directory("terraform/modules/unifi-dns")` with `dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")`
- [x] 3.3 Verify error handling is preserved

## 4. Fix Terraform Module Loading in plan() - Cloudflare Path

- [x] 4.1 Locate `plan()` function's Cloudflare module loading in [`src/main/main.py`](src/main/main.py:1189)
- [x] 4.2 Replace `dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")` with `dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")`
- [x] 4.3 Verify error handling is preserved

## 5. Fix Terraform Module Loading in destroy() - Cloudflare Path

- [x] 5.1 Locate `destroy()` function's Cloudflare module loading in [`src/main/main.py`](src/main/main.py:1473)
- [x] 5.2 Replace `dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")` with `dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")`
- [x] 5.3 Verify error handling is preserved

## 6. Fix Terraform Module Loading in destroy() - UniFi Path

- [x] 6.1 Locate `destroy()` function's UniFi module loading in [`src/main/main.py`](src/main/main.py:1567)
- [x] 6.2 Replace `dagger.dag.directory().directory("terraform/modules/unifi-dns")` with `dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")`
- [x] 6.3 Verify error handling is preserved

## 7. Fix Terraform Module Loading in test_integration()

- [x] 7.1 Locate `test_integration()` function in [`src/main/main.py`](src/main/main.py:2204)
- [x] 7.2 Replace `dagger.dag.directory().directory("terraform/modules/unifi-dns")` with `dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")`
- [x] 7.3 Verify error handling is preserved

## 8. Fix Terraform Module Loading in get_tunnel_secrets()

- [x] 8.1 Locate `get_tunnel_secrets()` function in [`src/main/main.py`](src/main/main.py:2805)
- [x] 8.2 Replace `dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")` with `dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")`
- [x] 8.3 Verify error handling is preserved

## 9. Update Documentation

- [x] 9.1 Add bug fix entry to CHANGELOG.md
- [x] 9.2 Bump patch version in VERSION file (e.g., 1.0.3 → 1.0.4)

## 10. Verification

- [x] 10.1 Run `dagger functions` to verify module loads without errors
- [x] 10.2 Verify all 8+ pattern replacements were made correctly
- [x] 10.3 Test by calling module from external project (if possible)
- [x] 10.4 Verify no regressions in existing functionality
