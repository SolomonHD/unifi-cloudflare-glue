# Cache Control

## Purpose

Ensure live infrastructure operations observe and execute fresh work while deterministic configuration generation remains reusable.

## Requirements

### Requirement: Deploy function supports cache busting
The deploy operation SHALL automatically execute fresh live effects without requiring a caller cache-buster. Deterministic source generation SHALL remain reusable independently of operation identity.

#### Scenario: Identical deployments are separately dispatched
- **WHEN** two explicitly requested deployments have identical configuration and no caller cache-buster
- **THEN** each dispatches its live execution rather than returning a prior cached effect
- **AND** unchanged deterministic generation is eligible for reuse

### Requirement: Plan function supports cache busting
The plan operation SHALL freshly initialize/refresh the selected backend and infrastructure observations as required, without caller timestamps or generation-wide invalidation.

#### Scenario: Repeated plan observes external changes
- **WHEN** a second plan follows an external resource change with unchanged desired configuration
- **THEN** it observes the current resource state and does not reuse the earlier live plan
- **AND** no secret becomes an ordinary freshness key

### Requirement: Destroy function supports cache busting
The destroy operation SHALL dispatch fresh execution and perform a fresh, ordered residual check without relying on a previous cleanup result.

#### Scenario: Cleanup is checked after destruction
- **WHEN** destruction follows a previous successful absence check
- **THEN** the residual check executes again after the destroy attempt
- **AND** a failed or unknown verification is not reported as absence

### Requirement: Test integration function supports cache busting
Live integration operations SHALL use automatic freshness for effects and observations at both function and underlying execution boundaries.

#### Scenario: Function cache policy is insufficient alone
- **WHEN** an uncached function constructs the same underlying live command graph twice
- **THEN** the module still ensures fresh command dispatch for both invocations
- **AND** callers need not inject a timestamp into source files, shell comments or command text

### Requirement: Manual run labels are not execution guarantees
An optional manual run label SHALL be bounded non-secret metadata and SHALL NOT be interpreted as shell syntax or required for live-operation correctness.

#### Scenario: Label contains shell metacharacters
- **WHEN** a label contains a newline or shell metacharacters
- **THEN** it is rejected or handled strictly as data
- **AND** it cannot introduce executable commands or replace automatic freshness
