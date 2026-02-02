## 1. Fix Cloudflare State Mounting

- [x] 1.1 Replace `.with_directory("/module", cloudflare_state_dir)` with file extraction and mounting
- [x] 1.2 Extract `terraform.tfstate` file from `cloudflare_state_dir` using `.file("terraform.tfstate")`
- [x] 1.3 Mount extracted file at `/module/terraform.tfstate` using `.with_file()`
- [x] 1.4 Wrap state mounting in try/except block
- [x] 1.5 Add success message: "✓ Cloudflare state file mounted for state-based destroy"
- [x] 1.6 Add failure handling to log warning and set state_dir to None
- [x] 1.7 Preserve existing "⚠ No state file available" warning when state_dir is None

## 2. Fix UniFi State Mounting

- [x] 2.1 Replace `.with_directory("/module", unifi_state_dir)` with file extraction and mounting
- [x] 2.2 Extract `terraform.tfstate` file from `unifi_state_dir` using `.file("terraform.tfstate")`
- [x] 2.3 Mount extracted file at `/module/terraform.tfstate` using `.with_file()`
- [x] 2.4 Wrap state mounting in try/except block
- [x] 2.5 Add success message: "✓ UniFi state file mounted for state-based destroy"
- [x] 2.6 Add failure handling to log warning and set state_dir to None
- [x] 2.7 Preserve existing "⚠ No state file available" warning when state_dir is None

## 3. Validation

- [x] 3.1 Verify Terraform module files remain intact at `/module`
- [x] 3.2 Verify state file is correctly accessible at `/module/terraform.tfstate`
- [ ] 3.3 Run integration test to confirm successful resource destruction
- [x] 3.4 Verify success/failure messages appear in test output
