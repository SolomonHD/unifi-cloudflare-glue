# OpenSpec Change Prompt

## Context
The `test_integration` function in `src/main/main.py` creates ephemeral Cloudflare and UniFi resources for testing. However, the Terraform state (`terraform.tfstate`) is lost between the create and destroy phases because each phase runs in a new ephemeral Dagger container. When cleanup runs `terraform destroy`, it has no state file, so it doesn't know what resources to delete. This causes resources to be orphaned in Cloudflare and UniFi.

## Goal
Persist Terraform state between the create and destroy phases of the integration test by:
1. Exporting state files after successful `terraform apply` operations
2. Passing state files to the cleanup containers before `terraform destroy`
3. Ensuring reliable cleanup of all test resources

## Scope

**In scope:**
- Modify Phase 2 (Cloudflare create) to export `terraform.tfstate` after apply
- Modify Phase 3 (UniFi create) to export `terraform.tfstate` after apply  
- Modify Phase 5 (Cloudflare cleanup) to import state before destroy
- Modify Phase 5 (UniFi cleanup) to import state before destroy
- Add error handling for state export/import operations
- Update test report to show state persistence status

**Out of scope:**
- Changes to the actual Terraform modules
- Changes to resource creation logic
- Remote state backend configuration

## Desired Behavior

### State Export (After Create)
- After successful Cloudflare `terraform apply`, export `/module/terraform.tfstate` 
- After successful UniFi `terraform apply`, export `/module/terraform.tfstate`
- Store state as strings in memory (passed between phases)

### State Import (Before Destroy)
- Before Cloudflare `terraform destroy`, write state file to `/module/terraform.tfstate`
- Before UniFi `terraform destroy`, write state file to `/module/terraform.tfstate`
- Run `terraform init` (required to initialize providers before destroy with state)
- Then run `terraform destroy -auto-approve`

### Error Handling
- If state export fails, log warning but continue (cleanup will use config-based destroy)
- If state import fails, fall back to config-based destroy with warning
- Include state persistence status in cleanup summary

## Constraints & Assumptions

- Use Dagger's `container.file(path).contents()` to read state files
- Use `container.with_new_file(path, contents)` to write state files
- State files may contain sensitive data (IPs, tokens) - handled securely by Dagger
- Backward compatibility: If state file doesn't exist, destroy should still work
- Test report should indicate whether state-based or config-based destroy was used

## Acceptance Criteria

- [ ] Cloudflare state is exported after Phase 2 apply and stored in memory
- [ ] UniFi state is exported after Phase 3 apply and stored in memory
- [ ] Cloudflare cleanup imports state before running terraform destroy
- [ ] UniFi cleanup imports state before running terraform destroy
- [ ] Test report shows state persistence status (e.g., "State-based cleanup: enabled")
- [ ] Resources are actually deleted from Cloudflare dashboard after test
- [ ] Resources are actually deleted from UniFi controller after test
- [ ] If state operations fail, graceful fallback with warning messages
- [ ] CHANGELOG.md updated with bug fix description
