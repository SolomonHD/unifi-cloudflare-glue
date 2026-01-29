# Tasks: Integration Test Function

## Implementation Tasks

- [ ] Add `test_integration` function signature with all parameters:
  - [ ] Required: `source`, `cloudflare_zone`, `cloudflare_token`, `cloudflare_account_id`, `unifi_url`, `api_url`
  - [ ] Auth (mutually exclusive): `unifi_api_key` OR (`unifi_username` AND `unifi_password`)
  - [ ] Cache/Wait flags: `cache_buster: str = ""`, `wait_before_cleanup: int = 0`
  - [ ] Optional: `cleanup: bool = True`, `validate_connectivity: bool = False`, `test_timeout: str = "5m"`

- [ ] Implement random test ID generation (e.g., `test-a7x9k`)

- [ ] Implement Phase 1 - Setup:
  - [ ] Generate random test ID
  - [ ] Create temporary KCL config with random hostnames
  - [ ] Prepare working directory

- [ ] Implement Phase 2 - Generation:
  - [ ] Generate unifi.json from KCL
  - [ ] Generate cloudflare.json from KCL
  - [ ] Validate output files exist

- [ ] Implement Phase 3 - Deployment:
  - [ ] Deploy UniFi DNS first (local state only)
  - [ ] Deploy Cloudflare Tunnel second (local state only)
  - [ ] Handle deployment failures

- [ ] Implement Phase 4 - Validation:
  - [ ] Verify Cloudflare tunnel exists
  - [ ] Verify Cloudflare DNS records
  - [ ] Verify UniFi DNS records
  - [ ] Optional HTTP connectivity check

- [ ] Implement Phase 5 - Cleanup (guaranteed via defer):
  - [ ] Destroy Cloudflare resources first
  - [ ] Destroy UniFi resources second
  - [ ] Remove local state files
  - [ ] Runs even if prior phases fail

- [ ] Implement cache buster integration:
  - [ ] Add `cache_buster` parameter to function signature
  - [ ] Inject `CACHE_BUSTER` environment variable when non-empty
  - [ ] Include cache buster in test report

- [ ] Implement wait before cleanup:
  - [ ] Add `wait_before_cleanup` parameter to function signature
  - [ ] Use `asyncio.sleep()` for async-compatible wait
  - [ ] Include wait duration and status in test report

- [ ] Implement test report generation:
  - [ ] Include test ID
  - [ ] Include phase durations
  - [ ] Include created resources list
  - [ ] Include validation results
  - [ ] Include cleanup status
  - [ ] Support both success and failure formats

- [ ] Implement authentication validation:
  - [ ] Validate either API key OR username/password provided
  - [ ] Return clear error if neither or both provided

- [ ] Implement error handling:
  - [ ] Handle failures at each phase
  - [ ] Ensure cleanup runs via defer
  - [ ] Include error details in report

- [ ] Security implementation:
  - [ ] Use `dagger.Secret` for all credentials
  - [ ] Ensure secrets don't appear in logs or output
  - [ ] Use environment variables for secret injection

## Validation Tasks

- [ ] Run `openspec validate 04-integration-test-function --strict`
- [ ] Verify all requirements have scenarios
- [ ] Verify cache buster requirements are covered
- [ ] Verify wait before cleanup requirements are covered

## Documentation Tasks

- [ ] Update function docstring with comprehensive documentation
- [ ] Include example usage in docstring:
  ```bash
  # Run with API key
  dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443

  # Run with cache buster to force fresh execution
  dagger call test-integration ... --cache-buster=$(date +%s)

  # Run with wait for debugging
  dagger call test-integration ... --wait-before-cleanup=300
  ```
