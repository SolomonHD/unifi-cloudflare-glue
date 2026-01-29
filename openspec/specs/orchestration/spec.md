# Spec: Deployment Orchestration Function

## ADDED Requirements

### Requirement: deploy Function (Orchestration)

The Dagger module SHALL provide a `deploy` function that orchestrates the complete deployment workflow: KCL generation, UniFi deployment, and Cloudflare deployment in the correct order.

#### Scenario: Full Deployment Orchestration
Given a KCL source directory with valid configuration
And UniFi credentials (API key or username/password)
And Cloudflare credentials (token, account ID, zone)
When the `deploy` function is called
Then it executes the following steps in order:
  1. Generate UniFi JSON configuration from KCL
  2. Generate Cloudflare JSON configuration from KCL
  3. Deploy UniFi DNS (creates local DNS records)
  4. Deploy Cloudflare Tunnels (points to now-resolvable hostnames)
And returns a combined status message

#### Scenario: Deployment Order Enforcement
Given a call to the `deploy` function
When the orchestration executes
Then UniFi deployment ALWAYS runs before Cloudflare deployment
And Cloudflare deployment only proceeds if UniFi deployment succeeds

#### Scenario: KCL Generation Integration
Given a KCL source directory
When the orchestration begins
Then it calls existing `generate_unifi_config` function
And it calls existing `generate_cloudflare_config` function
And exports generated files to a working directory

#### Scenario: Orchestration Failure - UniFi Deployment Fails
Given a configuration that causes UniFi deployment to fail
When the `deploy` function runs
Then it stops execution after UniFi deployment failure
And does NOT proceed to Cloudflare deployment
And returns an error message indicating UniFi deployment failed

#### Scenario: Orchestration Failure - Cloudflare Deployment Fails
Given UniFi deployment succeeds but Cloudflare deployment fails
When the `deploy` function runs
Then it reports both results:
  - UniFi deployment: success
  - Cloudflare deployment: failed
And returns a combined status with both outcomes

#### Scenario: Deployment Success Reporting
Given both UniFi and Cloudflare deployments succeed
When the function completes
Then it returns a message starting with "✓ Success"
And includes summary of both deployments
And lists applied resources from both providers

---

### Requirement: deploy Function Parameters

The `deploy` function SHALL accept all parameters needed for both UniFi and Cloudflare deployments, plus KCL source.

#### Scenario: KCL Source Parameter
Given the function signature
Then it accepts a required `kcl_source` parameter of type `dagger.Directory`
Containing the KCL module with schemas and generators

#### Scenario: Combined UniFi Parameters
Given the function signature
Then it accepts all UniFi deployment parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `unifi_url` | `str` | UniFi Controller URL |
| `api_url` | `str` | UniFi API URL (optional, defaults to unifi_url) |
| `unifi_api_key` | `dagger.Secret` | UniFi API key (optional) |
| `unifi_username` | `dagger.Secret` | UniFi username (optional) |
| `unifi_password` | `dagger.Secret` | UniFi password (optional) |

#### Scenario: Combined Cloudflare Parameters
Given the function signature
Then it accepts all Cloudflare deployment parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `cloudflare_token` | `dagger.Secret` | Cloudflare API Token |
| `cloudflare_account_id` | `str` | Cloudflare Account ID |
| `zone_name` | `str` | DNS zone name |

#### Scenario: Parameter Validation
Given the `deploy` function
When called with invalid or missing parameters
Then it validates all parameters before starting execution
And returns clear error messages for any validation failures

---

### Requirement: deploy Function Return Value

The `deploy` function SHALL return a comprehensive status message suitable for CLI display.

#### Scenario: Success Return Format
Given successful orchestration
When the function returns
Then the return value is a string containing:
  - "✓ Success" indicator
  - UniFi deployment summary
  - Cloudflare deployment summary
  - Total resources created/updated

#### Scenario: Partial Failure Return Format
Given partial failure (UniFi succeeds, Cloudflare fails)
When the function returns
Then the return value is a string containing:
  - Mixed success/failure indicators
  - UniFi success details
  - Cloudflare failure details with error

#### Scenario: Complete Failure Return Format
Given complete failure (UniFi fails)
When the function returns
Then the return value is a string containing:
  - "✗ Failed" indicator
  - Error details from UniFi deployment
  - Note that Cloudflare deployment was skipped
