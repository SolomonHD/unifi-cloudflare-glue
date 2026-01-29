# Proposal: Implement Real Resource Validation in Integration Tests

## Change ID
`04-implement-real-validation`

## Summary

Replace the simulated resource validation in Phase 4 of the `test_integration` function with actual API calls to Cloudflare and UniFi. This change enables the integration test to verify that resources were actually created by querying the respective APIs.

## Motivation

Currently, Phase 4 of `test_integration` (lines 1083-1105) only sets boolean flags to `True` without actually verifying that resources exist. This provides false confidence in the test results. By implementing real API validation, the integration test will:

1. Verify Cloudflare tunnels actually exist by querying the Cloudflare API
2. Verify Cloudflare DNS records exist by querying zone DNS records
3. Provide accurate validation status based on actual API responses
4. Detect cases where Terraform reported success but resources don't exist
5. Handle API errors gracefully with detailed reporting

## Scope

### In Scope
- Replace fake validation with real Cloudflare API calls
- Query Cloudflare API to verify tunnel exists by name
- Query Cloudflare API to verify DNS record exists
- Extract zone ID from zone name for DNS queries
- Handle API errors gracefully with try/except blocks
- Update validation results based on actual API responses
- Provide detailed validation summary report
- Implement UniFi validation (checking Terraform apply success as baseline)
- Create validation container with `alpine/curl` and `jq`
- Parse JSON API responses to determine resource existence

### Out of Scope
- Resource creation (handled in Prompts 02 and 03)
- Cleanup logic (handled in Prompt 05)
- HTTP connectivity checks (validate_connectivity parameter - keep as optional/future)
- UniFi API validation (complex authentication, use Terraform success as proxy)

## Proposed Solution

### Cloudflare Validation Flow

```python
# Phase 4: Validation
report_lines.append("")
report_lines.append("PHASE 4: Validating resources...")

# Validate Cloudflare resources using API
cf_token_plain = await cloudflare_token.plaintext()

# Create a container with curl/jq for API calls
validate_ctr = dagger.dag.container().from_("alpine/curl:latest")
validate_ctr = validate_ctr.with_exec(["apk", "add", "--no-cache", "jq"])

# Query Cloudflare API for tunnel
try:
    tunnel_list_result = await validate_ctr.with_exec([
        "sh", "-c",
        f'curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/cfd_tunnel?name={tunnel_name}" \
         -H "Authorization: Bearer {cf_token_plain}" \
         -H "Content-Type: application/json"'
    ]).stdout()
    
    # Parse result to check if tunnel exists
    tunnel_count = await validate_ctr.with_exec([
        "sh", "-c",
        f'echo \'{tunnel_list_result}\' | jq \'.result | length\''
    ]).stdout()
    
    if tunnel_count.strip() == "1":
        report_lines.append(f"  ✓ Cloudflare tunnel validated: {tunnel_name}")
        validation_results["cloudflare_tunnel"] = "validated"
    else:
        report_lines.append(f"  ✗ Cloudflare tunnel not found: {tunnel_name}")
        validation_results["cloudflare_tunnel"] = "not_found"
except Exception as e:
    report_lines.append(f"  ✗ Cloudflare tunnel validation failed: {str(e)}")
    validation_results["cloudflare_tunnel"] = f"error: {str(e)}"
```

### DNS Record Validation Flow

```python
# Query Cloudflare API for DNS record
try:
    # First get zone ID from zone name
    dns_list_result = await validate_ctr.with_exec([
        "sh", "-c",
        f'curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name={cloudflare_zone}" \
         -H "Authorization: Bearer {cf_token_plain}" \
         -H "Content-Type: application/json"'
    ]).stdout()
    
    # Extract zone ID
    zone_id = await validate_ctr.with_exec([
        "sh", "-c",
        f'echo \'{dns_list_result}\' | jq -r \'.result[0].id\''
    ]).stdout()
    
    if zone_id and zone_id.strip() != "null":
        # Query DNS records for the hostname
        dns_record_result = await validate_ctr.with_exec([
            "sh", "-c",
            f'curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id.strip()}/dns_records?name={test_hostname}" \
             -H "Authorization: Bearer {cf_token_plain}" \
             -H "Content-Type: application/json"'
        ]).stdout()
        
        # Check if record exists
        dns_count = await validate_ctr.with_exec([
            "sh", "-c",
            f'echo \'{dns_record_result}\' | jq \'.result | length\''
        ]).stdout()
        
        if dns_count.strip() == "1":
            report_lines.append(f"  ✓ Cloudflare DNS validated: {test_hostname}")
            validation_results["cloudflare_dns"] = "validated"
        else:
            report_lines.append(f"  ✗ Cloudflare DNS not found: {test_hostname}")
            validation_results["cloudflare_dns"] = "not_found"
    else:
        report_lines.append(f"  ✗ Could not find zone: {cloudflare_zone}")
        validation_results["cloudflare_dns"] = "zone_not_found"
except Exception as e:
    report_lines.append(f"  ✗ Cloudflare DNS validation failed: {str(e)}")
    validation_results["cloudflare_dns"] = f"error: {str(e)}"
```

