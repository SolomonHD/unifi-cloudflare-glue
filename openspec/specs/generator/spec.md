# generator Specification

## Purpose
TBD - created by archiving change 005-kcl-unifi-generator. Update Purpose after archive.
## Requirements
### Requirement: Generator Function

The generator SHALL provide a `generate_unifi_config()` function that accepts a `UniFiConfig` and returns a dictionary suitable for JSON serialization.

#### Scenario: Basic Generator Invocation
Given a valid `UniFiConfig` instance  
When `generate_unifi_config(config)` is called  
Then it returns a dictionary with `devices` and `default_domain` keys

#### Scenario: Empty Configuration
Given a `UniFiConfig` with empty devices list  
When `generate_unifi_config(config)` is called  
Then it returns `{"devices": [], "default_domain": "internal.lan"}`

### Requirement: Entity to Device Transformation

The generator SHALL transform each `UniFiEntity` into a device record.

#### Scenario: Single Entity Transformation
Given a `UniFiEntity` with:
- `friendly_hostname = "media-server"`
- `domain = "internal.lan"`
- `service_cnames = ["storage.internal.lan"]`
- One endpoint with MAC `aa:bb:cc:dd:ee:ff`  
When the entity is transformed  
Then the output contains a device with matching fields

#### Scenario: Multiple Entities
Given a `UniFiConfig` with two `UniFiEntity` objects  
When `generate_unifi_config()` is called  
Then the output `devices` array contains both entities in order

### Requirement: MAC Address Normalization

The generator SHALL normalize all MAC addresses to lowercase colon format (`aa:bb:cc:dd:ee:ff`).

#### Scenario: Colon-Separated MAC
Given an endpoint with `mac_address = "AA:BB:CC:DD:EE:FF"`  
When transformed  
Then output contains `mac_address = "aa:bb:cc:dd:ee:ff"`

#### Scenario: Hyphen-Separated MAC
Given an endpoint with `mac_address = "AA-BB-CC-DD-EE-FF"`  
When transformed  
Then output contains `mac_address = "aa:bb:cc:dd:ee:ff"`

#### Scenario: No-Separator MAC
Given an endpoint with `mac_address = "AABBCCDDEEFF"`  
When transformed  
Then output contains `mac_address = "aa:bb:cc:dd:ee:ff"`

#### Scenario: Mixed Case MAC
Given an endpoint with `mac_address = "Ab:Cd:Ef:01:23:45"`  
When transformed  
Then output contains `mac_address = "ab:cd:ef:01:23:45"`

### Requirement: Service Distribution Filtering

The generator SHALL only include services where `distribution != "cloudflare_only"`.

#### Scenario: Unifi-Only Service
Given a service with `distribution = "unifi_only"`  
When device is transformed  
Then the service CNAMEs are included in output

#### Scenario: Both Distribution Service
Given a service with `distribution = "both"`  
When device is transformed  
Then the service CNAMEs are included in output

#### Scenario: Cloudflare-Only Service Exclusion
Given a service with `distribution = "cloudflare_only"`  
When device is transformed  
Then the service CNAMEs are NOT included in output

### Requirement: CNAME Generation

The generator SHALL correctly generate CNAMEs at both device and NIC levels.

#### Scenario: Device-Level CNAMEs
Given a `UniFiEntity` with `service_cnames = ["backup.internal.lan", "storage.internal.lan"]`  
When transformed  
Then the device record contains `service_cnames` with both entries

#### Scenario: NIC-Level CNAMEs
Given a `UniFiEndpoint` with `service_cnames = ["nas-eth0.internal.lan"]`  
When transformed  
Then the NIC record contains `service_cnames` with the entry

#### Scenario: Empty CNAMEs
Given a `UniFiEntity` with `service_cnames = []`  
When transformed  
Then the device record contains empty `service_cnames` array

### Requirement: Optional Field Handling

The generator SHALL handle optional fields gracefully.

#### Scenario: Missing NIC Name
Given an endpoint without `nic_name`  
When transformed  
Then the NIC record omits the `nic_name` field (not included in JSON)

#### Scenario: Missing Service CNAMEs
Given an entity with no `service_cnames` defined  
When transformed  
Then the device record includes empty `service_cnames` array

### Requirement: JSON Output Format

The generator SHALL produce JSON that matches the UniFi Terraform module input schema.

#### Scenario: Valid JSON Structure
Given a valid `UniFiConfig`  
When `generate_unifi_config()` output is serialized to JSON  
Then the JSON is valid and can be parsed

#### Scenario: Complete Output Structure
Given a `UniFiConfig` with at least one device  
When output is generated  
Then the JSON contains:
```json
{
  "devices": [{
    "friendly_hostname": "...",
    "domain": "...",
    "service_cnames": [...],
    "nics": [{
      "mac_address": "...",
      "nic_name?": "...",
      "service_cnames": [...]
    }]
  }],
  "default_domain": "..."
}
```

### Requirement: Default Domain Inclusion

The generator SHALL include the `default_domain` from `UniFiConfig` in the output.

#### Scenario: Default Domain Output
Given a `UniFiConfig` with `default_domain = "home.local"`  
When `generate_unifi_config()` is called  
Then the output contains `default_domain: "home.local"`

