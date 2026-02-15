## ADDED Requirements

### Requirement: Working directory uses explicit boolean logic
The system SHALL use an explicit `using_persistent_state` boolean variable to determine working directory setup, avoiding fragile string checks on container objects.

#### Scenario: deploy_unifi uses boolean for workdir selection
- **WHEN** `deploy_unifi()` sets up the working directory
- **THEN** it SHALL use `using_persistent_state = state_dir is not None`
- **AND** it SHALL NOT use string checks like `"/module" in str(ctr)`
- **AND** workdir SHALL be `/state` when `using_persistent_state` is True
- **AND** workdir SHALL be `/module` when `using_persistent_state` is False

#### Scenario: deploy_cloudflare uses boolean for workdir selection
- **WHEN** `deploy_cloudflare()` sets up the working directory
- **THEN** it SHALL use `using_persistent_state = state_dir is not None`
- **AND** it SHALL NOT use string checks like `"/module" in str(ctr)`
- **AND** workdir SHALL be `/state` when `using_persistent_state` is True
- **AND** workdir SHALL be `/module` when `using_persistent_state` is False

#### Scenario: destroy uses boolean for Cloudflare workdir selection
- **WHEN** `destroy()` sets up working directory for Cloudflare phase
- **THEN** it SHALL use `using_persistent_state = state_dir is not None`
- **AND** it SHALL NOT use string checks like `"/module" in str(ctr)`
- **AND** workdir SHALL be `/state` when `using_persistent_state` is True
- **AND** workdir SHALL be `/module` when `using_persistent_state` is False

#### Scenario: destroy uses boolean for UniFi workdir selection
- **WHEN** `destroy()` sets up working directory for UniFi phase
- **THEN** it SHALL use `using_persistent_state = state_dir is not None`
- **AND** it SHALL NOT use string checks like `"/module" in str(ctr)`
- **AND** workdir SHALL be `/state` when `using_persistent_state` is True
- **AND** workdir SHALL be `/module` when `using_persistent_state` is False

### Requirement: State directory setup follows consistent pattern
The system SHALL follow a consistent pattern for state directory setup when `using_persistent_state` is True.

#### Scenario: State directory is mounted correctly
- **WHEN** `using_persistent_state` is True
- **THEN** the state directory SHALL be mounted at `/state` using `with_directory("/state", state_dir)`
- **AND** module files SHALL be copied from `/module` to `/state`
- **AND** the copy operation SHALL complete before changing workdir

#### Scenario: Working directory is set to state after copy
- **WHEN** module files have been copied to `/state`
- **THEN** the working directory SHALL be set to `/state` using `with_workdir("/state")`
- **AND** all subsequent operations SHALL execute in `/state`

#### Scenario: Ephemeral state uses module directory
- **WHEN** `using_persistent_state` is False
- **THEN** the working directory SHALL be set to `/module` using `with_workdir("/module")`
- **AND** no state directory mounting SHALL occur
- **AND** Terraform SHALL operate directly in `/module`

### Requirement: String-based container checks are eliminated
The system SHALL NOT use string checks on container objects to determine working directory or other logic.

#### Scenario: No string checks in deploy_unifi
- **WHEN** reviewing `deploy_unifi()` implementation
- **THEN** there SHALL be no occurrences of `str(ctr)` for logic decisions
- **AND** there SHALL be no string containment checks like `"/module" in str(ctr)`

#### Scenario: No string checks in deploy_cloudflare
- **WHEN** reviewing `deploy_cloudflare()` implementation
- **THEN** there SHALL be no occurrences of `str(ctr)` for logic decisions
- **AND** there SHALL be no string containment checks like `"/module" in str(ctr)`

#### Scenario: No string checks in destroy
- **WHEN** reviewing `destroy()` implementation
- **THEN** there SHALL be no occurrences of `str(ctr)` for logic decisions
- **AND** there SHALL be no string containment checks like `"/module" in str(ctr)`

### Requirement: Container reference is maintained through workdir changes
The system SHALL preserve container references when changing working directories.

#### Scenario: Workdir change preserves container reference
- **WHEN** calling `with_workdir()` on a container
- **THEN** the result SHALL be assigned back to the container variable
- **AND** subsequent operations SHALL use the reassigned variable
- **AND** files from previous operations SHALL remain accessible
