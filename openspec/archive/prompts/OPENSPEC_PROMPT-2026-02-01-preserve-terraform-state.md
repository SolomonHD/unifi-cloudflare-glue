# OpenSpec Prompt: Preserve Terraform State for Test Cleanup

## Context

The `test_integration()` function in `src/main/main.py` creates Cloudflare and UniFi resources during the test phase, then attempts to clean them up in the `finally` block. However, the cleanup creates NEW containers for the destroy operation. Since each Dagger container has its own ephemeral filesystem, the Terraform state file from the `apply` phase is not available during `destroy`. Without state, Terraform doesn't know what resources to delete, causing the cleanup to fail silently.

## Goal

Preserve Terraform state files between the apply and destroy phases by exporting state after successful resource creation and mounting it during cleanup.

## Scope

### In Scope
- Export Terraform state files after successful Cloudflare `terraform apply`
- Export Terraform state files after successful UniFi `terraform apply`
- Mount saved state files during Cloudflare cleanup destroy operation
- Mount saved state files during UniFi cleanup destroy operation
- Handle state file export using Dagger's file export mechanisms

### Out of Scope
- Changes to the actual Terraform modules
- Changes to the Dagger container base images
- Remote state backend configuration

## Desired Behavior

1. After successful Cloudflare `terraform apply`, export `terraform.tfstate` from the container
2. After successful UniFi `terraform apply`, export `terraform.tfstate` from the container
3. During Cloudflare cleanup, mount the saved state file before running `terraform destroy`
4. During UniFi cleanup, mount the saved state file before running `terraform destroy`
5. State files should be stored in Dagger Directory objects that persist through the function execution

## Constraints & Assumptions

- State files are small enough to store in memory/Dagger directories
- The cleanup phase runs in the same function invocation as apply (same `test_integration` call)
- Both Cloudflare and UniFi modules use local state (terraform.tfstate file)
- State files need to be mounted at `/module/terraform.tfstate` in cleanup containers

## Acceptance Criteria

- [ ] Cloudflare state is exported after successful `terraform apply` (lines ~1103)
- [ ] UniFi state is exported after successful `terraform apply` (lines ~1170)
- [ ] Cloudflare cleanup mounts the saved state file before `terraform init`/`destroy`
- [ ] UniFi cleanup mounts the saved state file before `terraform init`/`destroy`
- [ ] State files are stored in Dagger Directory objects that persist to cleanup phase
- [ ] Cleanup uses existing retry logic (2 attempts with 5s delay for Cloudflare)
- [ ] State export failures are handled gracefully (don't fail the test if state export fails)
- [ ] Destroy operations properly delete resources when state is available

## Implementation Notes

### State Export Pattern
```python
# After successful apply, export state from the container
state_file = await cf_ctr.file("/module/terraform.tfstate")
state_dir = dagger.dag.directory().with_file("terraform.tfstate", state_file)
```

### State Mount Pattern
```python
# During cleanup, mount the saved state
cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", state_dir)
# Or mount just the state file
cf_cleanup_ctr = cf_cleanup_ctr.with_file("/module/terraform.tfstate", state_file)
```

## Files to Modify

- `src/main/main.py`: Update `test_integration()` method to preserve and restore state

## Dependencies

- Depends on: `01-fix-test-config-domain.md` (should be applied after or independently)
