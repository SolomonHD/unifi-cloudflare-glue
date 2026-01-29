# terraform-module Specification - Tunnel Config Migration

## Purpose

Specification for migrating the `cloudflare_tunnel_config` resource to `cloudflare_zero_trust_tunnel_cloudflared_config` for Cloudflare provider v5.x compatibility.

## MODIFIED Requirements

### Requirement: Terraform Cloudflare Tunnel Module - Tunnel Config Resource

The Terraform module SHALL create a `cloudflare_zero_trust_tunnel_cloudflared_config` resource for each tunnel with ingress rules using the v5.x schema.

#### Scenario: Resource uses correct v5.x resource type

Given: The cloudflare-tunnel module's `main.tf` file
When: Inspecting the tunnel config resource
Then: The resource type SHALL be `cloudflare_zero_trust_tunnel_cloudflared_config`
And: It SHALL NOT be `cloudflare_tunnel_config`

#### Scenario: Config uses attribute syntax instead of block

Given: A `cloudflare_zero_trust_tunnel_cloudflared_config` resource
When: Defining the config
Then: The config SHALL use attribute syntax: `config = { ... }`
And: It SHALL NOT use block syntax: `config { ... }`

#### Scenario: Ingress rules use list syntax with for expression

Given: A tunnel with multiple services configured
When: Generating ingress rules
Then: The ingress field SHALL be a list constructed with a for expression
And: It SHALL NOT use `dynamic "ingress_rule"` blocks

#### Scenario: Service hostname mapping in for expression

Given: A service with public_hostname "media.example.com"
When: Constructing the ingress list
Then: The for expression SHALL map `svc.public_hostname` to the hostname field

#### Scenario: Service URL mapping in for expression

Given: A service with local_service_url "http://jellyfin.internal.lan:8096"
When: Constructing the ingress list
Then: The for expression SHALL map `svc.local_service_url` to the service field

#### Scenario: Origin request uses conditional expression

Given: A service with no_tls_verify set to true
When: Constructing the ingress entry
Then: The origin_request field SHALL use a conditional expression:
  ```
  origin_request = svc.no_tls_verify ? { no_tls_verify = true } : null
  ```
And: It SHALL NOT use `dynamic "origin_request"` blocks

#### Scenario: Origin request null when not needed

Given: A service with no_tls_verify set to false
When: Constructing the ingress entry
Then: The origin_request field SHALL be `null`
And: It SHALL NOT include an empty origin_request object

#### Scenario: Catch-all 404 rule preserved at end

Given: A tunnel config with service ingress rules
When: The ingress list is constructed
Then: A final catch-all rule SHALL be appended using `concat()`
And: The catch-all SHALL be `[{ service = "http_status:404" }]`
And: It SHALL be the last element in the ingress list

#### Scenario: Concat pattern for ingress list construction

Given: Service ingress rules and a catch-all rule
When: Constructing the complete ingress list
Then: The config SHALL use `concat()` to combine service rules and catch-all:
  ```
  ingress = concat(
    [for svc in each.value.services : { ... }],
    [{ service = "http_status:404" }]
  )
  ```

#### Scenario: Tunnel ID references updated resource

Given: A `cloudflare_zero_trust_tunnel_cloudflared_config` resource
When: Referencing the tunnel ID
Then: It SHALL reference `cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id`
And: The tunnel_id attribute SHALL be properly set

#### Scenario: Account ID passed correctly

Given: A `cloudflare_zero_trust_tunnel_cloudflared_config` resource
When: Configuring the resource
Then: The account_id SHALL be set to `local.effective_config.account_id`

#### Scenario: For_each iteration over tunnels

Given: A `cloudflare_zero_trust_tunnel_cloudflared_config` resource
When: Defining the resource
Then: It SHALL use `for_each = local.effective_config.tunnels`
And: Each tunnel SHALL get its own config resource

#### Scenario: Handle empty services list

Given: A tunnel with no services configured
When: The config is generated
Then: The ingress list SHALL contain only the catch-all 404 rule
And: The concat SHALL handle empty service lists gracefully

## REMOVED Requirements

The following requirements from the base terraform-module spec are superseded by this migration:

- ~~`cloudflare_tunnel_config` resource type~~ → Use `cloudflare_zero_trust_tunnel_cloudflared_config`
- ~~Block syntax for config~~ → Use attribute syntax
- ~~Dynamic blocks for ingress_rule~~ → Use for expressions
- ~~Dynamic blocks for origin_request~~ → Use conditional expressions
