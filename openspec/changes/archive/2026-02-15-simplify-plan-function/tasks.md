## 1. Update plan() Function Signature

- [x] 1.1 Add `unifi_only: bool = False` parameter to `plan()` function
- [x] 1.2 Add `cloudflare_only: bool = False` parameter to `plan()` function
- [x] 1.3 Make `cloudflare_token` parameter optional (default `None`)
- [x] 1.4 Make `cloudflare_account_id` parameter optional (default `""`)
- [x] 1.5 Make `zone_name` parameter optional (default `""`)
- [x] 1.6 Make `unifi_url` parameter optional (default `""`)
- [x] 1.7 Update function docstring with new parameters and usage examples

## 2. Implement Flag Validation

- [x] 2.1 Add validation to prevent both `--unifi-only` and `--cloudflare-only` being True
- [x] 2.2 Raise `ValueError` with clear error message when both flags are set

## 3. Implement Conditional Credential Validation

- [x] 2.1 Implement credential validation for full deployment mode (both required)
- [x] 2.2 Implement credential validation for UniFi-only mode (UniFi required, Cloudflare optional)
- [x] 2.3 Implement credential validation for Cloudflare-only mode (Cloudflare required, UniFi optional)
- [x] 2.4 Add clear error messages indicating which credentials are missing

## 4. Update KCL Configuration Generation

- [x] 4.1 Conditionally generate UniFi config only when not `cloudflare_only`
- [x] 4.2 Conditionally generate Cloudflare config only when not `unifi_only`
- [x] 4.3 Skip config generation and mount when component is not selected

## 5. Update Terraform Module Usage

- [x] 5.1 Replace separate UniFi and Cloudflare module mounting with combined `terraform/modules/glue/` module
- [x] 5.2 Update container setup to use single Terraform container with combined module
- [x] 5.3 Mount configuration directories conditionally based on selected components
- [x] 5.4 Set environment variables conditionally based on selected components
- [x] 5.5 Set secret variables conditionally based on selected components

## 6. Update Plan Artifact Generation

- [x] 6.1 Generate unified plan files (`plan.tfplan`, `plan.json`, `plan.txt`) from combined module
- [x] 6.2 Update plan summary generation to indicate which components were planned
- [x] 6.3 Ensure plan files are extracted from correct container path
- [x] 6.4 Return output directory with all plan artifacts

## 7. Update Docstrings and Examples

- [x] 7.1 Update function docstring to document new selective deployment flags
- [x] 7.2 Add usage example for UniFi-only plan
- [x] 7.3 Add usage example for Cloudflare-only plan
- [x] 7.4 Update Args section to reflect optional parameters

## 8. Testing and Validation

- [ ] 8.1 Test `plan()` with full deployment (both components)
- [ ] 8.2 Test `plan()` with `--unifi-only` flag
- [ ] 8.3 Test `plan()` with `--cloudflare-only` flag
- [ ] 8.4 Test validation error when both flags are provided
- [ ] 8.5 Test validation error when missing credentials for selected mode
- [ ] 8.6 Verify plan artifacts are generated correctly for each mode
