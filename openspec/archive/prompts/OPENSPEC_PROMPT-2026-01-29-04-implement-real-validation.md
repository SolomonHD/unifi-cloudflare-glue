# OpenSpec Change Prompt 04: Implement Real Resource Validation

## Context

Currently, Phase 4 of `test_integration` (lines 942-965) only sets `cf_validation = True` and `unifi_validation = True` without actually verifying that resources exist. Real validation should query the Cloudflare and UniFi APIs to confirm the resources were created successfully.

## Goal

Implement real validation by making API calls to Cloudflare and UniFi to verify the test resources exist.

## Scope

**In scope:**
- Replace fake validation with real API calls
- Query Cloudflare API to verify tunnel exists
- Query Cloudflare API to verify DNS record exists
- Query UniFi API to verify DNS records exist (if possible)
- Update validation results based on actual API responses
- Handle API errors gracefully

**Out of scope:**
- Resource creation (handled in Prompts 02 and 03)
- Cleanup logic (handled in Prompt 05)
- HTTP connectivity checks (validate_connectivity parameter - keep as optional/future)

## Desired Behavior

### 1. Cloudflare Validation

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

# Query Cloudflare API for DNS record
try:
    dns_list_result = await validate_ctr.with_exec([
        "sh", "-c",
        f'curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name={cloudflare_zone}" \
         -H "Authorization: Bearer {cf_token_plain}" \
         -H "Content-Type: application/json"'
    ]).stdout()
    
    # Extract zone ID and query for DNS record
    zone_id = await validate_ctr.with_exec([
        "sh", "-c",
        f'echo \'{dns_list_result}\' | jq -r \'.result[0].id\''
    ]).stdout()
    
    if zone_id and zone_id.strip() != "null":
        dns_record_result = await validate_ctr.with_exec([
            "sh", "-c",
            f'curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id.strip()}/dns_records?name={test_hostname}" \
             -H "Authorization: Bearer {cf_token_plain}" \
             -H "Content-Type: application/json"'
        ]).stdout()
        
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

### 2. UniFi Validation (Optional/Graceful)

```python
# Validate UniFi resources (may fail due to test MAC not being in controller)
try:
    # UniFi API validation is complex due to authentication
    # For now, mark as validated if Terraform apply succeeded
    # Future: Implement actual UniFi API query
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

### 3. Validation Summary

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

## Constraints & Assumptions

- Cloudflare API token must have permissions to read tunnels and DNS records
- Validation uses the Cloudflare REST API (api.cloudflare.com)
- UniFi validation is simplified due to complex authentication requirements
- Use `alpine/curl` container with `jq` for JSON parsing
- The tunnel name and DNS record are known from earlier phases
- Zone name is used to look up zone ID first, then query DNS records

## Dependencies

- Prompt 02: Implement Cloudflare Creation (resources must exist to validate)
- Prompt 03: Implement UniFi Creation (resources must exist to validate)

## Acceptance Criteria

- [ ] Phase 4 creates a validation container with curl and jq
- [ ] Cloudflare API is queried to verify tunnel exists by name
- [ ] Cloudflare API is queried to verify DNS record exists
- [ ] Zone ID is extracted from zone name query
- [ ] Validation results are updated based on actual API responses
- [ ] UniFi validation is implemented (at minimum checking Terraform success)
- [ ] Errors during validation are caught and logged, not raised
- [ ] Validation summary reflects actual resource state
- [ ] Report includes details about which resources passed/failed validation

## Reference

- Target: Phase 4 in `test_integration` function (lines 942-965) in `src/main/main.py`
- Cloudflare API docs: https://developers.cloudflare.com/api/
- Tunnel API: GET /accounts/{account_id}/cfd_tunnel
- DNS API: GET /zones/{zone_id}/dns_records
