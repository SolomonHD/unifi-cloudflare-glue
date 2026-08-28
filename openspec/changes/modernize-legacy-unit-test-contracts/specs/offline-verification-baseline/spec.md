## ADDED Requirements

### Requirement: Complete offline verification has one authoritative baseline
The repository SHALL document and execute one authoritative offline verification sequence that covers Python formatting, Python type and compile checks, the complete unit-test suite, and KCL schema and generator tests.

#### Scenario: Maintainer runs the offline baseline
- **WHEN** a maintainer runs the documented offline verification sequence from a clean checkout
- **THEN** every formatting, static, unit, schema, and generator check MUST pass
- **AND** the sequence MUST NOT require UniFi, Cloudflare, or backend credentials

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
