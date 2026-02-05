## ADDED Requirements

### Requirement: State management options SHALL be presented as a decision tree

The documentation SHALL include a diagram showing how to choose between ephemeral state, persistent local state, and remote backend state based on use case requirements.

#### Scenario: Three main options are visible
- **WHEN** viewing the state management diagram
- **THEN** the decision tree SHALL present three primary branches: Development (ephemeral), Solo Developer (persistent local), and Team/Production (remote backend)

#### Scenario: Decision criteria are clear
- **WHEN** evaluating which option to choose
- **THEN** each branch SHALL indicate the use case that makes it appropriate

### Requirement: Each option SHALL show trade-offs

The diagram SHALL include key characteristics of each state management approach including persistence, setup complexity, and cloud costs.

#### Scenario: Ephemeral state characteristics
- **WHEN** viewing the ephemeral state option
- **THEN** the diagram SHALL indicate: container-only storage, lost on exit, no setup required

#### Scenario: Persistent local characteristics
- **WHEN** viewing the persistent local option
- **THEN** the diagram SHALL indicate: local filesystem storage, requires --state-dir flag, no cloud costs

#### Scenario: Remote backend choices
- **WHEN** viewing the remote backend option
- **THEN** the diagram SHALL show sub-options for S3, Azure Blob, and GCS

### Requirement: S3 locking options SHALL be detailed

The diagram SHALL show that S3 backends have two locking mechanisms: S3 lockfile (Terraform 1.9+) and DynamoDB (all versions).

#### Scenario: S3 locking decision
- **WHEN** choosing S3 as the remote backend
- **THEN** the diagram SHALL present a sub-decision between S3 lockfile and DynamoDB locking

#### Scenario: Version compatibility is indicated
- **WHEN** viewing S3 locking options
- **THEN** the diagram SHALL note that S3 lockfile requires Terraform 1.9+ while DynamoDB works with all versions
