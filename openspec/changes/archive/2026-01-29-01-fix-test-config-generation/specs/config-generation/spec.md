## ADDED Requirements

### Requirement: Method Rename and Signature Update

The method `_generate_test_kcl_config()` SHALL be renamed to `_generate_test_configs()` and its signature updated to accept new parameters and return a dict.

#### Scenario: Method renamed for clarity
Given: The existing `_generate_test_kcl_config()` method exists in `src/main/main.py`
When: The change is implemented
Then: The method is renamed to `_generate_test_configs()`
And: All references to the old method name are updated

#### Scenario: Method signature updated with new parameter
Given: The `_generate_test_configs()` method
When: The method signature is defined
Then: It accepts `test_id: str` as the first parameter
And: It accepts `cloudflare_zone: str` as the second parameter
And: It accepts `cloudflare_account_id: str` as the third parameter
And: It returns a `dict` with "cloudflare" and "unifi" keys

#### Scenario: Call site updated in test_integration
Given: The `test_integration` method calls `_generate_test_kcl_config()` at line 888
When: The method is renamed
Then: The call site uses the new name `_generate_test_configs()`
And: The call passes `cloudflare_account_id` parameter
And: The call handles the dict return value

---

### Requirement: Cloudflare JSON Structure

The Cloudflare config JSON SHALL match the variable structure defined in `terraform/modules/cloudflare-tunnel/variables.tf`.

#### Scenario: Cloudflare config top-level structure
Given: The Cloudflare tunnel module at `terraform/modules/cloudflare-tunnel/variables.tf`
When: The Cloudflare config JSON is generated
Then: The JSON contains `zone_name` field with value from `cloudflare_zone` parameter
And: The JSON contains `account_id` field with value from `cloudflare_account_id` parameter
And: The JSON contains `tunnels` field as a map/dict

#### Scenario: Cloudflare tunnel entry structure
Given: A test configuration is being generated
When: The tunnel entry is created
Then: The tunnel is keyed by MAC address (e.g., "aa:bb:cc:dd:ee:ff")
And: The tunnel object contains `tunnel_name` field set to `f"tunnel-{test_id}"`
And: The tunnel object contains `mac_address` field set to the same MAC used as key
And: The tunnel object contains `services` field as a list

#### Scenario: Cloudflare service entry structure
Given: A tunnel entry is being created
When: The services list is populated
Then: Each service contains `public_hostname` set to `f"{test_id}.{cloudflare_zone}"`
And: Each service contains `local_service_url` set to an internal URL (e.g., `http://192.168.1.100:8080`)
And: Each service contains `no_tls_verify` set to `false`

#### Scenario: DNS loop prevention compliance
Given: A service entry is being created
When: The `local_service_url` is set
Then: The URL uses an internal domain (e.g., IP address or `.local` domain)
And: The URL does NOT contain the `cloudflare_zone` value to prevent DNS loops

---

### Requirement: UniFi JSON Structure

The UniFi config JSON SHALL match the variable structure defined in `terraform/modules/unifi-dns/variables.tf`.

#### Scenario: UniFi config top-level structure
Given: The UniFi DNS module at `terraform/modules/unifi-dns/variables.tf`
When: The UniFi config JSON is generated
Then: The JSON contains `devices` field as a list
And: The JSON contains `default_domain` field set to `"local"`
And: The JSON contains `site` field set to `"default"`

#### Scenario: UniFi device entry structure
Given: A UniFi configuration is being generated
When: The device entry is created
Then: The device contains `friendly_hostname` set to the `test_id` value
And: The device contains `domain` set to `"local"`
And: The device contains `nics` field as a list

#### Scenario: UniFi NIC entry structure
Given: A device entry is being created
When: The NICs list is populated
Then: Each NIC contains `mac_address` set to the same MAC used in Cloudflare config
And: Each NIC contains `nic_name` set to `"eth0"`

---

### Requirement: MAC Address Format and Consistency

The MAC address SHALL be consistent across both configs and match the validation regex.

#### Scenario: Consistent MAC address across configs
Given: Both Cloudflare and UniFi configs are generated
When: The MAC addresses are compared
Then: Both configs use the exact same MAC address
And: The MAC is in lowercase colon format (aa:bb:cc:dd:ee:ff)

