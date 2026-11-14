## ADDED Requirements

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
Cloudflare KCL generation MUST reject resolved origin hostnames equal to the public zone or a subdomain of that zone, for explicit tunnel services and entity-derived services, before exporting usable configuration.

#### Scenario: Explicit or derived origin points into the public zone
- **WHEN** an explicit service URL, service hostname override, or resolved fallback hostname uses the zone apex or a subdomain, including case and trailing-dot variants
- **THEN** KCL generation MUST fail with an actionable tunnel/service location
- **AND** it MUST NOT silently omit the invalid service

#### Scenario: Origin is outside the public zone
- **WHEN** an origin uses an internal domain or a distinct hostname such as `notexample.com` for zone `example.com`
- **THEN** DNS-loop validation MUST allow it

## MODIFIED Requirements

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
