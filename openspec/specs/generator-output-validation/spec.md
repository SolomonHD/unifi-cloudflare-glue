# Generator Output Validation

## Purpose

Specify provider generator output shapes, validation diagnostics, and offline
test coverage. Active change deltas reconcile consumer fixtures and supported
APIs separately; this structural repair preserves the existing obligations.

## Requirements

### Requirement: UniFi generator output has all required top-level fields
When the UniFi generator produces output, it SHALL contain all required top-level fields with correct types.

#### Scenario: UniFi output has devices array
- **WHEN** the UniFi generator processes a valid configuration
- **THEN** the output SHALL contain a `devices` field that is an array

#### Scenario: UniFi output has default_domain string
- **WHEN** the UniFi generator processes a valid configuration
- **THEN** the output SHALL contain a `default_domain` field that is a string

#### Scenario: UniFi output has site string
- **WHEN** the UniFi generator processes a valid configuration
- **THEN** the output SHALL contain a `site` field that is a string representing the UniFi controller site

#### Scenario: UniFi output missing required field fails validation
- **WHEN** validating UniFi generator output that is missing `devices`, `default_domain`, or `site`
- **THEN** the validation SHALL fail with a clear error message indicating which field is missing

### Requirement: UniFi generator device structure is valid
Each device in the UniFi generator output SHALL have the correct structure and required fields.

#### Scenario: Device has friendly_hostname
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `friendly_hostname` field that is a non-empty string

#### Scenario: Device has domain
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `domain` field that is a string

#### Scenario: Device has service_cnames array
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `service_cnames` field that is an array of strings

#### Scenario: Device has nics array
- **WHEN** a device is present in UniFi generator output
- **THEN** it SHALL have a `nics` field that is an array containing at least one NIC

### Requirement: UniFi generator NIC structure is valid
Each NIC in a UniFi device SHALL have the correct structure and MAC address format.

#### Scenario: NIC has mac_address in normalized format
- **WHEN** a NIC is present in UniFi generator output
- **THEN** it SHALL have a `mac_address` field in normalized lowercase colon format (aa:bb:cc:dd:ee:ff)

#### Scenario: NIC has optional nic_name
- **WHEN** a NIC is present in UniFi generator output
- **THEN** it MAY have a `nic_name` field that is either a string or null

#### Scenario: NIC has service_cnames array
- **WHEN** a NIC is present in UniFi generator output
- **THEN** it SHALL have a `service_cnames` field that is an array of strings

### Requirement: Cloudflare generator output has all required top-level fields
When the Cloudflare generator produces output, it SHALL contain all required top-level fields with correct types.

#### Scenario: Cloudflare output has zone_name string
- **WHEN** the Cloudflare generator processes a valid configuration
- **THEN** the output SHALL contain a `zone_name` field that is a string

#### Scenario: Cloudflare output has account_id string
- **WHEN** the Cloudflare generator processes a valid configuration
- **THEN** the output SHALL contain an `account_id` field that is a string

#### Scenario: Cloudflare output has tunnels object
- **WHEN** the Cloudflare generator processes a valid configuration
- **THEN** the output SHALL contain a `tunnels` field that is an object/dictionary

#### Scenario: Cloudflare output missing required field fails validation
- **WHEN** validating Cloudflare generator output that is missing `zone_name`, `account_id`, or `tunnels`
- **THEN** the validation SHALL fail with a clear error message indicating which field is missing

### Requirement: Cloudflare generator tunnel structure is valid
Each tunnel in the Cloudflare generator output SHALL have the correct structure and required fields.

#### Scenario: Tunnel has tunnel_name
- **WHEN** a tunnel is present in Cloudflare generator output
- **THEN** it SHALL have a `tunnel_name` field that is a non-empty string

#### Scenario: Tunnel has mac_address in normalized format
- **WHEN** a tunnel is present in Cloudflare generator output
- **THEN** it SHALL have a `mac_address` field in normalized lowercase colon format

#### Scenario: Tunnel has services array
- **WHEN** a tunnel is present in Cloudflare generator output
- **THEN** it SHALL have a `services` field that is an array (may be empty)

### Requirement: Cloudflare generator service structure is valid
Each service in a Cloudflare tunnel SHALL have the correct structure and required fields.

#### Scenario: Service has public_hostname
- **WHEN** a service is present in Cloudflare generator output
- **THEN** it SHALL have a `public_hostname` field that is a string ending with the zone name

