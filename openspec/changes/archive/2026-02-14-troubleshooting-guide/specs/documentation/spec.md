## MODIFIED Requirements

### Requirement: Troubleshooting Section

The README SHALL include a troubleshooting section covering common deployment issues with links to the comprehensive troubleshooting guide.

#### Scenario: Common deployment issues
- **WHEN** users encounter problems during deployment
- **THEN** documentation MUST cover:
  - KCL validation errors (MAC format, missing fields)
  - Terraform provider authentication issues
  - UniFi controller connection problems
  - Cloudflare API token permissions
  - DNS resolution not working
  - Tunnel connectivity issues
  - local_service_url causing DNS loops

#### Scenario: Link to comprehensive troubleshooting guide
- **WHEN** users need more detailed troubleshooting information
- **THEN** the troubleshooting section MUST include a link to `docs/troubleshooting.md` with description of available content

#### Scenario: Cross-references from related documentation
- **WHEN** users read security.md, state-management.md, or dagger-reference.md
- **THEN** relevant sections MUST include links to the troubleshooting guide for error scenarios