### UniFi Validation (Graceful)

```python
# Validate UniFi resources (may fail due to test MAC not being in controller)
try:
    # UniFi API validation is complex due to authentication
    # For now, mark as validated if Terraform apply succeeded
    if validation_results.get("unifi_dns") == "created":
        report_lines.append(f"  ✓ UniFi DNS validated (Terraform apply succeeded)")
        validation_results["unifi_validation"] = "validated"
    else:
        report_lines.append(f"  ○ UniFi DNS validation skipped (creation may have failed)")
        validation_results["unifi_validation"] = "skipped"
except Exception as e:
    report_lines.append(f"  ○ UniFi validation skipped: {str(e)}")
    validation_results["unifi_validation"] = f"skipped: {str(e)}"
```

### Validation Summary

```python
# Determine overall validation status
cf_success = validation_results.get("cloudflare_tunnel") == "validated" and \
             validation_results.get("cloudflare_dns") == "validated"

report_lines.append("")
report_lines.append("-" * 60)
if cf_success:
    report_lines.append("VALIDATION SUMMARY: ✓ CLOUDFLARE RESOURCES VALIDATED")
else:
    report_lines.append("VALIDATION SUMMARY: ✗ SOME RESOURCES NOT FOUND")
report_lines.append("-" * 60)
```

## Dependencies

- **Prompt 02** (`02-implement-cloudflare-creation`): Must create Cloudflare resources to validate
- **Prompt 03** (`03-implement-unifi-creation`): Must create UniFi resources to validate
- **Existing Code**: `test_integration` function (lines 1083-1105) contains current fake validation

## Acceptance Criteria

- [ ] Phase 4 creates a validation container with `alpine/curl:latest` and installs `jq`
- [ ] Cloudflare API token is obtained via `await cloudflare_token.plaintext()`
- [ ] Cloudflare tunnel is queried using GET `/accounts/{account_id}/cfd_tunnel?name={tunnel_name}`
- [ ] Zone ID is extracted from zone name query (`/zones?name={cloudflare_zone}`)
- [ ] DNS record is queried using GET `/zones/{zone_id}/dns_records?name={test_hostname}`
- [ ] Validation results are updated based on actual API response parsing (`.result | length`)
- [ ] All API calls are wrapped in try/except blocks for graceful error handling
- [ ] Error messages include specific failure details
- [ ] UniFi validation checks `validation_results["unifi_dns"]` status
- [ ] Validation summary reflects actual resource state (success/failure)
- [ ] Report includes details about which resources passed/failed validation
- [ ] Optional `validate_connectivity` parameter remains as future enhancement

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cloudflare API rate limits | Medium | Use minimal API calls (2 per validation); test runs are infrequent |
| API token lacks permissions | High | Document required permissions (Zone:Read, Tunnel:Read); fail gracefully |
| Zone not found | Medium | Validate zone exists before DNS query; report clear error |
| Network connectivity to Cloudflare | Medium | Error handling catches connection failures; report as validation error |
| JSON parsing failures | Low | Use `jq` for robust parsing; catch parsing errors |
| UniFi API complexity | Medium | Use Terraform success as validation proxy; document limitation |

## Cloudflare API Permissions Required

The Cloudflare API token must have the following permissions:
- **Zone:Read** - To list zones and get zone ID
- **DNS Records:Read** - To query DNS records
- **Cloudflare Tunnel:Read** - To query tunnel status

## References

- Target: Phase 4 in `test_integration` function (lines 1083-1105) in `src/main/main.py`
- Cloudflare API docs: https://developers.cloudflare.com/api/
- Tunnel API: GET /accounts/{account_id}/cfd_tunnel
- DNS API: GET /zones/{zone_id}/dns_records
- Zone API: GET /zones?name={zone_name}
- Related changes: `02-implement-cloudflare-creation`, `03-implement-unifi-creation`
