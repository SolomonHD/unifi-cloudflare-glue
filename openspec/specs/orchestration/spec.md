# Spec: Deployment Orchestration Function

## Purpose

Define ordered, validated deployment orchestration with truthful status, protected credentials and recoverable partial or unknown outcomes.

## Requirements

### Requirement: deploy Function (Orchestration)

The module SHALL orchestrate validated KCL generation and selected infrastructure operations using the accepted resource dependency graph, preserving UniFi-before-dependent-Cloudflare ordering and reporting actual operation outcomes.

#### Scenario: Full Deployment Orchestration
- **WHEN** valid configuration and both providers' credentials are supplied for full deployment
- **THEN** both configurations are validated before effects and dependent Cloudflare work follows successful UniFi prerequisites
- **AND** resource addresses and state ownership are preserved

#### Scenario: Deployment Order Enforcement
- **WHEN** a UniFi prerequisite fails
- **THEN** dependent Cloudflare work is not dispatched and the overall command fails

#### Scenario: KCL Generation Integration
- **WHEN** orchestration begins with valid KCL input
- **THEN** selected validated provider files come from the shared deterministic generation result

#### Scenario: Orchestration Failure - UniFi Deployment Fails
- **WHEN** UniFi execution fails
- **THEN** the command exits unsuccessfully with sanitized phase information and records any attempted effects needing reconciliation

#### Scenario: Orchestration Failure - Cloudflare Deployment Fails
- **WHEN** Cloudflare fails after UniFi effects succeeded
- **THEN** the command fails while identifying completed and failed phases without claiming automatic rollback

#### Scenario: Deployment Success Reporting
- **WHEN** all requested operations and required verification succeed
- **THEN** the report identifies success and bounded resource outcomes without secret values

---

### Requirement: deploy Function Parameters

The `deploy` function SHALL accept all parameters needed for both UniFi and Cloudflare deployments, plus KCL source.

#### Scenario: KCL Source Parameter
- **WHEN** the function receives KCL source
- **THEN** it accepts a required `kcl_source` parameter of type `dagger.Directory` containing the KCL module with schemas and generators

#### Scenario: Combined UniFi Parameters
- **WHEN** UniFi deployment is selected
- **THEN** it accepts all UniFi deployment parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `unifi_url` | `str` | UniFi Controller URL |
| `api_url` | `str` | UniFi API URL (optional, defaults to unifi_url) |
| `unifi_api_key` | `dagger.Secret` | UniFi API key (optional) |
| `unifi_username` | `dagger.Secret` | UniFi username (optional) |
| `unifi_password` | `dagger.Secret` | UniFi password (optional) |

#### Scenario: Combined Cloudflare Parameters
- **WHEN** Cloudflare deployment is selected
- **THEN** it accepts all Cloudflare deployment parameters:
| Parameter | Type | Description |
|-----------|------|-------------|
| `cloudflare_token` | `dagger.Secret` | Cloudflare API Token |
| `cloudflare_account_id` | `str` | Cloudflare Account ID |
| `zone_name` | `str` | DNS zone name |

#### Scenario: Parameter Validation
- **WHEN** `deploy` is called with invalid or missing parameters
- **THEN** it validates all selected-scope parameters before starting execution
- **AND** validation fails nonzero with clear sanitized diagnostics

---

### Requirement: deploy Function Return Value

Successful deployment SHALL return a CLI-readable bounded summary. Failed or partially failed deployment SHALL produce unsuccessful command status rather than a successful string containing a failure marker.

#### Scenario: Success Return Format
- **WHEN** orchestration succeeds
- **THEN** the summary includes selected scope and bounded resource counts

#### Scenario: Partial Failure Return Format
- **WHEN** some effects succeeded before a later phase failed
- **THEN** the CLI exits nonzero and preserves sanitized completed/failed/unknown outcomes

#### Scenario: Complete Failure Return Format
- **WHEN** a required phase fails before dependent work begins
- **THEN** the CLI exits nonzero and identifies the failure and skipped dependent phases

### Requirement: Execution snapshots preserve completed preparation
Operations that depend on initialization or earlier filesystem changes SHALL execute from the corresponding completed snapshot, including integration and cleanup paths.

#### Scenario: Cleanup follows initialization
- **WHEN** cleanup initialization succeeds
- **THEN** destroy uses the initialized snapshot and its state/configuration rather than a pre-init snapshot

### Requirement: Unknown effects require reconciliation
Timeouts, cancellation and transport loss SHALL remain unknown outcomes until authoritative reconciliation; retries SHALL NOT blindly repeat an uncertain effect.

#### Scenario: Apply exceeds its wait deadline
- **WHEN** the client stops waiting without proof of remote termination
- **THEN** the operation reports uncertainty with a non-secret identity and recovery guidance
- **AND** it does not claim rollback or automatically repeat apply
