# offline-verification-baseline Specification

## Purpose

Provides an authoritative credential-free regression baseline before execution modernization and dependent infrastructure feature implementation.

## Requirements

### Requirement: Complete offline verification has one authoritative baseline
The repository SHALL document and execute one authoritative offline verification sequence that covers Python formatting, Python type and compile checks, the complete unit-test suite, and KCL schema and generator tests.

#### Scenario: Maintainer runs the offline baseline
- **WHEN** a maintainer runs the documented offline verification sequence from a clean checkout
- **THEN** every formatting, static, unit, schema, and generator check MUST pass
- **AND** the sequence MUST NOT require UniFi, Cloudflare, or backend credentials
- **AND** documented tool/bootstrap prerequisites MUST distinguish initial dependency acquisition from verification without live infrastructure calls

### Requirement: Security regression tests remain in the complete suite
The authoritative offline baseline MUST include the sentinel-secret and failure-injection regression tests introduced by `harden-dagger-secret-and-state-handling`.

#### Scenario: Complete unit suite is collected
- **WHEN** the authoritative offline unit suite is collected
- **THEN** sentinel coverage for output, exceptions, reports, and exported artifacts MUST be present
- **AND** failure-injection coverage for partial apply, validation failure, timeout, cleanup failure, and residual resources MUST be present

### Requirement: Obsolete tests are explicitly reconciled
Every test that targets a removed API or superseded output contract MUST be rewritten against supported behavior or removed with its obsolete contract documented in the change review.

#### Scenario: Legacy failure inventory is resolved
- **WHEN** implementation completes
- **THEN** no unit-test failure, skip, xfail, or marker exclusion MAY remain solely because it targets an obsolete repository contract
- **AND** live infrastructure tests MAY remain separately gated by explicit operator authorization

### Requirement: Baseline precedes execution and infrastructure changes
The accepted current-contract baseline MUST precede execution refactoring in `modernize-dagger-execution-contracts` and provider/canary implementation; later changes MUST extend and rerun it without temporary obsolete APIs.

#### Scenario: Runtime qualification proceeds concurrently
- **WHEN** the parent qualifies an exact Dagger beta runtime while baseline repair proceeds
- **THEN** baseline repair MUST remain independent of that selection
- **AND** execution refactoring MUST wait for recorded baseline acceptance, without requiring migration/canary completion or baseline archive