#### Scenario: Service has local_service_url
- **WHEN** a service is present in Cloudflare generator output
- **THEN** it SHALL have a `local_service_url` field that is a valid URL string

#### Scenario: Service has no_tls_verify boolean or null
- **WHEN** a service is present in Cloudflare generator output
- **THEN** it SHALL have a `no_tls_verify` field that is either a boolean or null/omitted

### Requirement: Generator output validation handles edge cases
The validation SHALL handle various edge cases gracefully.

#### Scenario: Empty devices array validation
- **WHEN** the UniFi generator produces output with an empty `devices` array
- **THEN** validation SHALL pass (empty devices is valid) but may issue a warning

#### Scenario: Device with no services
- **WHEN** a device has no services (empty services array)
- **THEN** validation SHALL pass as this is a valid configuration

#### Scenario: Device with multiple NICs
- **WHEN** a device has multiple NICs in its `nics` array
- **THEN** validation SHALL pass and verify all NICs have valid structure

#### Scenario: MAC address normalization is consistent
- **WHEN** MAC addresses are provided in various formats (AA:BB:CC:DD:EE:FF, aa-bb-cc-dd-ee-ff, AABBCCDDEEFF)
- **THEN** the generator SHALL normalize all to lowercase colon format (aa:bb:cc:dd:ee:ff)

### Requirement: Validation provides clear error messages
When validation fails, it SHALL provide actionable field-path and type/format diagnostics without echoing offending values or the full configuration.

#### Scenario: Missing field error message
- **WHEN** validation detects a missing required field
- **THEN** the error message SHALL identify the field path, that the field is missing, and the expected type

#### Scenario: Wrong type error message
- **WHEN** validation detects a field with incorrect type
- **THEN** the error message SHALL identify the field path, expected type, and found type
- **AND** it MUST NOT include the offending value or full configuration

#### Scenario: Invalid MAC address format error
- **WHEN** validation detects a MAC address not in normalized format
- **THEN** the error message SHALL identify the field path and expected normalized MAC format
- **AND** it MUST NOT echo the invalid MAC value or arbitrary tunnel-map key

### Requirement: Tests run without external dependencies
The generator validation tests SHALL run without requiring external services.

#### Scenario: Tests run locally without UniFi controller
- **WHEN** running generator validation tests
- **THEN** they SHALL NOT require connection to a UniFi controller

#### Scenario: Tests run locally without Cloudflare API
- **WHEN** running generator validation tests
- **THEN** they SHALL NOT require connection to Cloudflare API

#### Scenario: Tests run in CI pipeline
- **WHEN** generator validation tests run in CI/CD
- **THEN** they SHALL complete successfully without external credentials

### Requirement: Generator output matches Terraform module expectations
The validation SHALL verify that generator output matches what Terraform modules expect.

#### Scenario: UniFi output matches unifi-dns module variables
- **WHEN** validating UniFi generator output
- **THEN** it SHALL match the structure expected by `terraform/modules/unifi-dns`

#### Scenario: Cloudflare output matches cloudflare-tunnel module variables
- **WHEN** validating Cloudflare generator output
- **THEN** it SHALL match the structure expected by `terraform/modules/cloudflare-tunnel`

#### Scenario: Services distribution filtering works correctly
- **WHEN** services have different distribution modes (unifi_only, cloudflare_only, both)
- **THEN** UniFi generator SHALL only include unifi_only and both services
- **AND** Cloudflare generator SHALL only include cloudflare_only and both services

### Requirement: Generator tests distinguish standalone and consumer outputs
Generator-output tests MUST validate standalone generator modules through their `result` output and MUST validate Dagger consumer generation through purpose-built `main.k` fixtures exporting the documented `unifi_output` or `cf_output` key.

#### Scenario: Standalone UniFi generator is validated
- **WHEN** the test suite executes `generators/unifi.k` directly
- **THEN** it MUST validate the generated configuration under `result`
- **AND** it MUST NOT require that standalone module to export `unifi_output`

#### Scenario: Standalone Cloudflare generator is validated
- **WHEN** the test suite executes `generators/cloudflare.k` directly
- **THEN** it MUST validate the generated configuration under `result`
- **AND** it MUST NOT require that standalone module to export `cf_output`

#### Scenario: Dagger consumer output is validated
- **WHEN** the test suite exercises a Dagger KCL generation function
- **THEN** its fixture `main.k` MUST export the consumer key documented for that function
- **AND** the test MUST validate the extracted JSON against the corresponding Terraform module contract

