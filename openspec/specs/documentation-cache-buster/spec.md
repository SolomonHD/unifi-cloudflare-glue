## ADDED Requirements

### Requirement: README.md contains no --no-cache references
All command examples in README.md SHALL use the `--cache-buster=$(date +%s)` pattern instead of `--no-cache`.

#### Scenario: User reads deployment example in README
- **WHEN** a user views the deployment examples in README.md
- **THEN** all dagger call commands show `--cache-buster=$(date +%s)`
- **AND** no examples contain `--no-cache`

#### Scenario: User reads quickstart example in README
- **WHEN** a user views the quickstart section in README.md
- **THEN** all command examples use `--cache-buster=$(date +%s)`
- **AND** no examples contain `--no-cache`

### Requirement: docs/dagger-reference.md parameter tables are updated
The parameter documentation in docs/dagger-reference.md SHALL only list `--cache-buster` parameter.

#### Scenario: User checks parameter reference
- **WHEN** a user views the parameter tables in docs/dagger-reference.md
- **THEN** the tables show `--cache-buster` with description "Unique value to bypass cache (use `$(date +%s)`)"
- **AND** no table rows reference `--no-cache`

#### Scenario: User checks deploy function documentation
- **WHEN** a user views the deploy function examples in docs/dagger-reference.md
- **THEN** all examples use `--cache-buster=$(date +%s)`
- **AND** no examples contain `--no-cache`

### Requirement: docs/deployment-patterns.md cache control section explains timestamp requirement
The cache control section in docs/deployment-patterns.md SHALL explain why explicit timestamps are required.

#### Scenario: User reads cache control documentation
- **WHEN** a user views the cache control section in docs/deployment-patterns.md
- **THEN** they see an explanation that Dagger's function-level caching requires unique timestamps
- **AND** they see the example `dagger call deploy --cache-buster=$(date +%s)`
- **AND** they see that `$(date +%s)` provides a unique epoch timestamp on each invocation

### Requirement: All documentation examples are syntactically correct
All command examples across updated documentation SHALL be valid, copy-pasteable bash commands.

#### Scenario: User copies example command
- **WHEN** a user copies any command example from the updated documentation
- **THEN** the command executes without syntax errors
- **AND** the command uses the correct `--cache-buster=$(date +%s)` syntax
