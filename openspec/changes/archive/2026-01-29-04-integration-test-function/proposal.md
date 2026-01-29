# Proposal: Integration Test Function

## Summary

Implement an integration test function that creates ephemeral DNS resources with real Cloudflare and UniFi APIs, validates the setup works, and automatically cleans up. This provides confidence that the DNS configuration pipeline (KCL → Terraform → Real APIs) functions correctly.

## Motivation

All deployment functions are in place. We need a DNS sanity test to verify the complete pipeline works end-to-end with real APIs. This test creates temporary resources, validates them, and ensures cleanup regardless of test outcome.

## Scope

### In Scope
- Add `test_integration` function with guaranteed cleanup via Dagger's defer pattern
- Generate random hostnames/tunnel names to avoid conflicts
- Create temporary Cloudflare tunnel with random services
- Create temporary UniFi DNS records
- Verify connectivity/resolve hostnames
- **Cache buster parameter** to force Dagger cache invalidation
- **Wait before cleanup parameter** to pause between validation and destruction
- Report test results with details

### Out of Scope
- Long-running monitoring tests
- Load testing
- Modifying production resources (test-only)
- UniFi client/MAC address workflow testing (future enhancement)

## Acceptance Criteria

- [ ] `test_integration` function exists with all required parameters
- [ ] Function supports `cache_buster` parameter for cache invalidation
- [ ] Function supports `wait_before_cleanup` parameter for debugging
- [ ] Generates random test ID for resource naming
- [ ] Creates temporary KCL config with random hostnames
- [ ] Runs Terraform apply for both modules using local state only
- [ ] Validates resources created successfully
- [ ] Guarantees cleanup via Dagger defer pattern
- [ ] Returns comprehensive test report as `str`

## Dependencies

- Requires change 01 (Dagger module scaffolding)
- Requires change 02 (KCL generation functions)
- Requires change 03 (Terraform deployment functions)

## Files to Modify

- `src/unifi_cloudflare_glue/main.py` - add test_integration function
