# OpenSpec Change Prompt: Integration Test Function (DNS Sanity Test)

## Context

All deployment functions are in place. We need a DNS sanity test that creates ephemeral resources with real Cloudflare and UniFi APIs, validates the setup works, and automatically cleans up. This provides confidence that the DNS configuration pipeline (KCL → Terraform → Real APIs) functions correctly.

**Note:** This is a **DNS-only sanity test** that creates temporary DNS records. A more comprehensive integration test that includes UniFi client/MAC address workflows may be added in the future.

**Critical requirements**:
- Dagger at repo base for git functions
- All credentials as Dagger Secrets
- **Guaranteed cleanup** using Dagger's defer pattern (cleanup runs even if tests fail)
- Random resource names to avoid conflicts

## Goal

Implement an integration test function that creates temporary resources, validates them, and ensures cleanup regardless of test outcome.

## Scope

**In scope:**
- Add `test_integration` function
- Generate random hostnames/tunnel names (e.g., `test-a7x9k.example.com`)
- Create temporary Cloudflare tunnel with random services
- Create temporary UniFi DNS records
- Verify connectivity/resolve hostnames
- **Guaranteed cleanup** via Dagger's defer mechanism
- Report test results with details

**Out of scope:**
- Long-running monitoring tests
- Load testing
- Modifying production resources (test-only)

## Desired Behavior

1. **Test Setup**:
   - Generate random test ID (e.g., `test-a7x9k`)
   - Create KCL config with random hostnames
   - Generate JSON configs

2. **Resource Creation**:
   - Create Cloudflare tunnel (`tunnel-test-a7x9k`)
   - Create Cloudflare DNS records (random hostnames)
   - Create UniFi DNS records (random internal hostnames)
   - Use local state file (isolated from production)

3. **Validation**:
   - Verify tunnel created successfully
   - Verify DNS records resolve (or would resolve)
   - Verify UniFi records exist
   - Optional: HTTP connectivity check if tunnel points to test service

4. **Cleanup** (guaranteed):
   - Destroy Cloudflare resources first
   - Destroy UniFi resources second
   - Remove local state files
   - Runs even if earlier steps fail

5. **Reporting**:
   - Return detailed test report
   - Include: created resources, validation results, cleanup status
   - Clear success/failure indication

## Constraints & Assumptions

- **All credentials as Secrets** (same as deployment functions):
  - `cloudflare_token: dagger.Secret`
  - `unifi_api_key: dagger.Secret` (or user/pass)
- Real Cloudflare zone required (user provides)
- Real UniFi controller access required
- Random hostnames prevent collisions
- **Integration test uses local Terraform state only** (isolated from production backends)
  - Production deployments support both local and remote state
  - Tests intentionally use local state to avoid polluting shared state
- Cleanup must run via Dagger's `defer` or similar pattern

## Required Parameters

### Required
- `source: dagger.Directory` - project source
- `cloudflare_zone: str` - DNS zone for test records
- `cloudflare_token: dagger.Secret` - Cloudflare API token
- `cloudflare_account_id: str` - Cloudflare account ID
- `unifi_url: str` - UniFi controller URL
- `api_url: str` - UniFi API URL (often same as unifi_url but may differ)

### UniFi Auth (mutually exclusive, pick one)
**Option 1: API Key**
- `unifi_api_key: dagger.Secret` - UniFi API key

**Option 2: Username/Password**
- `unifi_username: dagger.Secret` - UniFi username
- `unifi_password: dagger.Secret` - UniFi password

### Optional
- `cleanup: bool = True` - whether to cleanup (default true, false for debugging)
- `validate_connectivity: bool = False` - whether to test actual HTTP connectivity
- `test_timeout: str = "5m"` - timeout for test operations

## Acceptance Criteria

- [ ] `test_integration` function exists:
  - All credentials use `dagger.Secret` type
  - UniFi auth validation: either `unifi_api_key` OR (`unifi_username` AND `unifi_password`)
  - Generates random test ID for resource naming
  - Creates temporary KCL config with random hostnames
  - Generates JSON configs
  - Runs Terraform apply for both modules using **local state only** (isolated from production)
  - Validates resources created successfully
  - **Guarantees cleanup** via Dagger defer pattern
  - Returns comprehensive test report as `str`

- [ ] Test report includes:
  - Test ID used for resources
  - List of created hostnames/tunnels
  - Validation results (pass/fail for each check)
  - Cleanup status (success/failure)
  - Duration of each phase

- [ ] Cleanup behavior:
  - Always runs (success or failure)
  - Destroys Cloudflare before UniFi (reverse order)
  - Removes local state files
  - Reports any cleanup failures

- [ ] Error handling:
  - If setup fails, still attempt cleanup
  - If validation fails, still attempt cleanup
  - Report exactly which step failed
  - Include error messages in output

- [ ] Example usage works:
  ```bash
  # Run full integration test with API key
  dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443

  # Run with username/password instead
  dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-username=env:UNIFI_USER \
    --unifi-password=env:UNIFI_PASS \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443

  # Run without cleanup (for debugging)
  dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --cleanup=false
  ```

## Files to Modify

**Modify:**
- `src/unifi_cloudflare_glue/main.py` - add test_integration function

## Dependencies

- Requires change 01 (Dagger module scaffolding)
- Requires change 02 (KCL generation functions)
- Requires change 03 (Terraform deployment functions)

## Implementation Notes

### Random ID Generation
```python
import random
import string

def generate_test_id() -> str:
    """Generate random test identifier."""
    return "test-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
```

### Dagger Defer Pattern
Use Dagger's defer mechanism to ensure cleanup runs:

```python
@function
async def test_integration(self, ...):
    """Integration test with guaranteed cleanup."""
    test_id = generate_test_id()
    
    try:
        # Setup and validation
        ...
    finally:
        # This always runs
        if cleanup:
            await self._cleanup_resources(test_id, ...)
```

### Test Phases
1. **Generate**: Create KCL with random hostnames
2. **Apply**: Terraform apply for both modules
3. **Validate**: Check resources exist
4. **Cleanup**: Destroy resources (guaranteed)

## Security Considerations

- **Never log secret values** (tokens, API keys)
- Random hostnames prevent DNS collisions
- Local state files prevent affecting production backends
- Cleanup prevents resource sprawl and costs

## Reference

- Dagger defer pattern: https://docs.dagger.io/
- Terraform local backend: https://developer.hashicorp.com/terraform/language/settings/backends/local
- Cloudflare tunnel docs: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/

## Open Questions

None - this follows standard Dagger integration testing patterns.

## Future Enhancements

A more comprehensive integration test may be added later that:
- Accepts a UniFi client MAC address as input
- Queries the UniFi controller for existing client information
- Creates DNS records based on actual client data
- Tests the full workflow including client discovery → DNS registration

This would test the complete end-to-end workflow rather than just DNS configuration.
