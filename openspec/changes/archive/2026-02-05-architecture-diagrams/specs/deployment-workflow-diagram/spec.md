## ADDED Requirements

### Requirement: Deployment workflow SHALL show interaction sequence

The documentation SHALL include a sequence diagram showing the step-by-step interaction between User, Dagger, Terraform, UniFi, and Cloudflare during deployment.

#### Scenario: User initiates deployment
- **WHEN** viewing the deployment workflow diagram
- **THEN** the diagram SHALL show the user invoking the `dagger call deploy` command as the starting point

#### Scenario: Initialization is depicted
- **WHEN** Dagger processes the deployment request
- **THEN** the diagram SHALL show configuration generation and terraform init steps

### Requirement: Deployment phases SHALL be visually separated

The diagram SHALL use visual grouping (colored rectangles or swim lanes) to distinguish Phase 1 (UniFi DNS) from Phase 2 (Cloudflare Tunnel and DNS).

#### Scenario: Phase 1 is clearly marked
- **WHEN** viewing the deployment sequence
- **THEN** UniFi DNS creation SHALL be contained in a visually distinct Phase 1 section

#### Scenario: Phase 2 follows Phase 1
- **WHEN** viewing the deployment sequence
- **THEN** Cloudflare operations SHALL be contained in a Phase 2 section that visually follows Phase 1

### Requirement: Success responses SHALL be indicated

The diagram SHALL show success responses flowing back from external services through Terraform to Dagger and finally to the user.

#### Scenario: UniFi confirms DNS creation
- **WHEN** UniFi successfully creates DNS records
- **THEN** the diagram SHALL show a success response arrow from UniFi back to Terraform

#### Scenario: Final completion message
- **WHEN** all phases complete successfully
- **THEN** the diagram SHALL show Dagger returning a completion confirmation to the user

### Requirement: Error handling paths SHALL be identifiable

The diagram SHALL indicate where errors might occur and how they are communicated back to the user.

#### Scenario: Terraform failure communication
- **WHEN** Terraform encounters an error
- **THEN** the diagram SHALL show the error path back to Dagger and the user
