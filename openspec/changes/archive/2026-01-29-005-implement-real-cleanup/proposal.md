# Proposal: Implement Real Resource Cleanup

## Change ID
005-implement-real-cleanup

## Context

Currently, Phase 5 (the `finally` block, lines 1206-1251) of the `test_integration` function only prints simulated cleanup messages without actually destroying resources. The cleanup phase shows success messages like:
- "✓ Destroyed tunnel: {tunnel_name}"
- "✓ Deleted DNS record: {test_hostname}"
- "✓ Deleted UniFi DNS record: {test_id}.local"

However, these are just print statements - no actual `terraform destroy` commands are executed. This means:
1. Test resources persist in Cloudflare and UniFi after tests complete
2. Manual cleanup is required to avoid resource leaks
3. The test report inaccurately claims cleanup was successful

## Goal

Implement real cleanup by executing `terraform destroy` to remove the Cloudflare tunnels, DNS records, and UniFi DNS records created during the test.

## Scope

**In scope:**
- Replace simulated cleanup (lines 1206-1251) with real Terraform destroy execution
- Create separate Terraform containers for Cloudflare and UniFi cleanup
- Mount the appropriate Terraform modules (`terraform/modules/cloudflare-tunnel` and `terraform/modules/unifi-dns`)
- Write the config JSON files to containers (needed for destroy to work)
- Set required environment variables and secrets
- Run `terraform init` and `terraform destroy -auto-approve`
- Handle cleanup errors gracefully (don't fail if resources already gone)
- Update cleanup status in the final report

**Out of scope:**
- Resource creation (handled in previous prompts)
- Validation logic (already implemented)
- Modifying the overall test flow or error handling
- Changes to the `destroy()` standalone function (already implemented correctly)

## Dependencies

- Prompt 01-04 implementations (test config generation, Cloudflare creation, UniFi creation, validation)
- Existing `destroy()` function (lines 431-623) as reference implementation
- Terraform modules at `terraform/modules/cloudflare-tunnel/` and `terraform/modules/unifi-dns/`

## Target

- **File:** `src/main/main.py`
- **Function:** `test_integration`
- **Lines:** 1206-1251 (the `finally` block's cleanup phase)

## Success Criteria

1. Phase 5 creates separate Terraform containers for Cloudflare and UniFi cleanup
2. Both Terraform modules are mounted in their respective containers
3. Config JSON files are written to both containers
4. All required environment variables and secrets are set in both containers
5. `terraform init` is run in both containers before destroy
6. `terraform destroy -auto-approve` is executed for Cloudflare resources
7. `terraform destroy -auto-approve` is executed for UniFi resources
8. Cleanup errors are caught and logged without raising
9. Cleanup status is accurately reported in the summary
10. Warning is displayed if any cleanup step fails
11. State file cleanup notes that state is container-local

## Reference Implementation

The existing `destroy()` function (lines 431-623) provides the correct pattern:
- Creates Terraform containers with proper module mounting
- Sets environment variables and secrets
- Runs `terraform init` followed by `terraform destroy -auto-approve`
- Handles errors gracefully
- Reports success/failure status

The cleanup implementation in `test_integration` should follow this same pattern.
