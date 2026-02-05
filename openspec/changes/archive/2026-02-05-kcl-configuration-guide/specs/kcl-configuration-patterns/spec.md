## ADDED Requirements

### Requirement: Single service per device pattern
The documentation SHALL provide a pattern for configuring a device with one service exposed both internally and externally.

#### Scenario: User sets up single service device
- **WHEN** user configures device with one service
- **THEN** pattern shows Entity with single Service using distribution="both", UniFi DNS record, and Cloudflare tunnel service

#### Scenario: User understands single service flow
- **WHEN** user reads single service pattern
- **THEN** documentation explains how one service creates both internal DNS (.internal.lan) and public hostname (.example.com)

### Requirement: Multiple services per device pattern
The documentation SHALL provide a pattern for configuring a device with multiple services using different distribution strategies.

#### Scenario: User configures multi-service device
- **WHEN** user sets up device with multiple services
- **THEN** pattern shows Entity with multiple Service entries using varied distributions (unifi_only, cloudflare_only, both)

#### Scenario: User learns service isolation
- **WHEN** user reads multiple services pattern
- **THEN** documentation explains how each service can independently control internal/external exposure

#### Scenario: User organizes admin interfaces
- **WHEN** user separates admin from public services
- **THEN** pattern demonstrates admin service with distribution="unifi_only" and public service with distribution="cloudflare_only"

### Requirement: Internal-only services pattern
The documentation SHALL provide a pattern for services accessible only within the local network without Cloudflare exposure.

#### Scenario: User creates internal-only configuration
- **WHEN** user configures internal-only services
- **THEN** pattern shows Services with distribution="unifi_only" and UniFi DNS records without Cloudflare tunnels

#### Scenario: User understands internal-only use cases
- **WHEN** user reads internal-only pattern
- **THEN** documentation provides examples (management interfaces, internal APIs, monitoring dashboards)

#### Scenario: User verifies no public exposure
- **WHEN** user implements internal-only pattern
- **THEN** documentation confirms services are unreachable from internet and only resolve via UniFi DNS

### Requirement: External-only services pattern
The documentation SHALL provide a pattern for services accessible only via Cloudflare tunnel without internal DNS.

#### Scenario: User creates external-only configuration
- **WHEN** user configures external-only services
- **THEN** pattern shows Services with distribution="cloudflare_only" and Cloudflare tunnel without UniFi DNS records

#### Scenario: User understands external-only use cases
- **WHEN** user reads external-only pattern
- **THEN** documentation provides examples (public-facing websites, external APIs, customer portals)

#### Scenario: User configures external-to-internal routing
- **WHEN** user implements external-only pattern
- **THEN** documentation shows how Cloudflare tunnel routes to internal hostname that resolves locally

### Requirement: Mixed distribution device pattern
The documentation SHALL provide a pattern for a single device hosting both internal-only and external-facing services.

#### Scenario: User configures mixed services
- **WHEN** user sets up device with mixed distribution
- **THEN** pattern shows one Entity with multiple Services using different distribution values

#### Scenario: User separates sensitive and public services
- **WHEN** user needs database internally and API externally
- **THEN** pattern demonstrates database Service with unifi_only and API Service with cloudflare_only on same device

### Requirement: Multi-NIC device pattern
The documentation SHALL provide a pattern for devices with multiple network interfaces each hosting different services.

#### Scenario: User configures multi-NIC device
- **WHEN** user defines device with multiple Endpoints
- **THEN** pattern shows Entity with multiple Endpoint entries, each with unique MAC and service_cnames

#### Scenario: User associates services with specific NICs
- **WHEN** user reads multi-NIC pattern
- **THEN** documentation explains how service_cnames link Services to specific network interfaces

#### Scenario: User handles interface-specific DNS
- **WHEN** user implements multi-NIC configuration
- **THEN** pattern shows how each NIC can have dedicated CNAME records for service discovery
