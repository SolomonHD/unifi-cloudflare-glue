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
