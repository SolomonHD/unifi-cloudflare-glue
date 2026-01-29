# Specification: Dagger Module - Real Resource Validation

## ADDED Requirements

### Requirement: Cloudflare Tunnel Validation via API

The `test_integration` function SHALL query the Cloudflare API to verify that the tunnel was created successfully.

#### Scenario: Successful Tunnel Query
Given a Cloudflare tunnel was created in Phase 2 with name `tunnel-{test_id}`
When the validation phase queries the Cloudflare API for tunnels with matching name
Then the API returns a response with exactly one tunnel result
And `validation_results["cloudflare_tunnel"]` is set to `"validated"`
And the report shows `✓ Cloudflare tunnel validated: {tunnel_name}`

#### Scenario: Tunnel Not Found
Given a Cloudflare tunnel was expected to exist
When the validation phase queries the Cloudflare API
Then the API returns zero results for the tunnel name
And `validation_results["cloudflare_tunnel"]` is set to `"not_found"`
And the report shows `✗ Cloudflare tunnel not found: {tunnel_name}`

#### Scenario: Tunnel Validation Error
Given a Cloudflare tunnel validation is attempted
When the API query fails (network error, auth failure, etc.)
Then the exception is caught gracefully
And `validation_results["cloudflare_tunnel"]` is set to `"error: {message}"`
And the report shows `✗ Cloudflare tunnel validation failed: {message}`

---

### Requirement: Cloudflare DNS Record Validation via API

The function SHALL query the Cloudflare API to verify that DNS records were created successfully.

#### Scenario: Successful DNS Record Query
Given a Cloudflare DNS record was created in Phase 2 with hostname `{test_id}.{cloudflare_zone}`
When the validation phase first queries the zone ID by zone name
And then queries DNS records for the hostname using the zone ID
Then the API returns a response with exactly one DNS record result
And `validation_results["cloudflare_dns"]` is set to `"validated"`
And the report shows `✓ Cloudflare DNS validated: {test_hostname}`

#### Scenario: DNS Record Not Found
Given a Cloudflare DNS record was expected to exist
When the validation phase queries the DNS records API
Then the API returns zero results for the hostname
And `validation_results["cloudflare_dns"]` is set to `"not_found"`
And the report shows `✗ Cloudflare DNS not found: {test_hostname}`

#### Scenario: Zone Not Found
Given the Cloudflare zone name is queried
When the zone lookup returns no matching zone
Then `validation_results["cloudflare_dns"]` is set to `"zone_not_found"`
And the report shows `✗ Could not find zone: {cloudflare_zone}`

#### Scenario: DNS Validation Error
Given a Cloudflare DNS validation is attempted
When the API query fails (network error, auth failure, etc.)
Then the exception is caught gracefully
And `validation_results["cloudflare_dns"]` is set to `"error: {message}"`
And the report shows `✗ Cloudflare DNS validation failed: {message}`

---

### Requirement: Validation Container Setup

The function SHALL create a container with the necessary tools for API validation.

#### Scenario: Create Validation Container
Given the validation phase needs to make API calls
When the phase creates a container from `alpine/curl:latest`
And installs `jq` package for JSON parsing
Then the container is ready for Cloudflare API calls

#### Scenario: API Token Retrieval
Given the validation phase needs to authenticate API calls
When `await cloudflare_token.plaintext()` is called
Then the Cloudflare API token is obtained for use in curl commands

---

### Requirement: UniFi Resource Validation

The function SHALL validate UniFi resources based on Terraform apply results.

#### Scenario: UniFi Validation via Terraform Success
Given UniFi DNS records were created in Phase 3
When the validation phase checks `validation_results["unifi_dns"]`
And the value equals `"created"`
Then `validation_results["unifi_validation"]` is set to `"validated"`
And the report shows `✓ UniFi DNS validated (Terraform apply succeeded)`

#### Scenario: UniFi Validation Skipped
Given UniFi DNS records may not have been created
When the validation phase checks `validation_results["unifi_dns"]`
And the value is not `"created"`
Then `validation_results["unifi_validation"]` is set to `"skipped"`
And the report shows `○ UniFi DNS validation skipped (creation may have failed)`

---

### Requirement: Validation Summary Report

The function SHALL generate a summary of validation results.

#### Scenario: All Cloudflare Resources Validated
Given both tunnel and DNS validations succeeded
When the validation summary is generated
Then the report shows `VALIDATION SUMMARY: ✓ CLOUDFLARE RESOURCES VALIDATED`

