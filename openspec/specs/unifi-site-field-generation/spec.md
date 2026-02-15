## ADDED Requirements

### Requirement: UniFi generator SHALL include site field in output
The `generate_unifi_config()` function in [`generators/unifi.k`](../../../../generators/unifi.k) SHALL include a `site` field in the generated JSON output, populated from `config.unifi_controller.site`.

#### Scenario: Generator includes site field
- **WHEN** `generate_unifi_config()` is called with a valid UniFiConfig
- **THEN** the returned dictionary MUST include a `site` field

#### Scenario: Site value comes from controller configuration
- **WHEN** `generate_unifi_config()` is called with `config.unifi_controller.site = "production"`
- **THEN** the generated JSON MUST contain `"site": "production"`

#### Scenario: Site field uses default value when not specified
- **WHEN** `generate_unifi_config()` is called with a config where `unifi_controller.site` is not explicitly set
- **THEN** the generated JSON MUST contain `"site": "default"` (the schema default)

### Requirement: Generated JSON SHALL match Terraform module expectations
The structure of the generated JSON MUST be compatible with the UniFi Terraform module's expected input format, including the `site` field at the root level alongside `devices` and `default_domain`.

#### Scenario: Complete JSON structure
- **WHEN** `generate_unifi_config()` is called
- **THEN** the returned dictionary MUST have keys: `devices`, `default_domain`, and `site`

#### Scenario: Site field is at root level
- **WHEN** the generated JSON is used by Terraform module
- **THEN** the module SHALL be able to access `local.effective_config.site` without errors

### Requirement: Existing functionality SHALL remain unchanged
Adding the `site` field MUST NOT break existing `devices` and `default_domain` generation.

#### Scenario: Devices array generation remains intact
- **WHEN** `generate_unifi_config()` is called with multiple devices
- **THEN** the `devices` array MUST be generated with the same structure as before

#### Scenario: Default domain generation remains intact
- **WHEN** `generate_unifi_config()` is called with `config.default_domain = "internal.lan"`
- **THEN** the generated JSON MUST contain `"default_domain": "internal.lan"`

#### Scenario: All existing examples continue to work
- **WHEN** existing example configurations (homelab-media-stack, internal-only, external-only, etc.) are run with `kcl run main.k`
- **THEN** they MUST generate valid JSON including the `site` field without errors
