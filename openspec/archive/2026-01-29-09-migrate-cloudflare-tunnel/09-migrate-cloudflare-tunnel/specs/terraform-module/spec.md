## MODIFIED Requirements

### Requirement: Resource Type Migration

The system SHALL migrate the `cloudflare_tunnel` resource type to `cloudflare_zero_trust_tunnel_cloudflared`.

#### Scenario: Resource definition updated
Given: A Terraform configuration with `cloudflare_tunnel` resource
When: The migration is applied
Then: The resource type is changed to `cloudflare_zero_trust_tunnel_cloudflared`
And: All other resource attributes remain unchanged

#### Scenario: Resource references updated in tunnel_config
Given: A `cloudflare_tunnel_config` resource referencing `cloudflare_tunnel.this`
When: The migration is applied
Then: The reference is updated to `cloudflare_zero_trust_tunnel_cloudflared.this`

#### Scenario: Resource references updated in DNS records
Given: A `cloudflare_record` resource referencing `cloudflare_tunnel.this[each.value.mac].id`
When: The migration is applied
Then: The reference is updated to `cloudflare_zero_trust_tunnel_cloudflared.this[each.value.mac].id`

### Requirement: Attribute Name Migration

The system SHALL rename the `secret` attribute to `tunnel_secret`.

#### Scenario: Secret attribute renamed
Given: A `cloudflare_tunnel` resource with `secret = base64encode(...)`
When: The migration is applied
Then: The attribute is renamed to `tunnel_secret`
And: The value expression remains unchanged

### Requirement: Resource Behavior Preservation

The system SHALL maintain identical resource behavior after migration.

#### Scenario: Tunnel creation behavior unchanged
Given: A valid tunnel configuration
When: The migrated resource is applied
Then: Tunnels are created with the same properties
And: The `for_each` logic remains unchanged
And: The `account_id` and `name` attributes remain unchanged

### Requirement: Validation Compliance

The migrated configuration SHALL pass Terraform validation.

#### Scenario: Terraform validate passes
Given: The migrated Terraform configuration
When: `terraform validate` is executed
Then: No errors are reported
And: No deprecation warnings for the tunnel resource

### Requirement: State Migration Path

The system SHALL provide a clear state migration path.

#### Scenario: State migration commands provided
Given: Existing Terraform state with `cloudflare_tunnel` resources
When: The migration is applied
Then: Documentation provides `terraform state mv` commands
And: The commands correctly rename the resource in state
