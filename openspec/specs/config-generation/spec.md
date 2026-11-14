# Configuration Generation

## Purpose

Define deterministic provider configuration generation and synthetic test fixtures with stable JSON schemas, consistent identities and DNS-loop prevention.

## Requirements

### Requirement: Method Rename and Signature Update

The method `_generate_test_kcl_config()` SHALL be renamed to `_generate_test_configs()` and its signature updated to accept new parameters and return a dict.

#### Scenario: Method renamed for clarity
- **GIVEN** the existing `_generate_test_kcl_config()` method exists in `src/main/main.py`
- **WHEN** the change is implemented
- **THEN** the method is renamed to `_generate_test_configs()`
- **AND** all references to the old method name are updated

#### Scenario: Method signature updated with new parameter
- **GIVEN** the `_generate_test_configs()` method
- **WHEN** the method signature is defined
- **THEN** it accepts `test_id: str` as the first parameter
- **AND** it accepts `cloudflare_zone: str` as the second parameter
- **AND** it accepts `cloudflare_account_id: str` as the third parameter
- **AND** it returns a `dict` with "cloudflare" and "unifi" keys

#### Scenario: Call site updated in test_integration
- **GIVEN** the `test_integration` method calls `_generate_test_kcl_config()`
- **WHEN** the method is renamed
- **THEN** the call site uses the new name `_generate_test_configs()`
- **AND** the call passes `cloudflare_account_id` parameter
- **AND** the call handles the dict return value

---

### Requirement: Cloudflare JSON Structure

The Cloudflare configuration JSON SHALL match the Terraform tunnel input schema regardless of the internal extraction/parser implementation.

#### Scenario: Cloudflare config top-level structure
- **WHEN** a valid Cloudflare test configuration is generated
- **THEN** it contains the selected zone_name, account_id and tunnels map

#### Scenario: Cloudflare tunnel entry structure
- **WHEN** a test tunnel is generated
- **THEN** it is keyed by normalized MAC and includes the corresponding tunnel_name, mac_address and services list

#### Scenario: Cloudflare service entry structure
- **WHEN** a test service is generated
- **THEN** it contains its public_hostname, internal local_service_url and no_tls_verify false

#### Scenario: DNS loop prevention compliance
- **WHEN** the origin URL of a generated test service is checked
- **THEN** it targets an internal address rather than routing back through the public Cloudflare hostname

---

### Requirement: UniFi JSON Structure

The UniFi configuration JSON SHALL match the Terraform DNS input schema regardless of the internal extraction/parser implementation.

#### Scenario: UniFi config top-level structure
- **WHEN** a default test configuration is generated
- **THEN** it contains devices, default_domain local and site default

#### Scenario: UniFi device entry structure
- **WHEN** a test device is generated
- **THEN** it contains its test_id friendly_hostname, local domain and nics list

#### Scenario: UniFi NIC entry structure
- **WHEN** a default test NIC is generated
- **THEN** it contains the MAC shared with the Cloudflare fixture and nic_name eth0

---

### Requirement: MAC Address Format and Consistency

The MAC address SHALL be consistent across both configs and match the validation regex.

#### Scenario: Consistent MAC address across configs
- **GIVEN** both Cloudflare and UniFi configs are generated
- **WHEN** the MAC addresses are compared
- **THEN** both configs use the exact same MAC address
- **AND** the MAC is in lowercase colon format (aa:bb:cc:dd:ee:ff)

#### Scenario: Valid MAC address format
- **GIVEN** a MAC address is generated for test configurations
- **WHEN** the MAC is used in either config
- **THEN** the format matches regex: `^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$|^[0-9a-fA-F]{12}$`
- **AND** the format uses lowercase hexadecimal characters
- **AND** the format uses colons as separators

#### Scenario: Use recommended test MAC
- **GIVEN** a test configuration needs a MAC address
- **WHEN** the MAC is selected
- **THEN** use `aa:bb:cc:dd:ee:ff` as the default test MAC address

