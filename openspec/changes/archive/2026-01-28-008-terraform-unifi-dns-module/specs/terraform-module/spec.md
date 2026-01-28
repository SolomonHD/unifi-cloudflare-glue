## ADDED Requirements

### Requirement: Terraform UniFi DNS Module - Input Variables

The Terraform module SHALL define a complete input variable schema matching the KCL UniFi generator output format.

#### Scenario: Config variable accepts device configuration
Given a KCL-generated configuration with devices, domain, and controller settings
When the `config` variable is defined as an object type
Then it SHALL accept the nested structure of devices, nics, and service_cnames

#### Scenario: Device type includes required fields
Given a device configuration object
When the device type is defined
Then it SHALL include friendly_hostname (string), domain (string), service_cnames (list), and nics (list)

#### Scenario: NIC type includes required fields
Given a NIC configuration object
When the NIC type is defined
Then it SHALL include mac_address (string), nic_name (optional string), and service_cnames (optional list)

#### Scenario: MAC address validation accepts multiple formats
Given MAC addresses in formats "aa:bb:cc:dd:ee:ff", "aa-bb-cc-dd-ee-ff", or "aabbccddeeff"
When the MAC address variable is validated
Then all formats SHALL be accepted and normalized internally

#### Scenario: Hostname validation enforces DNS label format
Given a friendly_hostname value
When the hostname is validated
Then it SHALL reject values containing underscores, spaces, or special characters

#### Scenario: Device must have at least one NIC
Given a device configuration with empty nics list
When the config variable is validated
Then it SHALL reject with a validation error

### Requirement: Terraform UniFi DNS Module - Data Source Queries

The Terraform module SHALL query the UniFi Controller for device IP addresses by MAC address using data sources.

#### Scenario: Query UniFi Controller by MAC address
Given a MAC address from the configuration
When the `unifi_user` data source queries the controller
Then it SHALL return the device details including assigned IP address

#### Scenario: Normalize MAC addresses for lookups
Given MAC addresses in various input formats
When the data source performs lookups
Then they SHALL be normalized to lowercase colon format (aa:bb:cc:dd:ee:ff)

#### Scenario: Track missing MAC addresses
Given a MAC address not found in the UniFi Controller
When the data source query executes
Then the missing MAC SHALL be tracked in the missing_devices list

#### Scenario: Build MAC to IP mapping
Given multiple MAC addresses from the configuration
When all data source queries complete
Then a map of MAC address to assigned IP SHALL be created

### Requirement: Terraform UniFi DNS Module - A-Record Creation

The Terraform module SHALL create A-records in UniFi DNS for each device's friendly_hostname pointing to the device's IP address(es).

#### Scenario: Create A-record for single-NIC device
Given a device with one NIC and friendly_hostname "media-server"
When the A-record resource is created
Then it SHALL create a DNS record for "media-server.internal.lan" pointing to the NIC's IP

#### Scenario: Create round-robin A-records for multi-NIC device
Given a device with multiple NICs (eth0, eth1) and friendly_hostname "backup-server"
When the A-record resources are created
Then multiple A-records SHALL be created for "backup-server.internal.lan" pointing to each NIC's IP

#### Scenario: Use device-specific domain for FQDN
Given a device with domain "home.local"
When the A-record is created
Then the FQDN SHALL use "home.local" instead of the default_domain

#### Scenario: Skip A-records for missing devices
Given a device whose MAC address is not found in UniFi
When the A-record would be created
Then it SHALL be skipped and the MAC added to missing_devices output

### Requirement: Terraform UniFi DNS Module - CNAME Creation

The Terraform module SHALL create CNAME records in UniFi DNS for service hostnames pointing to the device's friendly_hostname FQDN.

#### Scenario: Create CNAME for device-level service_cnames
Given a device with service_cnames ["storage.internal.lan"]
When CNAME resources are created
Then a CNAME SHALL be created for "storage.internal.lan" pointing to the device FQDN

#### Scenario: Create CNAME for NIC-level service_cnames
Given a NIC with service_cnames ["nas-eth0.internal.lan"]
When CNAME resources are created
Then a CNAME SHALL be created for "nas-eth0.internal.lan" pointing to the device FQDN

#### Scenario: CNAME target is device FQDN
Given a device with friendly_hostname "media-server" and domain "internal.lan"
When CNAMEs are created for its services
Then they SHALL point to "media-server.internal.lan"

#### Scenario: Skip empty CNAME entries
Given a service_cnames list containing empty strings or null values
When CNAME resources are created
Then empty entries SHALL be filtered out and not create records

### Requirement: Terraform UniFi DNS Module - Outputs

The Terraform module SHALL provide outputs exposing created records, missing devices, and device IP mappings.

#### Scenario: Output A-records map
Given A-records created for devices
When the module completes
Then the `a_records` output SHALL contain a map of hostname to IP addresses

#### Scenario: Output CNAME records map
Given CNAME records created for services
When the module completes
Then the `cname_records` output SHALL contain a map of CNAME to target FQDN

#### Scenario: Output missing devices list
Given MAC addresses not found in UniFi Controller
When the module completes
Then the `missing_devices` output SHALL contain the list of missing MAC addresses

#### Scenario: Output device IPs map
Given devices found in UniFi Controller
When the module completes
Then the `device_ips` output SHALL contain a map of MAC address to assigned IP

### Requirement: Terraform UniFi DNS Module - Error Handling

The Terraform module SHALL handle edge cases gracefully without failing unnecessarily.

#### Scenario: Missing MAC addresses don't cause failure
Given a configuration with MAC addresses not present in UniFi
When the module runs with strict_mode = false (default)
Then it SHALL complete successfully with warnings in missing_devices output

#### Scenario: Strict mode causes failure on missing MACs
Given a configuration with MAC addresses not present in UniFi
When the module runs with strict_mode = true
Then it SHALL fail with an error listing missing MAC addresses

#### Scenario: Handle devices with no IP assigned
Given a device found in UniFi but with no IP address assigned
When processing the device
Then it SHALL be treated as missing and added to missing_devices

#### Scenario: Handle duplicate MAC addresses
Given multiple devices configured with the same MAC address
When the module processes the configuration
Then it SHALL use the first occurrence and log a warning

### Requirement: Terraform UniFi DNS Module - Provider Integration

The Terraform module SHALL integrate correctly with the UniFi provider.

#### Scenario: Use paultyng/unifi provider
Given the module configuration
When providers are declared
Then it SHALL use the "paultyng/unifi" provider version ~> 0.41

#### Scenario: Support provider authentication via environment variables
Given UniFi Controller credentials
When the provider is configured
Then it SHALL support authentication via UNIFI_USERNAME and UNIFI_PASSWORD environment variables

#### Scenario: Support site-specific configuration
Given devices in different UniFi sites
When DNS records are created
Then they SHALL be created in the appropriate site (default: "default")
