# Change: Preserve Terraform State for Test Cleanup

## Why

The `test_integration()` function in `src/main/main.py` creates Cloudflare and UniFi resources during the test phase, then attempts to clean them up in the `finally` block. However, the cleanup creates NEW containers for the destroy operation. Since each Dagger container has its own ephemeral filesystem, the Terraform state file from the `apply` phase is not available during `destroy`. Without state, Terraform doesn't know what resources to delete, causing the cleanup to fail silently and leaving orphaned resources in Cloudflare and UniFi.

## What Changes

- Export Terraform state files after successful Cloudflare `terraform apply` (lines ~1114-1117)
- Export Terraform state files after successful UniFi `terraform apply` (lines ~1180-1183)
- Mount saved state files during Cloudflare cleanup destroy operation (lines ~1358-1368)
- Mount saved state files during UniFi cleanup destroy operation (lines ~1444-1453)
- Store state files in Dagger Directory objects that persist through function execution
- Handle state file export failures gracefully (don't fail the test if state export fails)

## Impact

- Affected specs:
  - `cleanup`: Modified to require state file mounting during destroy operations
  - `integration-testing`: Modified to require state preservation between apply and destroy phases
- Affected code:
  - `src/main/main.py`: `test_integration()` method state handling
- Breaking changes: None (internal implementation detail)

## References

- Prompt: `openspec/prompts/02-preserve-terraform-state.md`
- Related change: `fix-test-config-domain` (01)
