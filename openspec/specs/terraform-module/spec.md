# terraform-module Specification

## Purpose
TBD - created by archiving change 009-terraform-cloudflare-tunnel-module. Update Purpose after archive.
## Requirements
### Requirement: Terraform Cloudflare Tunnel Module - Input Variables

The Terraform module SHALL define a complete input variable schema matching the KCL Cloudflare generator output format.

#### Scenario: Config variable accepts Cloudflare configuration
Given a KCL-generated configuration with zone_name, account_id, and tunnels
When the `config` variable is defined as an object type
Then it SHALL accept the nested structure of tunnels keyed by MAC address

#### Scenario: Tunnel type includes required fields
Given a tunnel configuration object
When the tunnel type is defined
Then it SHALL include tunnel_name (string), mac_address (string), and services (list)

#### Scenario: Service type includes required fields
Given a service configuration object
When the service type is defined
Then it SHALL include public_hostname (string), local_service_url (string), and no_tls_verify (optional bool, default false)

#### Scenario: Zone name validation ensures non-empty value
Given a config with empty zone_name
When the variable is validated
Then it SHALL reject with a validation error

#### Scenario: Account ID validation ensures non-empty value
Given a config with empty account_id
When the variable is validated
Then it SHALL reject with a validation error

#### Scenario: DNS loop prevention validation
Given a local_service_url containing the zone_name
When the config variable is validated
Then it SHALL reject with a validation error to prevent DNS resolution loops

### Requirement: Terraform Cloudflare Tunnel Module - Zone Data Source

The Terraform module SHALL query the existing Cloudflare Zone using a data source.

#### Scenario: Query Cloudflare Zone by name
Given a zone_name from the configuration
When the `cloudflare_zone` data source queries Cloudflare
Then it SHALL return the zone details including zone_id

#### Scenario: Fail when zone does not exist
Given a zone_name that does not exist in Cloudflare
When the data source queries Cloudflare
Then Terraform SHALL fail with a clear error message indicating the zone was not found

#### Scenario: Extract zone_id for resource creation
Given a successful zone data source query
When resources are created
Then the zone_id SHALL be available for use in tunnel and record resources

### Requirement: Terraform Cloudflare Tunnel Module - Tunnel Resource Creation

The Terraform module SHALL create a `cloudflare_tunnel` resource for each MAC address in the configuration.

#### Scenario: Create tunnel for each MAC address
Given a tunnels map with MAC addresses as keys
When Terraform applies
Then a `cloudflare_tunnel` resource SHALL be created for each entry

#### Scenario: Tunnel name matches configuration
Given a tunnel configuration with tunnel_name "home-server"
When the tunnel resource is created
Then the tunnel name in Cloudflare SHALL be "home-server"

#### Scenario: Tunnel uses correct account ID
Given an account_id in the configuration
When the tunnel resource is created
Then it SHALL be created in the specified Cloudflare account

#### Scenario: Capture tunnel ID and token
Given a successfully created tunnel
When the resource is created
Then the tunnel ID and tunnel token SHALL be captured for outputs

### Requirement: Terraform Cloudflare Tunnel Module - Tunnel Config Resource

The Terraform module SHALL create a `cloudflare_tunnel_config` resource for each tunnel with ingress rules.

#### Scenario: Create tunnel config for each tunnel
Given a tunnel resource
When Terraform applies
Then a `cloudflare_tunnel_config` resource SHALL be created for that tunnel

#### Scenario: Generate ingress rules from services
Given a tunnel with multiple services configured
When the tunnel_config is created
Then ingress rules SHALL be generated for each service

#### Scenario: Map public_hostname to ingress hostname
Given a service with public_hostname "media.example.com"
When the ingress rule is created
Then the hostname field SHALL be "media.example.com"

#### Scenario: Map local_service_url to ingress service
Given a service with local_service_url "http://jellyfin.internal.lan:8096"
When the ingress rule is created
Then the service field SHALL be "http://jellyfin.internal.lan:8096"

#### Scenario: Set no_tls_verify on ingress rule
Given a service with no_tls_verify set to true
When the ingress rule is created
Then the origin_request.no_tls_verify field SHALL be set to true

#### Scenario: Add catch-all 404 rule
Given a tunnel config with service ingress rules
When the tunnel_config is created
Then a final catch-all rule SHALL be added that returns HTTP 404

#### Scenario: Handle empty services list
Given a tunnel with no services configured
When the tunnel_config is created
Then only the catch-all 404 rule SHALL be present

