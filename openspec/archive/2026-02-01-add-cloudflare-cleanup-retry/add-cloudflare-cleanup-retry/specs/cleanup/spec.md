# Cleanup Specification Delta

## MODIFIED Requirements

### Requirement: Cloudflare terraform destroy execution

The Cloudflare cleanup phase SHALL implement retry logic for tunnel deletion to handle the known provider bug (issue #5255).

#### Scenario: Successful destroy on first attempt
Given: The Cloudflare cleanup container is configured
When: Terraform init is executed
And: Terraform destroy -auto-approve is executed on the first attempt
Then: The Cloudflare tunnel is destroyed
And: The Cloudflare DNS record is deleted
And: cleanup_status["cloudflare"] is set to "success"
And: The report includes "✓ Destroyed tunnel: {tunnel_name}"
And: The report includes "✓ Deleted DNS record: {test_hostname}"

#### Scenario: Successful destroy on retry
Given: The Cloudflare cleanup container is configured
And: The first destroy attempt fails with an "active connections" error
When: The system waits 5 seconds
And: Terraform destroy -auto-approve is executed on the second attempt
And: The second attempt succeeds
Then: The Cloudflare tunnel is destroyed
And: The Cloudflare DNS record is deleted
And: cleanup_status["cloudflare"] is set to "success_after_retry"
And: The report includes "First destroy attempt failed, retrying in 5 seconds..."
And: The report includes "✓ Destroy succeeded on retry"

#### Scenario: Failed destroy after retry
Given: The Cloudflare cleanup container is configured
And: The first destroy attempt fails
And: The second destroy attempt also fails
When: Both destroy attempts have been executed with a 5-second delay between them
Then: cleanup_status["cloudflare"] is set to "failed_needs_manual_cleanup"
And: The report includes "✗ Cloudflare cleanup failed after 2 attempts"
And: The report includes "The following resources may need manual deletion via Cloudflare Dashboard:"
And: The report includes "  - Tunnel: {tunnel_name}"
And: The report includes "  - DNS Record: {test_hostname}"
And: The report includes manual cleanup steps:
  - "1. Visit https://dash.cloudflare.com/ > Zero Trust > Networks > Tunnels"
  - "2. Find and delete tunnel: {tunnel_name}"
  - "3. Visit DNS > Records for zone {cloudflare_zone}"
  - "4. Delete CNAME record: {test_hostname}"

---

## ADDED Requirements

### Requirement: Cloudflare Destroy Retry Logic

The cleanup phase SHALL implement a retry mechanism for Cloudflare terraform destroy operations.

#### Scenario: Retry mechanism implementation
Given: The test_integration function is in the Cloudflare cleanup phase
When: Implementing the destroy logic
Then: The implementation SHALL use a loop with maximum 2 attempts
And: The implementation SHALL use asyncio.sleep(5) for the delay between attempts
And: The delay SHALL only occur if the first attempt fails
And: The retry logic SHALL be scoped to Cloudflare cleanup only
And: UniFi cleanup SHALL NOT be affected by the retry logic

#### Scenario: Retry delay implementation
Given: The first destroy attempt fails
When: Preparing for the second attempt
Then: The system SHALL wait exactly 5 seconds using await asyncio.sleep(5)
And: The report SHALL include "First destroy attempt failed, retrying in 5 seconds..."
And: The delay SHALL be non-blocking (async-compatible)

### Requirement: Enhanced Cleanup Status Tracking

The cleanup phase SHALL support granular status tracking for Cloudflare cleanup.

#### Scenario: Status values for Cloudflare cleanup
Given: The Cloudflare cleanup is being executed
When: Tracking the cleanup status
Then: The system SHALL support the following status values:
  - "success" - Destroy succeeded on first attempt
  - "success_after_retry" - Destroy succeeded on second attempt
  - "failed_needs_manual_cleanup" - Destroy failed after 2 attempts
  - "failed: {error_message}" - Infrastructure/init errors (existing behavior)

#### Scenario: Backward compatible status reporting
Given: Cloudflare cleanup succeeds on first attempt
When: The cleanup summary is generated
Then: The status SHALL be "success" (unchanged from existing behavior)
And: The report format SHALL match existing behavior

### Requirement: Error Preservation During Retry

The cleanup phase SHALL preserve error information for debugging when retry is needed.

#### Scenario: Error logging on first failure
Given: The first destroy attempt fails
When: Preparing for retry
Then: The error message SHALL be preserved internally
And: The error SHALL be available for final report if second attempt also fails

#### Scenario: Error context in final report
Given: Both destroy attempts fail
When: Generating the manual cleanup instructions
Then: The report SHALL include the final error message context
And: The status SHALL be set to "failed_needs_manual_cleanup"
