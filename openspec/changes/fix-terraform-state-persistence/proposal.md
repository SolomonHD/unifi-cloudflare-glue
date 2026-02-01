# Change: Fix Terraform State Persistence in Integration Tests

## Why

The `test_integration` function creates ephemeral Cloudflare and UniFi resources for testing. However, the Terraform state (`terraform.tfstate`) is lost between the create and destroy phases because each phase runs in a new ephemeral Dagger container. When cleanup runs `terraform destroy`, it has no state file, so it doesn't know what resources to delete. This causes resources to be orphaned in Cloudflare and UniFi.

This is a critical bug that leads to:
- Orphaned Cloudflare tunnels and DNS records
- Orphaned UniFi DNS records  
- Manual cleanup required after each test run
- Accumulation of test resources in cloud accounts

## What Changes

- **Cloudflare State Export**: After successful Cloudflare `terraform apply`, export `/module/terraform.tfstate` and store in memory
- **UniFi State Export**: After successful UniFi `terraform apply`, export `/module/terraform.tfstate` and store in memory
- **Cloudflare State Import**: Before Cloudflare `terraform destroy`, write state file to `/module/terraform.tfstate` and run `terraform init`
- **UniFi State Import**: Before UniFi `terraform destroy`, write state file to `/module/terraform.tfstate` and run `terraform init`
- **Error Handling**: Add graceful fallback to config-based destroy if state operations fail
- **Test Report Updates**: Include state persistence status in cleanup summary (e.g., "State-based cleanup: enabled")
- **CHANGELOG.md**: Update with bug fix description

## Impact

- **Affected specs**: `test-integration`, `cleanup`
- **Affected code**: `src/main/main.py` (test_integration function, lines 832-1500)
- **Breaking changes**: None - fully backward compatible
- **Performance**: Minimal - state files are small JSON files passed as strings

## References

- Related spec: `openspec/specs/test-integration/spec.md`
- Related spec: `openspec/specs/cleanup/spec.md`
- Source code: `src/main/main.py:832-1500`
