## ADDED Requirements

### Requirement: Error reference documents Dagger module errors

The troubleshooting guide SHALL document common Dagger module errors including module not found, secret parameter errors, container execution failures, and function not found errors.

#### Scenario: User encounters module not found error
- **WHEN** user runs `dagger call -m unifi-cloudflare-glue` and module is not installed
- **THEN** documentation provides symptoms (error message), cause (not installed or wrong name), solution (install command), and prevention (installation verification)

#### Scenario: User encounters secret parameter error
- **WHEN** user passes secret without `env:` prefix
- **THEN** documentation explains the `env:SECRET_VAR` syntax requirement with examples

#### Scenario: User encounters container execution failure
- **WHEN** Dagger container fails to execute
- **THEN** documentation provides debugging steps for container issues

### Requirement: Error reference documents Terraform errors

The troubleshooting guide SHALL document common Terraform errors including backend initialization failures, state lock timeouts, provider authentication failures, and provider configuration errors.

#### Scenario: User encounters backend initialization failure
- **WHEN** `terraform init` fails due to backend issues
- **THEN** documentation provides steps to verify backend config, credentials, and network access

#### Scenario: User encounters state lock timeout
- **WHEN** Terraform cannot acquire state lock
- **THEN** documentation explains lock mechanism, how to check for stale locks, and force-unlock procedure with warnings

#### Scenario: User encounters provider authentication failure
- **WHEN** UniFi or Cloudflare provider cannot authenticate
- **THEN** documentation provides credential verification steps for each provider

### Requirement: Error reference documents KCL validation errors

The troubleshooting guide SHALL document common KCL validation errors including MAC address format validation, DNS loop detection, duplicate MAC addresses, and schema validation failures.

#### Scenario: User encounters MAC address format error
- **WHEN** KCL validation fails due to invalid MAC format
- **THEN** documentation shows accepted formats and normalization to `aa:bb:cc:dd:ee:ff`

#### Scenario: User encounters DNS loop detection error
- **WHEN** Cloudflare local_service_url points to external hostname
- **THEN** documentation explains why internal domains (.internal.lan) are required

#### Scenario: User encounters duplicate MAC error
- **WHEN** same MAC address is used for multiple devices
- **THEN** documentation explains uniqueness requirement and how to resolve conflicts

### Requirement: Error reference documents UniFi Controller errors

The troubleshooting guide SHALL document common UniFi Controller errors including TLS certificate verification failures, API authentication errors, connection refused, and timeout errors.

#### Scenario: User encounters TLS certificate error
- **WHEN** connection to UniFi Controller fails due to self-signed certificate
- **THEN** documentation explains `--unifi-insecure` flag and proper certificate options

#### Scenario: User encounters UniFi API authentication error
- **WHEN** UniFi provider returns 401 Unauthorized
- **THEN** documentation provides steps to verify API key and check expiration

### Requirement: Error reference documents Cloudflare API errors

The troubleshooting guide SHALL document common Cloudflare API errors including zone not found, insufficient permissions, tunnel name conflicts, and rate limit exceeded.

#### Scenario: User encounters zone not found error
- **WHEN** Cloudflare provider cannot find DNS zone
- **THEN** documentation provides steps to verify zone name and API token permissions

#### Scenario: User encounters insufficient permissions error
- **WHEN** API token lacks required permissions
- **THEN** documentation lists required permissions for tunnel and DNS management

#### Scenario: User encounters rate limit error
- **WHEN** Cloudflare API returns 429 rate limit
- **THEN** documentation explains rate limits and retry strategies

### Requirement: Each error entry follows consistent format

All error entries in the troubleshooting guide SHALL follow a consistent format with Symptoms, Cause, Solution, and Prevention sections.

#### Scenario: User reads any error entry
- **WHEN** user navigates to any error in the reference
- **THEN** the entry contains all four sections: Symptoms (what user sees), Cause (why it happens), Solution (how to fix), Prevention (how to avoid)
