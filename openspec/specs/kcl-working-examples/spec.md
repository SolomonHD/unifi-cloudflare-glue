## ADDED Requirements

### Requirement: Single service example
The documentation SHALL provide a complete working example of a device with one service accessible both internally and externally.

#### Scenario: User copies single service example
- **WHEN** user needs starting point for simple configuration
- **THEN** example includes complete main.k with Entity, Endpoint, Service using distribution="both", UniFi and Cloudflare configs

#### Scenario: User validates single service example
- **WHEN** user runs example configuration
- **THEN** example validates successfully with kcl run main.k and generates valid JSON output

#### Scenario: User understands single service example
- **WHEN** user reads single service example README
- **THEN** documentation explains each schema usage, what gets created in UniFi and Cloudflare, and how to customize

### Requirement: Multiple services example
The documentation SHALL provide a complete working example of a device hosting multiple services with different distribution strategies.

#### Scenario: User copies multiple services example
- **WHEN** user needs pattern for complex device
- **THEN** example includes Entity with 3+ Services using varied distributions (unifi_only, cloudflare_only, both)

#### Scenario: User learns service organization
- **WHEN** user reads multiple services example
- **THEN** documentation shows how to organize admin, internal, and public services on same device

#### Scenario: User customizes multiple services
- **WHEN** user adapts example to their services
- **THEN** README provides guidance on adding/removing services and choosing appropriate distribution

### Requirement: Internal-only services example
The documentation SHALL provide a complete working example of services accessible only within local network.

#### Scenario: User copies internal-only example
- **WHEN** user needs internal-only configuration
- **THEN** example includes complete UniFi config with Services using distribution="unifi_only" and no Cloudflare tunnels

#### Scenario: User validates internal-only example
- **WHEN** user runs internal-only example
- **THEN** generates UniFi DNS configuration without Cloudflare tunnel entries

#### Scenario: User understands internal-only security
- **WHEN** user reads internal-only example README
- **THEN** documentation explains network boundary, use cases (management interfaces, internal tools), and verification steps

### Requirement: External-only services example
The documentation SHALL provide a complete working example of services accessible only via Cloudflare tunnel.

#### Scenario: User copies external-only example
- **WHEN** user needs external-only configuration
- **THEN** example includes Cloudflare tunnels with Services using distribution="cloudflare_only" and minimal UniFi config

#### Scenario: User validates external-only example
- **WHEN** user runs external-only example
- **THEN** generates Cloudflare tunnel configuration without UniFi DNS entries for public services

#### Scenario: User understands external routing
- **WHEN** user reads external-only example README
- **THEN** documentation explains how Cloudflare routes to internal hostnames, DNS resolution flow, and troubleshooting

### Requirement: Example validation commands
All examples SHALL include validation commands and expected output for verification.

#### Scenario: User validates example syntax
- **WHEN** user runs example validation
- **THEN** example README shows kcl run main.k command with expected success output

#### Scenario: User tests example generators
- **WHEN** user generates JSON from example
- **THEN** example README shows generator commands and sample output structure

#### Scenario: User troubleshoots example errors
- **WHEN** user encounters validation failure
- **THEN** example README links to debugging guide section relevant to error type

### Requirement: Example customization guidance
Each example SHALL include README with customization instructions and common modifications.

#### Scenario: User modifies example MAC addresses
- **WHEN** user needs to use own device MACs
- **THEN** README explains where to change MAC values and validation requirements

#### Scenario: User adapts example domains
- **WHEN** user wants to use own domains
- **THEN** README shows domain fields in config and DNS implications

#### Scenario: User adds services to example
- **WHEN** user extends example with additional services
- **THEN** README provides template Service blocks and distribution decision guide