### Requirement: Repository library entry point is not treated as a consumer fixture
The generator-output suite MUST NOT assume the repository's schema/library `main.k` exports consumer-specific generated configuration keys unless that file's documented contract explicitly requires them.

#### Scenario: Generator fixture selection
- **WHEN** a test needs valid or invalid consumer output
- **THEN** it MUST create or use a dedicated consumer fixture
- **AND** it MUST NOT infer missing consumer keys by executing the repository library entry point

### Requirement: Generator assertions exercise actual supported transformations
The generator suite MUST exercise current transformations and validation through real generator inputs and consumer fixtures rather than assert precomputed expected values, tautologies, or manually reproduced errors.

#### Scenario: Input formats and distribution vary
- **WHEN** fixtures contain uppercase, hyphenated, compact, and mixed-case MACs, multiple or empty NIC/service cases, and each service distribution
- **THEN** generated output MUST demonstrate the supported normalization and provider filtering behavior
- **AND** both provider outputs and DNS-loop rejection MUST be checked

#### Scenario: Consumer output is missing or malformed
- **WHEN** a dedicated consumer fixture omits a required output key or emits an invalid type or structure
- **THEN** tests MUST exercise the supported generation/validation path and verify an actionable failure

### Requirement: Production generation rejects malformed provider structures
Both public generation methods MUST validate parsed JSON against existing provider input structures before returning a generated file, without adding a validation dependency or changing provider schemas.

#### Scenario: Invalid nested field is emitted
- **WHEN** a consumer emits an invalid top-level or nested device, NIC, tunnel, or service type or omits a required field
- **THEN** generation MUST raise `KCLGenerationError` identifying the field path and expected/found type or missing field
- **AND** the diagnostic MUST NOT echo offending values or the complete configuration

#### Scenario: Legitimate empty and optional fields are emitted
- **WHEN** output uses empty collections or optional values permitted by the existing Terraform contract
- **THEN** generation MUST preserve those supported values

### Requirement: KCL generation enforces DNS-loop rejection
Cloudflare KCL generation MUST reject origins at the public zone apex or its subdomains by default for explicit and entity-derived services, before exporting usable configuration. Only an exact typed `split_dns_origins` declaration matching protocol, normalized DNS hostname and effective port MAY exempt an origin.

#### Scenario: Explicit or derived origin points into the public zone
- **WHEN** an explicit service URL, service hostname override, or resolved fallback hostname uses the zone apex or a subdomain, including case and trailing-dot variants
- **THEN** KCL generation MUST fail with an actionable tunnel/service location unless that exact origin tuple is declared
- **AND** it MUST NOT silently omit the invalid service

#### Scenario: Origin is outside the public zone
- **WHEN** an origin uses an internal domain or a distinct hostname such as `notexample.com` for zone `example.com`
- **THEN** DNS-loop validation MUST allow it

#### Scenario: Exact split-DNS declaration permits a same-zone origin
- **WHEN** an explicit, entity-derived, hostname-override or fallback service resolves to an origin exactly matching a valid `cloudflare.SplitDNSOrigin` declaration
- **THEN** generation MUST allow the same-zone origin without altering the URL, service ordering, TLS/path metadata or Terraform input shape
- **AND** tests MUST exercise both configuration and direct transform helper entry points with the same typed policy
- **AND** documentation MUST distinguish public-zone membership from proof of a loop and declared operator intent from verified DNS resolution

#### Scenario: Origin matching is narrowly normalized
- **WHEN** matching lowercase URL schemes, DNS hostname case and one terminal DNS root dot, or implicit HTTP port 80 and HTTPS port 443 against declared ports
- **THEN** tests MUST prove equivalent tuples match and protocol, port and distinct-hostname tuples do not
- **AND** TCP MUST require an explicit URL port to qualify
- **AND** paths, queries and fragments MUST NOT change origin identity or be rewritten

#### Scenario: Declaration does not grant inherited or global permission
- **WHEN** a declaration names a specific hostname and port
- **THEN** tests MUST prove it grants no suffix wildcard, subdomain inheritance, other port/protocol or global bypass
- **AND** omitted or empty policy MUST retain default rejection of same-zone apex and subdomains

#### Scenario: Invalid declarations and ambiguous authorities fail closed
- **WHEN** a declaration has an invalid protocol, non-integer or out-of-range port, or a hostname that is a URL, wildcard, IP address, address range or otherwise not a concrete DNS name
- **THEN** generation MUST reject the declaration rather than ignore it or broaden permission
- **AND** tests MUST prove userinfo or ambiguous URL authority cannot qualify for an exception
