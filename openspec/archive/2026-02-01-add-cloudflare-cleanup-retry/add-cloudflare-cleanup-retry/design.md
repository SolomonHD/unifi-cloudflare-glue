# Design: Cloudflare Cleanup Retry Logic

## Context

The Cloudflare Terraform provider (issue #5255) has a race condition where tunnel deletion fails on the first attempt if there are "active connections". This is a known behavior that typically resolves on a second attempt after a brief delay.

## Goals

1. Implement automatic retry for Cloudflare tunnel deletion (2 attempts)
2. Provide clear feedback when retry succeeds
3. Provide actionable manual cleanup instructions when retry fails
4. Maintain backward compatibility with existing behavior
5. Do not affect UniFi cleanup (no retry needed there)

## Non-Goals

1. Implementing Cloudflare API direct deletion workaround
2. Adding retry logic for other operations (init, apply)
3. Modifying UniFi cleanup behavior
4. Implementing exponential backoff (fixed 5-second delay is sufficient)

## Decisions

### Decision: Fixed Delay vs Exponential Backoff

**Chosen**: Fixed 5-second delay between attempts

**Rationale**:
- The Cloudflare provider issue is related to connection state propagation, not rate limiting
- A 5-second delay is sufficient for connection state to clear (per GitHub issue reports)
- Simpler implementation, easier to reason about
- Two attempts with 5-second delay fits within acceptable test cleanup time

**Alternatives considered**:
- Exponential backoff (1s, 2s, 4s): Overkill for this specific issue
- Longer single delay (10s): Wastes time when first attempt would succeed

### Decision: Retry Scope

**Chosen**: Retry only Cloudflare destroy, not UniFi

**Rationale**:
- The known bug is specific to Cloudflare tunnel resources
- UniFi cleanup doesn't have the same issue
- Limiting scope reduces risk and complexity

### Decision: Status Tracking Granularity

**Chosen**: Three distinct statuses: `success`, `success_after_retry`, `failed_needs_manual_cleanup`

**Rationale**:
- `success` vs `success_after_retry` helps identify if the workaround is being triggered frequently
- `failed_needs_manual_cleanup` is actionable and clearly indicates user intervention needed
- Distinct from existing `failed: {error}` format for immediate failures

### Decision: Error Message Preservation

**Chosen**: Include original error in final report even after retry

**Rationale**:
- Debuggability: Original error helps identify if it's the known issue or something new
- Transparency: Users should know what happened on each attempt
- Format: First error logged at retry time, final error included in cleanup summary

## Implementation Pattern

```python
# Pseudo-code for retry logic
cleanup_status["cloudflare"] = "pending"
last_error = None

for attempt in range(1, 3):  # 2 attempts
    try:
        await cf_cleanup_ctr.with_exec(["terraform", "destroy", "-auto-approve"])
        if attempt == 1:
            cleanup_status["cloudflare"] = "success"
            report_lines.append("✓ Destroyed tunnel (first attempt)")
        else:
            cleanup_status["cloudflare"] = "success_after_retry"
            report_lines.append("✓ Destroy succeeded on retry")
        break  # Success, exit retry loop
    except dagger.ExecError as e:
        last_error = str(e)
        if attempt == 1:
            report_lines.append("First destroy attempt failed, retrying in 5 seconds...")
            await asyncio.sleep(5)
        else:
            # Second attempt failed - provide manual cleanup instructions
            cleanup_status["cloudflare"] = "failed_needs_manual_cleanup"
            report_lines.append("✗ Cloudflare cleanup failed after 2 attempts")
            report_lines.append("")
            report_lines.append("The following resources may need manual deletion via Cloudflare Dashboard:")
            report_lines.append(f"  - Tunnel: {tunnel_name}")
            report_lines.append(f"  - DNS Record: {test_hostname}")
            report_lines.append("")
            report_lines.append("Manual cleanup steps:")
            report_lines.append("  1. Visit https://dash.cloudflare.com/ > Zero Trust > Networks > Tunnels")
            report_lines.append(f"  2. Find and delete tunnel: {tunnel_name}")
            report_lines.append(f"  3. Visit DNS > Records for zone {cloudflare_zone}")
            report_lines.append(f"  4. Delete CNAME record: {test_hostname}")
```

## Error Handling Strategy

1. **First attempt fails**: Log failure, wait 5 seconds, retry
2. **Second attempt succeeds**: Log success on retry, continue with UniFi cleanup
3. **Second attempt fails**: Log manual cleanup instructions, mark status, continue with UniFi cleanup
4. **Container/init errors**: Fail fast (no retry for infrastructure issues)

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Retry masks other issues | Preserve original error in logs; status shows retry was needed |
| Adds 5 seconds to test time | Only adds delay when first attempt fails (edge case) |
| Complexity in cleanup code | Well-commented, follows clear retry pattern |
| UniFi cleanup affected | Explicitly scope retry to Cloudflare block only |

## Migration Plan

No migration needed - this is an additive change to existing behavior:
- Existing successful cleanups: No behavior change
- Existing failing cleanups: Now retry once before failing
- No API changes to function signatures