#### Scenario: Some Resources Not Found
Given at least one Cloudflare validation failed
When the validation summary is generated
Then the report shows `VALIDATION SUMMARY: ✗ SOME RESOURCES NOT FOUND`
And details of which validations passed/failed are included

---

### Requirement: Cloudflare API Call Structure

The function SHALL construct proper Cloudflare API requests.

#### Scenario: Tunnel API Call
Given the validation phase queries for a tunnel
When the curl command is constructed
Then it uses GET method to `https://api.cloudflare.com/client/v4/accounts/{account_id}/cfd_tunnel`
And it includes query parameter `?name={tunnel_name}`
And it includes Authorization header with Bearer token
And it includes Content-Type header with value application/json

#### Scenario: Zone API Call
Given the validation phase needs a zone ID
When the curl command is constructed
Then it uses GET method to `https://api.cloudflare.com/client/v4/zones`
And it includes query parameter `?name={cloudflare_zone}`
And it includes Authorization header with Bearer token

#### Scenario: DNS Record API Call
Given the validation phase queries for a DNS record
When the curl command is constructed
Then it uses GET method to `https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records`
And it includes query parameter `?name={test_hostname}`
And it includes Authorization header with Bearer token

---

### Requirement: JSON Response Parsing

The function SHALL parse Cloudflare API responses to determine resource existence.

#### Scenario: Parse Tunnel Count
Given the tunnel API returns a JSON response
When the response is parsed with `jq '.result | length'`
Then a count of "1" indicates the tunnel exists
And a count of "0" indicates the tunnel was not found

#### Scenario: Parse Zone ID
Given the zone API returns a JSON response
When the response is parsed with `jq -r '.result[0].id'`
Then the zone ID is extracted for use in DNS queries
And a value of "null" indicates the zone was not found

#### Scenario: Parse DNS Record Count
Given the DNS record API returns a JSON response
When the response is parsed with `jq '.result | length'`
Then a count of "1" indicates the DNS record exists
And a count of "0" indicates the DNS record was not found

---

## MODIFIED Requirements

### Requirement: Phase 4 Implementation

Phase 4 of `test_integration` SHALL be modified to perform real API validation instead of fake validation.

#### Scenario: Replace Fake Validation
Given the current Phase 4 implementation (lines 1083-1105)
When the code is modified
Then the fake validation (setting `cf_validation = True`) is removed
And real Cloudflare API queries are added
And `validation_results` is properly updated based on API responses
And validation summary reflects actual resource state

#### Scenario: Maintain Report Format
Given the validation is performed
When the report lines are generated
Then the Phase 4 header is preserved
And individual validation results are reported
And the validation summary header format is preserved

---

## Technical References

### Source Code Locations

| Element | File | Lines | Description |
|---------|------|-------|-------------|
| `test_integration` | `src/main/main.py` | 789-1185 | Main integration test function |
| Phase 4 (current) | `src/main/main.py` | 1083-1105 | Fake validation to replace |
| `deploy_cloudflare()` | `src/main/main.py` | 223-298 | Reference for Cloudflare operations |

### Cloudflare API Endpoints

| Endpoint | Method | Path | Purpose |
|----------|--------|------|---------|
| List Tunnels | GET | `/accounts/{account_id}/cfd_tunnel?name={tunnel_name}` | Query tunnel by name |
| List Zones | GET | `/zones?name={cloudflare_zone}` | Get zone ID from name |
| List DNS Records | GET | `/zones/{zone_id}/dns_records?name={test_hostname}` | Query DNS record |

### Required API Token Permissions

| Permission | Scope | Purpose |
|------------|-------|---------|
| Zone:Read | Zone | List zones to get zone ID |
| DNS Records:Read | Zone | Query DNS records |
| Cloudflare Tunnel:Read | Account | Query tunnel status |

### Dagger Patterns

```python
# Validation container creation
validate_ctr = dagger.dag.container().from_("alpine/curl:latest")
validate_ctr = validate_ctr.with_exec(["apk", "add", "--no-cache", "jq"])

# API token retrieval
cf_token_plain = await cloudflare_token.plaintext()

# API call with curl
result = await validate_ctr.with_exec([
    "sh", "-c",
    f'curl -s -X GET "{api_url}" -H "Authorization: Bearer {token}"'
]).stdout()

# JSON parsing with jq
count = await validate_ctr.with_exec([
    "sh", "-c",
    f'echo \'{result}\' | jq \'.result | length\''
]).stdout()
```