#### Scenario: Valid MAC address format
Given: A MAC address is generated for test configurations
When: The MAC is used in either config
Then: The format matches regex: `^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$|^[0-9a-fA-F]{12}$`
And: The format uses lowercase hexadecimal characters
And: The format uses colons as separators

#### Scenario: Use recommended test MAC
Given: A test configuration needs a MAC address
When: The MAC is selected
Then: Use `aa:bb:cc:dd:ee:ff` as the default test MAC address

---

### Requirement: Test ID Usage

The test_id SHALL be used consistently across all generated identifiers.

#### Scenario: Consistent test ID in hostnames and tunnel names
Given: A `test_id` parameter (e.g., "test-abc12")
When: Hostnames and tunnel names are generated
Then: The test hostname is `f"{test_id}.{cloudflare_zone}"` (e.g., "test-abc12.test.example.com")
And: The tunnel name is `f"tunnel-{test_id}"` (e.g., "tunnel-test-abc12")
And: The `friendly_hostname` in UniFi device uses the same `test_id`

---

### Requirement: JSON Serialization

The configurations SHALL be serialized to valid, consistently formatted JSON.

#### Scenario: Generate valid JSON output
Given: The configuration dicts are created
When: JSON strings are generated
Then: Use `json.dumps()` with `indent=2` for readable formatting
And: The output is valid JSON that passes `json.loads()` validation

#### Scenario: Consistent JSON formatting
Given: Both Cloudflare and UniFi configs are generated
When: The JSON strings are compared
Then: Both use the same indentation (2 spaces)
And: Both use standard JSON formatting (no trailing commas)

---

### Requirement: Method Documentation

The method SHALL have comprehensive documentation.

#### Scenario: Method has comprehensive docstring
Given: The `_generate_test_configs()` method
When: Documentation is reviewed
Then: The docstring describes all parameters (`test_id`, `cloudflare_zone`, `cloudflare_account_id`)
And: The docstring describes the return value structure (dict with "cloudflare" and "unifi" keys)
And: The docstring includes an example return value

---

## REMOVED Requirements

None - this change adds new functionality while maintaining backward compatibility of the test flow.

---

## MODIFIED Requirements

None - this is a replacement of an existing internal method.

---

## Cross-References

### Terraform Variable Definitions

#### Cloudflare Module (`terraform/modules/cloudflare-tunnel/variables.tf`)
```hcl
variable "config" {
  type = object({
    zone_name  = string
    account_id = string
    tunnels = map(object({
      tunnel_name = string
      mac_address = string
      services = list(object({
        public_hostname   = string
        local_service_url = string
        no_tls_verify     = optional(bool, false)
      }))
    }))
  })
}
```

#### UniFi Module (`terraform/modules/unifi-dns/variables.tf`)
```hcl
variable "config" {
  type = object({
    devices = list(object({
      friendly_hostname = string
      domain            = optional(string, null)
      service_cnames    = optional(list(string), [])
      nics = list(object({
        mac_address    = string
        nic_name       = optional(string, null)
        service_cnames = optional(list(string), [])
      }))
    }))
    default_domain = string
    site           = optional(string, "default")
  })
}
```

---

## Validation Checklist

- [ ] Method renamed from `_generate_test_kcl_config` to `_generate_test_configs`
- [ ] Method accepts `test_id`, `cloudflare_zone`, and `cloudflare_account_id` parameters
- [ ] Method returns dict with "cloudflare" and "unifi" keys
- [ ] Cloudflare JSON contains: `zone_name`, `account_id`, `tunnels`
- [ ] Cloudflare tunnel entry contains: `tunnel_name`, `mac_address`, `services`
- [ ] Cloudflare service entry contains: `public_hostname`, `local_service_url`, `no_tls_verify`
- [ ] UniFi JSON contains: `devices`, `default_domain`, `site`
- [ ] UniFi device entry contains: `friendly_hostname`, `domain`, `nics`
- [ ] UniFi NIC entry contains: `mac_address`, `nic_name`
- [ ] Both configs use the same MAC address in lowercase colon format
- [ ] MAC address matches validation regex
- [ ] `test_id` used consistently in tunnel names and hostnames
- [ ] JSON output is valid and properly formatted
- [ ] Method has comprehensive docstring with examples
