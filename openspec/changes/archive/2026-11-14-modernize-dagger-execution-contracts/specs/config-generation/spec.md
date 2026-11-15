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
- **AND** same-zone origins remain rejected unless their exact tuple is approved by the typed split-DNS origin policy
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

### Requirement: Split-DNS origin exceptions are typed and exact
Cloudflare generation SHALL accept opt-in `cloudflare.SplitDNSOrigin` records with `protocol: "http" | "https" | "tcp"`, `hostname: str` and `port: int` in 1..65535. `CloudflareConfig.split_dns_origins` SHALL be a typed `[SplitDNSOrigin]` list defaulting to `[]`, permitting only exact origin matches.

#### Scenario: Existing callers omit the policy
- **WHEN** existing explicit configuration, entity-generator or direct transform helper calls omit `split_dns_origins` or supply an empty list
- **THEN** their signatures remain usable and same-zone apex/subdomain origins remain rejected by default
- **AND** the entity generator and direct transform helpers SHALL accept the same typed list as an optional trailing `split_dns_origins` argument defaulting to empty
- **AND** origins outside the public zone retain existing behavior

#### Scenario: Operator approves one concrete origin
- **WHEN** a valid declaration matches the service's lowercase URL scheme, case-insensitive DNS hostname with one terminal root dot normalized, and effective port
- **THEN** generation SHALL allow that exact origin in the public zone
- **AND** HTTP and HTTPS without explicit ports SHALL match port 80 and 443 respectively, while TCP SHALL require an explicit URL port
- **AND** no suffix wildcard, subdomain inheritance or global bypass SHALL be granted

#### Scenario: Malformed policy or unsafe authority is supplied
- **WHEN** a declaration contains a protocol outside the declared union, a non-integer or out-of-range port, or a hostname that is not a concrete DNS name, including a URL, wildcard, IP address or address range
- **THEN** validation SHALL fail closed even if the declaration is unused
- **AND** userinfo and ambiguous URL authorities SHALL NOT qualify for an exception

#### Scenario: Origin policy does not change generated routing
- **WHEN** an exact approved origin URL contains a path, query or fragment
- **THEN** those components SHALL NOT change the origin identity
- **AND** output URLs, service ordering, TLS/path metadata and Terraform JSON shape SHALL remain unchanged
- **AND** `split_dns_origins` SHALL NOT be emitted into Terraform JSON

#### Scenario: Declared intent is distinguished from live acceptance
- **WHEN** a consumer declares `https`, `traefik-mid.sghd.io`, port `443` as a split-DNS origin
- **THEN** documentation SHALL explain that public-zone membership alone does not prove a loop and the exception expresses operator intent only
- **AND** separately authorized live acceptance SHALL prove that the connector resolves the origin internally without a Cloudflare loop

### Requirement: Checkout generation is explicitly selected
The module SHALL distinguish transient provider configuration from intentionally applied checkout changes and SHALL NOT expose state, credentials or raw plans as ordinary generated checkout content.

#### Scenario: Caller selects checkout generation
- **WHEN** a caller explicitly requests configuration changes for its checkout
- **THEN** only designated non-sensitive output paths are included in the reviewable change set
- **AND** ordinary validation does not write checkout files implicitly
