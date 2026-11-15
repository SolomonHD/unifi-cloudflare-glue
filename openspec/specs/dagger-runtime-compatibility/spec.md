# dagger-runtime-compatibility Specification

## Purpose

Define the qualified runtime and reproducibility contract shared by reusable DNS modules, local callers, CI runners, and consuming repositories.

## Requirements

### Requirement: Exact runtime qualification precedes adoption
The module SHALL qualify Dagger v1.0.0-beta.27 as its primary CLI/engine candidate and resolve its compatible exact Python SDK identity before target-dependent modernization. The v0.21.11 fallback SHALL require failed beta evidence, explicit recorded acceptance and separate compatibility checks. Installation alone SHALL NOT count as runtime acceptance; qualification SHALL preserve host-global selection and use exact versions.

#### Scenario: Candidate CLI is installed
- **WHEN** the candidate CLI is installed and its version output is verified
- **THEN** engine execution, SDK compatibility, manifest migration and consumer acceptance remain unverified until their checks pass
- **AND** qualification uses an explicit versioned invocation without changing host-global tool selection or following moving latest/beta labels

#### Scenario: Beta qualification succeeds
- **WHEN** the v1.0.0-beta.27 candidate and its resolved exact Python SDK pass isolated schema loading, Python execution, secret-channel, cache and cross-repository consumption tests
- **THEN** its immutable identity and supported manifest/lock formats are recorded as the modernization target
- **AND** production adoption remains gated on separate consumer acceptance

#### Scenario: Qualification is blocked
- **WHEN** the candidate fails a required compatibility check
- **THEN** dependent implementation stops with the failed evidence retained
- **AND** adopting v0.21.11 instead requires a recorded acceptance decision and its own compatibility checks

### Requirement: Execution dependencies are reproducible
The module SHALL use tested exact tool identities and ecosystem lockfiles without refreshing dependencies during ordinary generation or verification.

#### Scenario: Repeated generation with unchanged inputs
- **WHEN** the same source and accepted dependency locks are supplied locally and in CI
- **THEN** the resolved tool identities and normalized generated outputs agree
- **AND** missing frozen resolutions fail instead of selecting latest versions

### Requirement: Offline verification is portable and credential-free
The module SHALL expose the same complete supported offline verification contract locally and through the qualified Dagger CI entry point without production credentials or live infrastructure access.

#### Scenario: Offline verification runs in CI
- **WHEN** the accepted Dagger verification entry point is invoked without cloud or controller credentials
- **THEN** it runs supported unit, KCL, schema and synthetic failure/security checks
- **AND** a failed check produces a nonzero command result
- **AND** it does not dispatch a live canary or infrastructure mutation

### Requirement: Consumer migration is explicit
Breaking runtime, manifest, backend-input or return-contract changes SHALL be documented with a tested consumer migration and reversible source selection before production adoption.

#### Scenario: Consumer loads a feature revision
- **WHEN** another repository selects the reviewed module revision and matching KCL dependency
- **THEN** remote module loading and credential-free generation succeed under the accepted runtime tuple
- **AND** no host-global tool selection, production state or unrelated deployment is changed implicitly
