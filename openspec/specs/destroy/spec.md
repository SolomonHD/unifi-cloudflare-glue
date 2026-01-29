# Spec: Destroy Function

## ADDED Requirements

### Requirement: destroy Function

The Dagger module SHALL provide a `destroy` function that tears down deployed resources in the reverse order of deployment (Cloudflare first, then UniFi) to prevent DNS loops and ensure clean removal.

#### Scenario: Full Destruction
Given deployed UniFi and Cloudflare resources
And valid credentials for both providers
When the `destroy` function is called
Then it executes the following steps in order:
  1. Destroy Cloudflare resources (tunnels, DNS records)
  2. Destroy UniFi resources (DNS records)
And returns a combined status message

#### Scenario: Destruction Order Enforcement
Given a call to the `destroy` function
When the destruction executes
Then Cloudflare destruction ALWAYS runs before UniFi destruction
And prevents DNS resolution issues during teardown

#### Scenario: KCL Generation for Destroy
Given a KCL source directory
When the destroy process begins
Then it generates configurations from KCL (same as deploy)
Or uses existing state files if available
To identify resources to destroy

#### Scenario: Destroy with API Key Authentication
Given UniFi API key authentication was used for deployment
When the `destroy` function is called with API key
Then it destroys resources using the same authentication method

#### Scenario: Destroy with Username/Password Authentication
Given UniFi username/password was used for deployment
When the `destroy` function is called with username/password
Then it destroys resources using the same authentication method

#### Scenario: Selective Destroy Not Supported
Given a user wants to destroy only Cloudflare resources
When they call the `destroy` function
Then it destroys both Cloudflare AND UniFi resources
(Selective destruction is not supported - use module-specific functions)

---

### Requirement: destroy Function Parameters

The `destroy` function SHALL accept the same parameters as the `deploy` function.

#### Scenario: KCL Source Parameter
Given the function signature
Then it accepts a required `kcl_source` parameter of type `dagger.Directory`
Containing the KCL module with configuration

#### Scenario: UniFi Authentication Parameters
Given the function signature
Then it accepts UniFi authentication parameters (mutually exclusive):
| Parameter | Type | Description |
|-----------|------|-------------|
| `unifi_url` | `str` | UniFi Controller URL |
| `api_url` | `str` | UniFi API URL (optional) |
| `unifi_api_key` | `dagger.Secret` | UniFi API key (optional) |
| `unifi_username` | `dagger.Secret` | UniFi username (optional) |
| `unifi_password` | `dagger.Secret` | UniFi password (optional) |

#### Scenario: Cloudflare Authentication Parameters
Given the function signature
Then it accepts Cloudflare authentication parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `cloudflare_token` | `dagger.Secret` | Cloudflare API Token |
| `cloudflare_account_id` | `str` | Cloudflare Account ID |
| `zone_name` | `str` | DNS zone name |

#### Scenario: Authentication Validation
Given the `destroy` function
When called with invalid authentication
Then it validates authentication parameters
And returns clear error messages for validation failures

---

### Requirement: destroy Function Execution

The `destroy` function SHALL execute Terraform destroy in the correct order with proper error handling.

#### Scenario: Cloudflare Destroy First
Given valid credentials
When destruction begins
Then it runs `terraform destroy -auto-approve` for Cloudflare module first
And waits for completion before proceeding

#### Scenario: UniFi Destroy Second
Given Cloudflare destruction succeeds
When the function proceeds
Then it runs `terraform destroy -auto-approve` for UniFi module
And waits for completion

#### Scenario: Destroy Failure - Cloudflare Fails
Given Cloudflare destruction fails
When the function executes
Then it stops execution
And does NOT proceed to UniFi destruction
And returns an error message with Cloudflare failure details

#### Scenario: Destroy Failure - UniFi Fails
Given Cloudflare destruction succeeds but UniFi fails
When the function executes
Then it reports both results:
  - Cloudflare destruction: success
  - UniFi destruction: failed
And warns about potential orphaned resources

---

### Requirement: destroy Function Return Value

The `destroy` function SHALL return a comprehensive status message.

#### Scenario: Success Return Format
Given successful destruction of all resources
When the function returns
Then the return value is a string containing:
  - "✓ Success" indicator
  - Cloudflare destruction summary
  - UniFi destruction summary
  - Note about state file cleanup if using local state

#### Scenario: Partial Failure Return Format
Given partial failure (Cloudflare succeeds, UniFi fails)
When the function returns
Then the return value is a string containing:
  - Mixed success/failure indicators
  - Cloudflare success details
  - UniFi failure details with error
  - Warning about orphaned UniFi resources

#### Scenario: Complete Failure Return Format
Given complete failure (Cloudflare fails)
When the function returns
Then the return value is a string containing:
  - "✗ Failed" indicator
  - Error details from Cloudflare destruction
  - Note that UniFi destruction was skipped
  - Warning that all resources may still exist

#### Scenario: State File Warning
Given destruction completes (success or partial)
When the function returns
Then it includes a warning about Terraform state files
And suggests manual cleanup of state files if using local state
