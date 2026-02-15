## ADDED Requirements

### Requirement: Unified KCL entry-point invocation
The Dagger module SHALL invoke `kcl run main.k` as the sole KCL execution command for both UniFi and Cloudflare configuration generation. The module SHALL NOT invoke individual generator files (`generators/unifi.k`, `generators/cloudflare.k`).

#### Scenario: Successful UniFi config generation via main.k
- **WHEN** `generate_unifi_config()` is called with a source directory containing a valid `main.k` that exports `unifi_output`
- **THEN** the function SHALL run `kcl run main.k`, extract the `unifi_output` section from the YAML output using `yq`, convert it to JSON, and return a valid JSON file

#### Scenario: Successful Cloudflare config generation via main.k
- **WHEN** `generate_cloudflare_config()` is called with a source directory containing a valid `main.k` that exports `cf_output`
- **THEN** the function SHALL run `kcl run main.k`, extract the `cf_output` section from the YAML output using `yq`, convert it to JSON, and return a valid JSON file

### Requirement: Entry-point file validation
The Dagger module SHALL check for the existence of `main.k` in the consumer's source directory before attempting KCL execution. The module SHALL NOT check for `generators/unifi.k` or `generators/cloudflare.k`.

#### Scenario: main.k exists
- **WHEN** the source directory contains `main.k`
- **THEN** KCL execution SHALL proceed normally

#### Scenario: main.k is missing
- **WHEN** the source directory does not contain `main.k`
- **THEN** the function SHALL return a clear error message stating that `main.k` is required and explaining that the module no longer supports running individual generator files

### Requirement: Output key validation
The Dagger module SHALL validate that the extracted YAML section is not null after `yq` extraction.

#### Scenario: Expected output key exists in main.k output
- **WHEN** `kcl run main.k` produces YAML containing the expected key (`unifi_output` or `cf_output`)
- **THEN** extraction SHALL succeed and the result SHALL be converted to valid JSON

#### Scenario: Expected output key is missing from main.k output
- **WHEN** `kcl run main.k` produces YAML that does not contain the expected key (e.g., `yq` returns `null`)
- **THEN** the function SHALL return a clear error message explaining that the consumer's `main.k` MUST export `unifi_output` (for UniFi) or `cf_output` (for Cloudflare) as a public variable

### Requirement: Error messages reference main.k
All error messages and diagnostic hints in `generate_unifi_config()` and `generate_cloudflare_config()` SHALL reference `main.k` as the expected entry point. No error message SHALL reference `generators/unifi.k` or `generators/cloudflare.k`.

#### Scenario: KCL syntax error
- **WHEN** `kcl run main.k` fails with a syntax or type error
- **THEN** the error message SHALL include a hint to check syntax with `kcl run main.k` locally

#### Scenario: Empty KCL output
- **WHEN** `kcl run main.k` produces empty output
- **THEN** the error message SHALL suggest running `kcl run main.k` locally to inspect the raw output

### Requirement: JSON output format preservation
The JSON output produced by the new `main.k` + `yq` extraction pipeline SHALL be identical in structure and content to the JSON previously produced by running individual generator files.

#### Scenario: UniFi JSON format unchanged
- **WHEN** `generate_unifi_config()` extracts `unifi_output` from `main.k` output
- **THEN** the resulting JSON SHALL match the schema expected by the `terraform/modules/unifi-dns/` module

#### Scenario: Cloudflare JSON format unchanged
- **WHEN** `generate_cloudflare_config()` extracts `cf_output` from `main.k` output
- **THEN** the resulting JSON SHALL match the schema expected by the `terraform/modules/cloudflare-tunnel/` module
