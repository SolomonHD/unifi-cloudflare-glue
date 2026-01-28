## MODIFIED Requirements

### Requirement: Provider Source Migration

The Terraform module SHALL use the `filipowm/unifi` provider instead of `paultyng/unifi`.

#### Scenario: versions.tf references filipowm/unifi provider
Given the existing versions.tf file with paultyng/unifi provider
When the provider source is updated
Then it SHALL reference `filipowm/unifi` instead of `paultyng/unifi`

#### Scenario: Provider version constraint updated
Given the versions.tf file
When the provider version constraint is set
Then it SHALL use ~> 1.0 or the latest stable version of filipowm/unifi

### Requirement: DNS Resource Migration

The module SHALL use dedicated DNS record resources instead of unifi_user workarounds.

#### Scenario: Replace unifi_user with DNS record resources
Given the existing main.tf using `unifi_user` resources with `local_dns_record`
When DNS records are created
Then they SHALL use the provider's native DNS record resource type (e.g., `unifi_dns_record`)

#### Scenario: A-records for device hostnames
Given a device with friendly_hostname and assigned IP
When DNS resources are created
Then an A-record SHALL be created mapping the hostname to the device's IP

#### Scenario: CNAME records for service aliases
Given a device with service_cnames configured
When DNS resources are created
Then CNAME records SHALL be created if the provider supports them

#### Scenario: Remove allow_existing workaround
Given the current implementation uses `allow_existing = true` on unifi_user resources
When migrating to new provider
Then this workaround SHALL be removed as it's specific to unifi_user

### Requirement: Data Source Migration

The module SHALL continue to query UniFi Controller for device IPs using the new provider's data sources.

#### Scenario: Query devices by MAC address
Given MAC addresses from configuration
When querying the UniFi Controller
Then the appropriate filipowm/unifi data source SHALL be used

#### Scenario: MAC address normalization preserved
Given MAC addresses in various formats (colon, hyphen, no separator)
When processing lookups
Then they SHALL be normalized to lowercase colon format as before

### Requirement: Output Compatibility

The module outputs SHALL maintain backward compatibility with the existing interface.

#### Scenario: dns_records output structure preserved
Given DNS records are created with new provider
When the module outputs are generated
Then `dns_records` SHALL maintain the same structure (map of hostname to FQDN)

#### Scenario: device_ips output preserved
Given device IP mappings from UniFi
When outputs are generated
Then `device_ips` SHALL maintain the same structure (map of MAC to IP)

#### Scenario: missing_devices output preserved
Given MAC addresses not found in UniFi
When outputs are generated
Then `missing_devices` SHALL continue to list missing MAC addresses

### Requirement: Documentation Update

The module documentation SHALL be updated to reference the new provider.

#### Scenario: README references correct provider
Given the README.md file
When provider information is documented
Then it SHALL reference `filipowm/unifi` and its documentation

#### Scenario: Provider authentication documented
Given the new provider may have different authentication
When documentation is updated
Then authentication methods SHALL be documented with correct environment variables

#### Scenario: Requirements table updated
Given the requirements section in README
When provider versions are listed
Then it SHALL show `filipowm/unifi` with the new version constraint

### Requirement: Input Interface Stability

The module SHALL maintain the existing input variable schema for backward compatibility.

#### Scenario: Config variable unchanged
Given existing configurations using the module
When the provider is migrated
Then the `config` variable structure SHALL remain unchanged

#### Scenario: strict_mode behavior preserved
Given the strict_mode variable
When the module runs
Then it SHALL continue to control whether missing MACs cause failure

### Requirement: Validation Requirements

The module SHALL pass Terraform validation after migration.

#### Scenario: terraform validate passes
Given the migrated module
When `terraform validate` is executed
Then it SHALL complete with no errors

#### Scenario: terraform fmt compliance
Given the migrated module files
When `terraform fmt` is run
Then all files SHALL be properly formatted
