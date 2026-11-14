## MODIFIED Requirements

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

## ADDED Requirements

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
