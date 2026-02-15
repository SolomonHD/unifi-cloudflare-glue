## MODIFIED Requirements

### Requirement: MAC address validation rule explanation
The documentation SHALL explain MAC address validation including accepted formats, normalization process, rationale for lowercase colon format, AND provide enhanced error messages with specific resolution guidance.

#### Scenario: User understands accepted MAC formats
- **WHEN** user reads MAC validation documentation
- **THEN** documentation lists all three accepted formats (aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff)

#### Scenario: User learns normalization rationale
- **WHEN** user encounters MAC address normalization
- **THEN** documentation explains why lowercase colon format enables consistent cross-provider matching

#### Scenario: User debugs invalid MAC format
- **WHEN** user receives MAC validation error
- **THEN** documentation shows error message interpretation and correction steps

#### Scenario: MAC consistency error with actionable details
- **WHEN** user encounters MAC_CONSISTENCY_ERROR
- **THEN** the error message SHALL include:
  - Specific MAC addresses that are missing from UniFi devices
  - Complete list of available UniFi MAC addresses
  - Suggestion to either add UniFi device with the missing MAC or update Cloudflare tunnel configuration

### Requirement: Hostname validation rule explanation
The documentation SHALL explain hostname validation (RFC 1123) including length limits, character restrictions, boundary rules, AND provide enhanced error messages with specific examples.

#### Scenario: User learns hostname constraints
- **WHEN** user reads hostname validation
- **THEN** documentation specifies 1-63 character limit, alphanumeric start/end, and hyphen-only internal characters

#### Scenario: User fixes invalid hostname
- **WHEN** user has hostname validation failure
- **THEN** documentation provides examples of common mistakes (underscores, leading hyphens, trailing hyphens)

#### Scenario: User understands hostname purpose
- **WHEN** user configures device hostname
- **THEN** documentation explains how hostname combines with domain to form fully qualified DNS names

#### Scenario: Duplicate hostname error with conflict details
- **WHEN** user encounters DUPLICATE_HOSTNAME_ERROR
- **THEN** the error message SHALL include:
  - List of duplicate friendly_hostnames
  - Which specific devices have conflicting hostnames
  - Suggestion to use unique friendly_hostnames for each device

### Requirement: DNS loop prevention rule explanation
The documentation SHALL explain DNS loop prevention validation including internal domain requirements, rationale, AND provide enhanced error messages with concrete examples.

#### Scenario: User understands internal domain requirement
- **WHEN** user configures Cloudflare local service URLs
- **THEN** documentation lists valid internal domain suffixes (.internal.lan, .local, .home, .home.arpa, .localdomain)

#### Scenario: User learns DNS loop consequence
- **WHEN** user reads DNS loop prevention rationale
- **THEN** documentation explains how using public zone in local_service_url causes resolution loops and tunnel failures

#### Scenario: User fixes DNS loop error
- **WHEN** user encounters DNS loop validation error
- **THEN** documentation shows how to identify public zone references and replace with internal hostnames

#### Scenario: Domain syntax error with format examples
- **WHEN** user encounters DOMAIN_SYNTAX_ERROR
- **THEN** the error message SHALL include:
  - Specific services with invalid local_service_url values
  - Examples of valid domain formats (http://service.internal.lan:8096, https://service.local:443)
  - Explanation that internal domains or valid public domains are required

### Requirement: Cross-provider consistency validation explanation
The documentation SHALL explain MAC consistency validation between UniFi and Cloudflare configurations with enhanced troubleshooting guidance.

#### Scenario: User understands MAC consistency requirement
- **WHEN** user reads cross-provider validation
- **THEN** documentation explains that every Cloudflare tunnel MAC MUST exist in UniFi device endpoints

#### Scenario: User fixes MAC mismatch error
- **WHEN** user encounters MAC consistency error
- **THEN** documentation shows available UniFi MACs and instructions to add missing device or correct tunnel MAC

#### Scenario: Error message shows both sides of the mismatch
- **WHEN** MAC consistency validation fails
- **THEN** the error message SHALL show:
  - MAC addresses referenced by Cloudflare tunnels
  - MAC addresses available in UniFi devices
  - Clear indication of which MACs are missing

## ADDED Requirements

### Requirement: Public hostname uniqueness validation explanation
The documentation SHALL explain public hostname uniqueness validation across tunnel services with clear error messages.

#### Scenario: User understands public hostname uniqueness requirement
- **WHEN** user configures multiple tunnel services
- **THEN** documentation explains that each public_hostname must be unique across all tunnels

#### Scenario: User fixes duplicate public hostname error
- **WHEN** user encounters DUPLICATE_PUBLIC_HOSTNAME_ERROR
- **THEN** the error message SHALL include:
  - List of duplicate public_hostnames
  - Which tunnels/services have conflicting public_hostnames
  - Suggestion to use unique public_hostnames for each service
