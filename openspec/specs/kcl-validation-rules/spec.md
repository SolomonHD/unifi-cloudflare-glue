## ADDED Requirements

### Requirement: MAC address validation rule explanation
The documentation SHALL explain MAC address validation including accepted formats, normalization process, and rationale for lowercase colon format.

#### Scenario: User understands accepted MAC formats
- **WHEN** user reads MAC validation documentation
- **THEN** documentation lists all three accepted formats (aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff)

#### Scenario: User learns normalization rationale
- **WHEN** user encounters MAC address normalization
- **THEN** documentation explains why lowercase colon format enables consistent cross-provider matching

#### Scenario: User debugs invalid MAC format
- **WHEN** user receives MAC validation error
- **THEN** documentation shows error message interpretation and correction steps

### Requirement: Hostname validation rule explanation
The documentation SHALL explain hostname validation (RFC 1123) including length limits, character restrictions, and boundary rules.

#### Scenario: User learns hostname constraints
- **WHEN** user reads hostname validation
- **THEN** documentation specifies 1-63 character limit, alphanumeric start/end, and hyphen-only internal characters

#### Scenario: User fixes invalid hostname
- **WHEN** user has hostname validation failure
- **THEN** documentation provides examples of common mistakes (underscores, leading hyphens, trailing hyphens)

#### Scenario: User understands hostname purpose
- **WHEN** user configures device hostname
- **THEN** documentation explains how hostname combines with domain to form fully qualified DNS names

### Requirement: DNS loop prevention rule explanation
The documentation SHALL explain DNS loop prevention validation including internal domain requirements and rationale.

#### Scenario: User understands internal domain requirement
- **WHEN** user configures Cloudflare local service URLs
- **THEN** documentation lists valid internal domain suffixes (.internal.lan, .local, .home, .home.arpa, .localdomain)

#### Scenario: User learns DNS loop consequence
- **WHEN** user reads DNS loop prevention rationale
- **THEN** documentation explains how using public zone in local_service_url causes resolution loops and tunnel failures

#### Scenario: User fixes DNS loop error
- **WHEN** user encounters DNS loop validation error
- **THEN** documentation shows how to identify public zone references and replace with internal hostnames

### Requirement: One tunnel per device rule explanation
The documentation SHALL explain the one-tunnel-per-device constraint including enforcement mechanism and workarounds for complex scenarios.

#### Scenario: User understands device-to-tunnel mapping
- **WHEN** user defines multiple tunnels
- **THEN** documentation explains that each physical device MAC maps to exactly one Cloudflare tunnel

#### Scenario: User learns constraint rationale
- **WHEN** user reads one-tunnel-per-device explanation
- **THEN** documentation describes how this enforces clear infrastructure mapping and prevents configuration ambiguity

#### Scenario: User handles multiple service requirements
- **WHEN** user needs multiple services on one device
- **THEN** documentation shows how to define multiple TunnelService entries within a single CloudflareTunnel

### Requirement: Port range validation rule explanation
The documentation SHALL explain port range validation (1-65535) with common port examples and protocol implications.

#### Scenario: User validates service port
- **WHEN** user configures service port
- **THEN** documentation shows valid range (1-65535) and explains reserved ports (1-1023 require root)

#### Scenario: User selects appropriate port
- **WHEN** user needs port for service
- **THEN** documentation provides common port examples (80/http, 443/https, 8080/alt-http, 8096/Jellyfin)

### Requirement: Cross-provider consistency validation explanation
The documentation SHALL explain MAC consistency validation between UniFi and Cloudflare configurations.

#### Scenario: User understands MAC consistency requirement
- **WHEN** user reads cross-provider validation
- **THEN** documentation explains that every Cloudflare tunnel MAC MUST exist in UniFi device endpoints

#### Scenario: User fixes MAC mismatch error
- **WHEN** user encounters MAC consistency error
- **THEN** documentation shows available UniFi MACs and instructions to add missing device or correct tunnel MAC
