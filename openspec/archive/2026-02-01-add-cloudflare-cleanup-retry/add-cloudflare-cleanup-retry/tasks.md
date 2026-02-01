# Implementation Tasks: Cloudflare Cleanup Retry Logic

## 1. Implement Retry Logic in Cloudflare Cleanup

- [x] 1.1 Locate Cloudflare cleanup section in `src/main/main.py` (~lines 1284-1334)
- [x] 1.2 Wrap terraform destroy in a retry loop (maximum 2 attempts)
- [x] 1.3 Add 5-second delay between attempts using `await asyncio.sleep(5)`
- [x] 1.4 Add logging for retry attempts: "First destroy attempt failed, retrying in 5 seconds..."
- [x] 1.5 Verify retry logic does not affect UniFi cleanup section

## 2. Update Cleanup Status Tracking

- [x] 2.1 Support status "success" for first-attempt success (existing behavior)
- [x] 2.2 Support status "success_after_retry" for second-attempt success
- [x] 2.3 Support status "failed_needs_manual_cleanup" for failure after 2 attempts
- [x] 2.4 Ensure backward compatibility with existing status reporting

## 3. Implement User-Friendly Error Messages

- [x] 3.1 Display "✓ Destroy succeeded on retry" when second attempt succeeds
- [x] 3.2 Display "✗ Cloudflare cleanup failed after 2 attempts" when both attempts fail
- [x] 3.3 Display tunnel name in failure message: `tunnel_name`
- [x] 3.4 Display DNS record name in failure message: `test_hostname`
- [x] 3.5 Display manual cleanup instructions with dashboard navigation steps
- [x] 3.6 Include Cloudflare zone name in manual cleanup instructions

## 4. Error Handling and Edge Cases

- [x] 4.1 Preserve original error message for debugging
- [x] 4.2 Ensure cleanup continues to UniFi even if Cloudflare fails
- [x] 4.3 Handle container/init errors (fail fast, no retry for infrastructure issues)
- [x] 4.4 Test that retry only triggers on destroy failure, not init failure

## 5. Validation and Testing

- [x] 5.1 Run `openspec validate add-cloudflare-cleanup-retry --strict`
- [x] 5.2 Verify syntax correctness: `cd unifi-cloudflare-glue && dagger functions`
- [x] 5.3 Review code changes match design.md pseudo-code
- [x] 5.4 Verify no changes to UniFi cleanup logic

## 6. Documentation Updates

- [x] 6.1 Update CHANGELOG.md with new retry behavior
- [x] 6.2 Document the known Cloudflare provider issue in code comments
- [x] 6.3 Add reference to GitHub issue #5255 in comments

## Acceptance Criteria Verification

- [x] Cloudflare `terraform destroy` implements retry logic with 5-second delay between attempts
- [x] First failure is logged but doesn't immediately report cleanup failure
- [x] Second successful attempt reports "destroy succeeded on retry" in the test report
- [x] Second failed attempt provides detailed manual cleanup instructions
- [x] Cleanup status tracking differentiates between: "success", "success_after_retry", "failed_needs_manual_cleanup"
- [x] Test report output includes the manual cleanup instructions when applicable
- [x] Retry logic does not affect UniFi cleanup phase
- [x] Error handling preserves the original error message for debugging
