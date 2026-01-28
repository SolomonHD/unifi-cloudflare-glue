# Capability: Example Configuration

## Description
Complete KCL configuration file that demonstrates a realistic homelab media stack setup with all three service distribution patterns.

## ADDED Requirements

### Requirement: Media Server Entity Definition

The KCL configuration SHALL define a media server entity with dual NICs as the foundation for all service configurations.

#### Scenario: Single device hosts all services
Given a user wants to configure a homelab media server
When they define the media server entity
Then it must include:
- friendly_hostname: "media-server"
- domain: "internal.lan"
- At least two endpoints (management and media NICs)

#### Scenario: Dual NIC configuration
Given a media server has multiple network interfaces
When endpoints are defined
Then they must include:
- Management NIC with MAC address placeholder
- Media NIC (10GbE) with MAC address placeholder
- Descriptive nic_name for each endpoint

### Requirement: UniFi-Only Services Configuration

The KCL configuration SHALL define internal automation services (*arr stack) that are only accessible within the internal network.

#### Scenario: Internal automation services
Given services that should only be accessible internally
When configuring Sonarr, Radarr, and Prowlarr
Then they must have:
- distribution: "unifi_only"
- internal_hostname in format "servicename.internal.lan"
- No public_hostname defined
- Standard ports (Sonarr: 8989, Radarr: 7878, Prowlarr: 9696)

### Requirement: Cloudflare-Only Services Configuration

The KCL configuration SHALL define external-facing services that are only accessible through Cloudflare Tunnel.

#### Scenario: External document and photo management
Given services that should only be accessible externally
When configuring Paperless-ngx and Immich
Then they must have:
- distribution: "cloudflare_only"
- public_hostname in format "service.<your-domain>.com"
- internal_hostname for local_service_url construction
- Standard ports (Paperless: 8000, Immich: 2283)

### Requirement: Dual-Exposure Services Configuration

The KCL configuration SHALL define services accessible both internally and externally through both UniFi DNS and Cloudflare Tunnel.

#### Scenario: Media streaming with internal and external access
Given services that need both internal and external access
When configuring Jellyfin and Jellyseerr
Then they must have:
- distribution: "both"
- internal_hostname for UniFi DNS (e.g., "jellyfin.internal.lan")
- public_hostname for Cloudflare (e.g., "media.<your-domain>.com")
- Correct ports (Jellyfin: 8096, Jellyseerr: 5055)

### Requirement: Placeholder Values

The KCL configuration SHALL use consistent placeholder values that users can easily identify and replace.

#### Scenario: User customization required
Given the example is intended for users to adapt
When placeholder values are needed
Then they must use consistent format:
- `<your-domain>` for Cloudflare zone
- `<your-account-id>` for Cloudflare account
- `<mac-management>` for management NIC MAC
- `<mac-media>` for media NIC MAC
- Comments explaining each placeholder

### Requirement: MAC Address Handling

The KCL configuration SHALL demonstrate MAC address normalization and proper usage patterns.

#### Scenario: MAC address normalization demonstration
Given MAC addresses can be provided in multiple formats
When the configuration includes MAC addresses
Then it must demonstrate:
- Acceptable formats (colon, hyphen, no separator)
- Normalization to lowercase colon format in output
- Consistent MAC address usage as dictionary keys

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## Cross-References

- Relates to: 007-kcl-integration-validation (generators)
- Used by: 008-terraform-unifi-dns-module, 009-terraform-cloudflare-tunnel-module
