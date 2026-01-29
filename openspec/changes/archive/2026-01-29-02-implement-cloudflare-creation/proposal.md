# Change: Implement Real Cloudflare Resource Creation in Integration Tests

## Why

The `test_integration` function currently simulates Cloudflare resource creation in Phase 2 (lines 960-970) by printing success messages without actually creating any resources. This provides false confidence in test results - the test appears to pass but no actual infrastructure is validated.

To make the integration test meaningful, we need to execute real Terraform commands that create Cloudflare tunnels and DNS records, similar to how the `deploy_cloudflare()` function works (lines 222-298).

## What Changes

- Replace simulated Cloudflare creation in Phase 2 of `test_integration` with real Terraform execution
- Create a Terraform container with the correct image (`hashicorp/terraform:{terraform_version}`)
- Mount the Cloudflare Tunnel Terraform module at `/module`
- Write the generated Cloudflare config JSON to `/workspace/cloudflare.json`
- Set required environment variables (`TF_VAR_cloudflare_account_id`, `TF_VAR_zone_name`, `TF_VAR_config_file`)
- Pass Cloudflare token as a secret (`TF_VAR_cloudflare_token`)
- Execute `terraform init` and capture output
- Execute `terraform apply -auto-approve` and capture output
- Update validation results based on actual Terraform execution
- Implement proper error handling that raises exceptions to trigger cleanup phase

## Impact

- **Affected specs**: `test-integration` (adding new requirements)
- **Affected code**: `src/main/main.py` - Phase 2 of `test_integration` function (lines 960-970)
- **Reference implementation**: `deploy_cloudflare()` function (lines 222-298)
- **Dependencies**: Requires completion of Prompt 01 (config generation fix) for proper JSON format
- **Breaking changes**: None - this is an internal test improvement

## Acceptance Criteria

- [ ] Phase 2 creates a Terraform container with the correct image
- [ ] Cloudflare tunnel module is mounted at `/module`
- [ ] Cloudflare config JSON is written to `/workspace/cloudflare.json`
- [ ] All required environment variables are set
- [ ] Cloudflare token is passed as a secret
- [ ] `terraform init` is executed and output captured
- [ ] `terraform apply -auto-approve` is executed
- [ ] Success messages include actual Terraform output summary
- [ ] Errors are caught and reported, triggering cleanup
- [ ] State tracking variables (`validation_results`) are updated correctly
