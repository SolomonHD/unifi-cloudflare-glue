# OpenSpec Change Prompt

## Context

The Cloudflare Terraform provider has a known bug (issue #5255) where deleting `cloudflare_zero_trust_tunnel_cloudflared` resources fails on the first attempt with an "active connections" error. The destroy operation typically succeeds on the second attempt, but if it fails again, the tunnel remains orphaned in Cloudflare and must be manually deleted via the Cloudflare dashboard UI.

The `test_integration` function in `src/main/main.py` currently runs `terraform destroy` once during Cloudflare cleanup. If this fails, the test reports an error but doesn't provide the user with the specific tunnel names and instructions for manual cleanup.

## Goal

Implement retry logic for Cloudflare tunnel deletion during test cleanup, with clear user notification containing tunnel names and manual cleanup instructions if the deletion ultimately fails.

## Scope

**In scope:**
- Add retry logic (2 attempts) for Cloudflare `terraform destroy` in the cleanup phase
- Add 5-second delay between retry attempts
- Capture and analyze destroy failure reasons
- If destroy fails after 2 attempts, provide user-friendly message with:
  - Tunnel name(s) that failed to delete
  - DNS record name(s) that may need cleanup
  - Step-by-step instructions for manual deletion via Cloudflare dashboard
- Update cleanup status reporting to distinguish between: "success", "success_after_retry", "failed_needs_manual_cleanup"

**Out of scope:**
- Changing the resource creation logic
- Modifying UniFi cleanup behavior
- Implementing the Cloudflare API direct deletion workaround
- Adding retry logic for other operations (init, apply)

## Desired Behavior

### Retry Logic

1. First destroy attempt executes normally
2. If first attempt fails:
   - Wait 5 seconds (`asyncio.sleep(5)`)
   - Log: "First destroy attempt failed, retrying in 5 seconds..."
   - Execute second destroy attempt
3. If second attempt succeeds:
   - Log: "✓ Destroy succeeded on retry"
   - Mark cleanup as "success_after_retry"
4. If second attempt fails:
   - Capture the tunnel name (`tunnel_name`) and DNS record name (`test_hostname`)
   - Display detailed manual cleanup instructions in the test report
   - Mark cleanup status as "failed_needs_manual_cleanup"

### User Notification on Failure

When cleanup fails after 2 attempts, the test report must display:

```
✗ Cloudflare cleanup failed after 2 attempts

The following resources may need manual deletion via Cloudflare Dashboard:
  - Tunnel: {tunnel_name}
  - DNS Record: {test_hostname}

Manual cleanup steps:
  1. Visit https://dash.cloudflare.com/ > Zero Trust > Networks > Tunnels
  2. Find and delete tunnel: {tunnel_name}
  3. Visit DNS > Records for zone {cloudflare_zone}
  4. Delete CNAME record: {test_hostname}
```

### Code Location

The retry logic should be implemented in the Cloudflare cleanup section (approximately lines 1284-1334 in `src/main/main.py`), specifically around:

```python
# Execute terraform destroy
try:
    destroy_result = await cf_cleanup_ctr.with_exec([
        "terraform", "destroy", "-auto-approve"
    ]).stdout()
    report_lines.append(f"    ✓ Destroyed tunnel: {tunnel_name}")
    cleanup_status["cloudflare"] = "success"
except dagger.ExecError as e:
    raise RuntimeError(f"Terraform destroy failed: {str(e)}")
```

## Constraints & Assumptions

- The retry logic should only apply to Cloudflare cleanup, not UniFi cleanup
- The tunnel name and DNS hostname are available from test context variables (`test_id`, `cloudflare_zone`, `tunnel_name`, `test_hostname`)
- The 5-second delay is a heuristic based on the GitHub issue report
- The failure detection should check for the specific "active connections" error code (1022) but retry on any destroy failure
- The retry should use `asyncio.sleep()` for the delay
- Backward compatibility: existing behavior should be maintained when no retry is needed

## Acceptance Criteria

- [ ] Cloudflare `terraform destroy` implements retry logic with 5-second delay between attempts
- [ ] First failure is logged but doesn't immediately report cleanup failure
- [ ] Second successful attempt reports "destroy succeeded on retry" in the test report
- [ ] Second failed attempt provides detailed manual cleanup instructions including:
  - [ ] Exact tunnel name to delete (`tunnel_name`)
  - [ ] Exact DNS record name to delete (`test_hostname`)
  - [ ] Cloudflare zone name (`cloudflare_zone`)
  - [ ] Step-by-step Cloudflare dashboard navigation instructions
- [ ] Cleanup status tracking differentiates between: "success", "success_after_retry", "failed_needs_manual_cleanup"
- [ ] Test report output includes the manual cleanup instructions when applicable
- [ ] Retry logic does not affect UniFi cleanup phase
- [ ] Error handling preserves the original error message for debugging

## Reference

- Target function: `test_integration` cleanup phase at approximately line 1284-1334 in `src/main/main.py`
- Known provider issue: https://github.com/cloudflare/terraform-provider-cloudflare/issues/5255
- Related variables in test context:
  - `tunnel_name` = f"tunnel-{test_id}"
  - `test_hostname` = f"{test_id}.{cloudflare_zone}"
  - `cloudflare_zone` = user-provided zone parameter
- Python async sleep: `await asyncio.sleep(5)`
