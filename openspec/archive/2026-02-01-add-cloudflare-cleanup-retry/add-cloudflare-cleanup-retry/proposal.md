# Change: Add Cloudflare Cleanup Retry Logic

## Why

The Cloudflare Terraform provider has a known bug (issue #5255) where deleting `cloudflare_zero_trust_tunnel_cloudflared` resources fails on the first attempt with an "active connections" error. The destroy operation typically succeeds on the second attempt, but if it fails again, the tunnel remains orphaned in Cloudflare and must be manually deleted via the Cloudflare dashboard UI.

The `test_integration` function currently runs `terraform destroy` once during Cloudflare cleanup. If this fails, the test reports an error but doesn't provide the user with the specific tunnel names and instructions for manual cleanup, leading to confusion and resource leaks.

## What Changes

- **Retry Logic**: Add 2-attempt retry logic for Cloudflare `terraform destroy` in the cleanup phase
  - First destroy attempt executes normally
  - If first attempt fails, wait 5 seconds and retry
  - If second attempt succeeds, mark as "success_after_retry"
  - If second attempt fails, provide detailed manual cleanup instructions

- **Enhanced Status Tracking**: Update cleanup status reporting to distinguish between:
  - `success` - Destroy succeeded on first attempt
  - `success_after_retry` - Destroy succeeded on second attempt
  - `failed_needs_manual_cleanup` - Destroy failed after both attempts

- **User-Friendly Error Messages**: When cleanup fails after 2 attempts, display:
  - Exact tunnel name that failed to delete
  - Exact DNS record name that may need cleanup
  - Step-by-step instructions for manual deletion via Cloudflare dashboard

- **Logging Improvements**: Add explicit log messages for retry attempts and outcomes

## Impact

- **Affected specs**: 
  - `cleanup` - Cloudflare destroy execution scenarios
  - `test-integration` - Cleanup status tracking and reporting

- **Affected code**: 
  - `src/main/main.py` - `test_integration` function, Cloudflare cleanup section (lines ~1284-1334)

- **Backward Compatibility**: Existing behavior maintained when no retry is needed; no breaking changes to function signatures

## References

- Known provider issue: https://github.com/cloudflare/terraform-provider-cloudflare/issues/5255
- Target function: `test_integration` cleanup phase