---

### Requirement: Test ID Usage

The test_id SHALL be used consistently across all generated identifiers.

#### Scenario: Consistent test ID in hostnames and tunnel names
- **GIVEN** a `test_id` parameter (e.g., "test-abc12")
- **WHEN** hostnames and tunnel names are generated
- **THEN** the test hostname is `f"{test_id}.{cloudflare_zone}"` (e.g., "test-abc12.test.example.com")
- **AND** the tunnel name is `f"tunnel-{test_id}"` (e.g., "tunnel-test-abc12")
- **AND** the `friendly_hostname` in UniFi device uses the same `test_id`

---

### Requirement: JSON Serialization

The configurations SHALL be serialized to valid, consistently formatted JSON.

#### Scenario: Generate valid JSON output
- **GIVEN** the configuration dicts are created
- **WHEN** JSON strings are generated
- **THEN** use `json.dumps()` with `indent=2` for readable formatting
- **AND** the output is valid JSON that passes `json.loads()` validation

#### Scenario: Consistent JSON formatting
- **GIVEN** both Cloudflare and UniFi configs are generated
- **WHEN** the JSON strings are compared
- **THEN** both use the same indentation (2 spaces)
- **AND** both use standard JSON formatting (no trailing commas)

---

### Requirement: Method Documentation

The method SHALL have comprehensive documentation.

#### Scenario: Method has comprehensive docstring
- **GIVEN** the `_generate_test_configs()` method
- **WHEN** documentation is reviewed
- **THEN** the docstring describes all parameters (`test_id`, `cloudflare_zone`, `cloudflare_account_id`)
- **AND** the docstring describes the return value structure (dict with "cloudflare" and "unifi" keys)
- **AND** the docstring includes an example return value

---

### Requirement: Shared deterministic configuration generation
The module SHALL produce requested UniFi and Cloudflare configuration from one consistent source/dependency snapshot without routine dependency updates or live provider credentials.

#### Scenario: Both provider outputs are requested
- **WHEN** a valid consumer KCL entry point exports both provider configurations
- **THEN** both outputs are generated from the same resolved snapshot
- **AND** MAC normalization, site propagation, service filtering and DNS-loop prevention retain their accepted behavior
- **AND** no unversioned parser download or live provider access is required

#### Scenario: Only one output is requested
- **WHEN** the caller requests UniFi-only or Cloudflare-only generation
- **THEN** the requested output retains its existing Terraform input schema
- **AND** absence of the unrequested output does not require unrelated credentials or cause failure

### Requirement: Generated data is separate from diagnostics
Generation SHALL validate machine-readable output and required selected keys without treating diagnostic text as configuration or rejecting valid data by keyword search alone.

#### Scenario: Output is missing or malformed
- **WHEN** generation returns empty, malformed or missing selected-key data
- **THEN** generation fails with a bounded useful diagnostic
- **AND** no downstream plan or apply is dispatched

#### Scenario: Valid data contains a diagnostic-like word
- **WHEN** a valid configuration string contains the word VALIDATION
- **THEN** structural validity determines acceptance rather than that substring

### Requirement: Checkout generation is explicitly selected
The module SHALL distinguish transient provider configuration from intentionally applied checkout changes and SHALL NOT expose state, credentials or raw plans as ordinary generated checkout content.

#### Scenario: Caller selects checkout generation
- **WHEN** a caller explicitly requests configuration changes for its checkout
- **THEN** only designated non-sensitive output paths are included in the reviewable change set
- **AND** ordinary validation does not write checkout files implicitly

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

## Historical Validation Notes

The former migration checklist restated the method, schema, identity, serialization and documentation requirements above. Those obligations remain normative requirements, not evidence that runtime implementation has passed. See `docs/spec-reconciliation.md` for historical clause disposition.
