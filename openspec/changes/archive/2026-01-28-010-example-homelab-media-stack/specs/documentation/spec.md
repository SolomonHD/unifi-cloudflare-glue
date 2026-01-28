# Capability: Documentation

## Description
Comprehensive documentation enabling users to understand, customize, and deploy the homelab media stack example.

## ADDED Requirements

### Requirement: Overview Section

The README SHALL include an overview section that introduces the example and its purpose.

#### Scenario: Understanding the example purpose
Given a new user discovering the example
When they read the README
Then they must find:
- Clear description of what the example configures
- List of included services by category
- Architecture overview (single server, dual NIC)
- Prerequisites for deployment

### Requirement: Deployment Workflow

The README SHALL include step-by-step deployment instructions that guide users through the complete workflow.

#### Scenario: Step-by-step deployment instructions
Given a user ready to deploy the example
When they follow the documentation
Then they must have clear steps:
1. Copy/cloning the example directory
2. Customizing KCL configuration (replacing placeholders)
3. Running KCL to generate JSON files
4. Configuring Terraform credentials
5. Applying UniFi module first (for internal DNS)
6. Applying Cloudflare module (for external access)
7. Configuring cloudflared with tunnel tokens
8. Verifying service accessibility

### Requirement: Customization Guide

The README SHALL include a customization guide that explains how to adapt the example for different needs.

#### Scenario: Adapting the example for different needs
Given a user wants to modify the example
When they read the customization section
Then they must understand how to:
- Add a new service (choosing distribution type)
- Remove existing services
- Change domain names
- Add additional devices
- Modify port numbers
- Change service hostnames

### Requirement: Placeholder Reference

The README SHALL include a reference table documenting all placeholder values that need customization.

#### Scenario: Identifying all customization points
Given the example uses placeholder values
When users need to customize
Then they must find a table documenting:
| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `<your-domain>` | Cloudflare DNS zone | example.com |
| `<your-account-id>` | Cloudflare account ID | 1234567890abcdef |
| `<mac-management>` | Management NIC MAC | aa:bb:cc:dd:ee:f1 |
| `<mac-media>` | Media NIC MAC | aa:bb:cc:dd:ee:f2 |

### Requirement: Troubleshooting Section

The README SHALL include a troubleshooting section covering common deployment issues.

#### Scenario: Common deployment issues
Given users may encounter problems
When issues occur
Then documentation must cover:
- KCL validation errors (MAC format, missing fields)
- Terraform provider authentication issues
- UniFi controller connection problems
- Cloudflare API token permissions
- DNS resolution not working
- Tunnel connectivity issues
- local_service_url causing DNS loops

### Requirement: Architecture Explanation

The README SHALL explain the design decisions and architecture of the example.

#### Scenario: Understanding design decisions
Given users want to understand the architecture
When they read the documentation
Then they must find explanations for:
- Why UniFi-only for *arr stack (security)
- Why dual-exposure for Jellyfin (local performance + remote access)
- How MAC addresses link UniFi and Cloudflare configs
- Why internal domains prevent DNS loops
- How the generators filter services by distribution

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## Cross-References

- Related to: All capabilities in this change
- Influenced by: 007, 008, 009 implementation patterns