### Requirement: Terraform Cloudflare Tunnel Module - DNS Record Creation

The Terraform module SHALL create CNAME records for each service's public_hostname pointing to the tunnel.

#### Scenario: Create CNAME for each public_hostname
Given a tunnel with services having public_hostnames
When Terraform applies
Then a `cloudflare_record` CNAME SHALL be created for each unique public_hostname

#### Scenario: CNAME target points to tunnel
Given a tunnel with ID "abcd1234-..."
When the CNAME record is created
Then the target SHALL be "abcd1234-....cfargotunnel.com"

#### Scenario: CNAME records are proxied
Given a CNAME record being created
When the record is configured
Then the proxied field SHALL be set to true

#### Scenario: CNAME uses correct zone
Given a zone_id from the data source
When CNAME records are created
Then they SHALL be created in that zone

### Requirement: Terraform Cloudflare Tunnel Module - Outputs

The Terraform module SHALL provide outputs exposing tunnel IDs, tokens, credentials, and public hostnames.

#### Scenario: Output tunnel_ids map
Given tunnels created for MAC addresses
When the module completes
Then the `tunnel_ids` output SHALL contain a map of MAC address to tunnel ID

#### Scenario: Output tunnel_tokens as sensitive
Given tunnels created with tokens
When the module completes
Then the `tunnel_tokens` output SHALL contain a map of MAC address to tunnel token marked as sensitive

#### Scenario: Output credentials_json as sensitive
Given tunnels created
When the module completes
Then the `credentials_json` output SHALL contain a map of MAC address to credentials file content marked as sensitive

#### Scenario: Output public_hostnames list
Given services with public_hostnames configured
When the module completes
Then the `public_hostnames` output SHALL contain a list of all created public hostnames

#### Scenario: Output zone_id
Given a successful zone data source query
When the module completes
Then the `zone_id` output SHALL contain the Cloudflare zone ID

### Requirement: Terraform Cloudflare Tunnel Module - Error Handling

The Terraform module SHALL handle edge cases gracefully without failing unnecessarily.

#### Scenario: Handle missing zone with clear error
Given a zone_name that does not exist
When Terraform applies
Then the error message SHALL clearly indicate which zone was not found

#### Scenario: Handle duplicate MAC addresses
Given multiple tunnels configured with the same MAC address
When the module processes the configuration
Then it SHALL use the first occurrence and ignore duplicates

#### Scenario: Handle duplicate public_hostnames
Given multiple services with the same public_hostname
When CNAME records are created
Then only one CNAME record SHALL be created per unique hostname

### Requirement: Terraform Cloudflare Tunnel Module - Security

The Terraform module SHALL follow security best practices for sensitive data.

#### Scenario: Tunnel tokens marked sensitive
Given tunnel tokens in outputs
When the outputs are defined
Then they SHALL have sensitive = true to prevent display in logs

#### Scenario: Credentials JSON marked sensitive
Given credentials file content in outputs
When the outputs are defined
Then they SHALL have sensitive = true to prevent display in logs

#### Scenario: No sensitive data in non-sensitive outputs
Given module outputs
When non-sensitive outputs are reviewed
Then they SHALL NOT contain tunnel tokens or credentials

### Requirement: cloudflare_token Variable Declaration

The Terraform module SHALL declare a cloudflare_token variable for Cloudflare API authentication.

#### Scenario: Variable is properly declared
Given: The cloudflare-tunnel module's `variables.tf` file
When: Inspecting the file contents
Then: The file must contain a `cloudflare_token` variable declaration

#### Scenario: Variable is marked sensitive
Given: The `cloudflare_token` variable declaration
When: Reviewing the variable configuration
Then: The variable must have `sensitive = true` to prevent value logging

#### Scenario: Variable has clear documentation
Given: The `cloudflare_token` variable declaration
When: Reading the description
Then: The description must specify required permissions:
  - Zone:Read
  - DNS:Edit
  - Cloudflare Tunnel:Edit

#### Scenario: Variable is required
Given: The `cloudflare_token` variable declaration
When: Attempting to use the module without providing the token
Then: Terraform must require the variable (no default value)

### Requirement: HCL Formatting Compliance

The variable declaration SHALL follow Terraform HCL formatting conventions.

#### Scenario: Variable follows Terraform conventions
Given: The added `cloudflare_token` variable
When: Running `terraform fmt`
Then: No formatting changes are required

