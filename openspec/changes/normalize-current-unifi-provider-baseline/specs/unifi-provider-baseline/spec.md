## ADDED Requirements

### Requirement: Current provider baseline is explicit
The UniFi modules MUST identify `filipowm/unifi` v1.1.x as the reviewed current-provider baseline and MUST describe the upgrade from v1.0.0 as maintenance rather than an authentication fix.

#### Scenario: Terraform initializes the UniFi modules
- **WHEN** provider dependencies are resolved
- **THEN** the selected `filipowm/unifi` version MUST satisfy `~> 1.1.0`
- **AND** tests MUST report the selected version without exposing credentials

### Requirement: API key is the tested primary authentication path
The baseline MUST prove that the current provider can authenticate to the production controller using the operator's UniFi API key.

#### Scenario: Production baseline plan is executed
- **WHEN** the hardened Dagger plan runs against the production state with API-key authentication
- **THEN** provider refresh MUST succeed
- **AND** the plan MUST report 0 add, 0 change, and 0 destroy

### Requirement: Network 10 unremembered clients remain supported
The UniFi DNS module MUST register or adopt configured clients before reading their current IP so that Network 10.x does not fail with `UnknownUser` for an active but unremembered MAC.

#### Scenario: Configured client is not yet remembered
- **WHEN** the module evaluates a configured normalized MAC address that is active but absent from the persistent client database
- **THEN** the provider resource MUST register or adopt the client before the dependent read
- **AND** destroy MUST be configured not to forget the client

### Requirement: Disposable DNS lifecycle baseline is isolated
The baseline fixture MUST exercise representative A and CNAME lifecycle operations below a unique `solomonhd.ai` namespace without taking ownership of production client MACs or production DNS names.

#### Scenario: Baseline fixture completes
- **WHEN** an authorized operator runs the fixture
- **THEN** it MUST create a production-scale representative record set, produce a zero-drift second plan, update one benign record, destroy the set, and verify absence
- **AND** every record name MUST be confined to the run-specific sandbox namespace
