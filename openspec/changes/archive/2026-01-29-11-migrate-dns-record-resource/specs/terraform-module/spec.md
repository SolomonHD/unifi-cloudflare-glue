# terraform-module Specification - DNS Record Migration

## Purpose

Specification for migrating the `cloudflare_record` resource to `cloudflare_dns_record` for Cloudflare provider v5.x compatibility.

## MODIFIED Requirements

### Requirement: Terraform Cloudflare Tunnel Module - DNS Record Resource

The Terraform module SHALL create a `cloudflare_dns_record` resource for each service using the v5.x schema.

#### Scenario: Resource uses correct v5.x resource type

Given: The cloudflare-tunnel module's `main.tf` file
When: Inspecting the DNS record resource
Then: The resource type SHALL be `cloudflare_dns_record`
And: It SHALL NOT be `cloudflare_record`

#### Scenario: DNS record uses content attribute instead of value

Given: A `cloudflare_dns_record` resource defining a CNAME record
When: Specifying the record value
Then: The attribute SHALL be `content`
And: It SHALL NOT use `value`
And: The content SHALL reference the tunnel ID: `${cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id}.cfargotunnel.com`

#### Scenario: DNS record includes required TTL attribute

Given: A `cloudflare_dns_record` resource
When: Configuring the record
Then: The `ttl` attribute SHALL be present
And: The value SHALL be `1` (automatic TTL)

#### Scenario: For_each creates unique keys for each service

Given: Multiple tunnels with multiple services
When: Creating DNS records
Then: The `for_each` SHALL use `setproduct` to create unique keys
And: Each key SHALL be formatted as `"${pair[0]}-${pair[1].index}"`
And: The keys SHALL map to objects with `mac` and `hostname` fields

#### Scenario: Zone ID references data source

Given: A `cloudflare_dns_record` resource
When: Setting the zone_id
Then: It SHALL reference `data.cloudflare_zone.this.id`

#### Scenario: Name uses hostname from for_each

Given: A `cloudflare_dns_record` resource
When: Setting the name
Then: It SHALL use `each.value.hostname`
And: The hostname SHALL be the public_hostname from the service configuration

#### Scenario: Type is CNAME for all records

Given: A `cloudflare_dns_record` resource
When: Setting the type
Then: The type SHALL be `"CNAME"`

#### Scenario: Proxied is enabled

Given: A `cloudflare_dns_record` resource
When: Setting the proxied attribute
Then: The value SHALL be `true`
And: Cloudflare proxying SHALL be enabled for all records

#### Scenario: Tunnel ID references updated resource

Given: A `cloudflare_dns_record` resource
When: Referencing the tunnel ID in content
Then: It SHALL reference `cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id`
And: It SHALL NOT reference the deprecated `cloudflare_tunnel` resource

## REMOVED Requirements

The following requirements from previous specs are superseded by this migration:

- ~~`cloudflare_record` resource type~~ → Use `cloudflare_dns_record`
- ~~`value` attribute~~ → Use `content` attribute
- ~~Optional TTL~~ → TTL is now required (use `1` for automatic)
