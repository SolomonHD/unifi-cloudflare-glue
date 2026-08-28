## ADDED Requirements

### Requirement: Same-family UniFi provider upgrades require before-and-after plans
An upgrade within the `filipowm/unifi` provider family MUST be verified against identical production configuration and state before and after changing the version selection.

#### Scenario: Provider version selection changes from v1.0.0 to v1.1.x
- **WHEN** the provider constraint and initialization selection are updated
- **THEN** both production plans MUST complete through API-key authentication
- **AND** each plan MUST report 0 add, 0 change, and 0 destroy

### Requirement: Provider upgrade claims match evidence
Release notes and repository documentation MUST distinguish empirically reproduced fixes from maintenance upgrades.

#### Scenario: v1.1.x baseline is documented
- **WHEN** the change log and upgrade notes describe the current-provider update
- **THEN** they MUST NOT claim it fixes API-key authentication
- **AND** they MUST identify the Network 10.x `UnknownUser` workaround as client registration behavior
