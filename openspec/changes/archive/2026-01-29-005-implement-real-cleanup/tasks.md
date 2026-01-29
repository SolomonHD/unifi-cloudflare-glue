# Tasks: Implement Real Resource Cleanup

## Implementation Tasks

### Phase 5 Cleanup Implementation

- [x] **TASK-001:** Create Cloudflare cleanup container
  - Create Terraform container from `hashicorp/terraform:{terraform_version}` image
  - Mount Cloudflare Tunnel Terraform module from `terraform/modules/cloudflare-tunnel`
  - Write cloudflare.json config to `/workspace/cloudflare.json`
  - Set required environment variables:
    - `TF_VAR_cloudflare_account_id`
    - `TF_VAR_zone_name`
    - `TF_VAR_config_file`
  - Set Cloudflare token as secret: `TF_VAR_cloudflare_token`
  - Set working directory to `/module`

- [x] **TASK-002:** Execute Cloudflare terraform destroy
  - Run `terraform init` in Cloudflare cleanup container
  - Run `terraform destroy -auto-approve` in Cloudflare cleanup container
  - Capture destroy output
  - Update cleanup_status["cloudflare"] to "success" on completion
  - Handle exceptions gracefully, setting status to "failed: {error}"

- [x] **TASK-003:** Create UniFi cleanup container
  - Create Terraform container from `hashicorp/terraform:{terraform_version}` image
  - Mount UniFi DNS Terraform module from `terraform/modules/unifi-dns`
  - Write unifi.json config to `/workspace/unifi.json`
  - Set required environment variables:
    - `TF_VAR_unifi_url`
    - `TF_VAR_api_url`
    - `TF_VAR_config_file`
  - Set UniFi authentication (API key OR username/password) as secrets
  - Set working directory to `/module`

- [x] **TASK-004:** Execute UniFi terraform destroy
  - Run `terraform init` in UniFi cleanup container
  - Run `terraform destroy -auto-approve` in UniFi cleanup container
  - Capture destroy output
  - Update cleanup_status["unifi"] to "success" on completion
  - Handle exceptions gracefully, setting status to "failed: {error}"

- [x] **TASK-005:** Update state file cleanup messaging
  - Document that Terraform state is container-local
  - Update cleanup_status["state_files"] to "success" with note about automatic cleanup

- [x] **TASK-006:** Add cleanup summary with warnings
  - Add cleanup summary section showing status of all cleanup operations
  - Display warning if any cleanup step failed
  - Include manual cleanup instructions in warning message

## Validation Tasks

- [ ] **TASK-007:** Verify Cloudflare cleanup flow
  - Test that Cloudflare tunnel is destroyed via API after cleanup
  - Test that Cloudflare DNS record is deleted after cleanup
  - Verify error handling when resources don't exist

- [ ] **TASK-008:** Verify UniFi cleanup flow
  - Test that UniFi DNS records are deleted after cleanup
  - Verify error handling when resources don't exist

- [ ] **TASK-009:** Verify cleanup error handling
  - Test that cleanup failures don't mask original test errors
  - Test that both Cloudflare and UniFi cleanup are attempted even if one fails
  - Verify graceful handling when resources are already deleted

## Documentation Tasks

- [ ] **TASK-010:** Update function docstring if needed
  - Verify docstring accurately describes real cleanup behavior

## Dependencies

- Blocks: None (this is the final prompt in the sequence)
- Blocked by: Prompts 01-04 (config generation, resource creation, validation)
- Related: `destroy()` function pattern (lines 431-623)
