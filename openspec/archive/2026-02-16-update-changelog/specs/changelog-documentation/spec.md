## ADDED Requirements

### Requirement: CHANGELOG.md contains breaking change documentation
The CHANGELOG.md SHALL include a breaking change section documenting the removal of the `--no-cache` flag.

#### Scenario: Breaking change section exists
- **WHEN** a user reads the `[Unreleased]` section of CHANGELOG.md
- **THEN** they SHALL see a `### ⚠️ BREAKING CHANGES` subsection
- **AND** it SHALL document the removal of the `no_cache` parameter

#### Scenario: Migration guidance is provided
- **WHEN** a user reads the breaking change documentation
- **THEN** they SHALL see before/after command examples showing the `--cache-buster=$(date +%s)` replacement
- **AND** the examples SHALL cover all affected functions: `deploy`, `plan`, `destroy`, `test_integration`

#### Scenario: Technical rationale is explained
- **WHEN** a user reads the breaking change documentation
- **THEN** they SHALL see an explanation of why the change was made
- **AND** the explanation SHALL reference Dagger's function-level caching behavior
