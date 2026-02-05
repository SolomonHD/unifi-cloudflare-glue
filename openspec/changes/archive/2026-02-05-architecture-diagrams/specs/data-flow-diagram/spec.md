## ADDED Requirements

### Requirement: Data flow SHALL show configuration transformation pipeline

The documentation SHALL include a data flow diagram illustrating the complete transformation from KCL configuration through validation to infrastructure deployment, including separate paths for UniFi and Cloudflare.

#### Scenario: Complete pipeline is visualized
- **WHEN** a user views the data flow diagram
- **THEN** they SHALL see the full path from main.k configuration through KCL validation, JSON generation, and Terraform apply

#### Scenario: Validation decision point is shown
- **WHEN** viewing the data flow
- **THEN** the diagram SHALL show a decision point after KCL validation with success and error paths

### Requirement: JSON generation SHALL be depicted as parallel outputs

The diagram SHALL show that KCL generates both UniFi JSON and Cloudflare JSON as parallel outputs from a single configuration source.

#### Scenario: Split into provider-specific outputs
- **WHEN** viewing JSON generation step
- **THEN** the diagram SHALL show one configuration source splitting into two output paths (UniFi and Cloudflare)

### Requirement: Infrastructure creation SHALL show sequential phases

The diagram SHALL illustrate that UniFi DNS is created first, followed by Cloudflare tunnel and edge DNS.

#### Scenario: Phase ordering is visible
- **WHEN** viewing the infrastructure deployment section
- **THEN** the diagram SHALL clearly show UniFi resources created before Cloudflare resources

#### Scenario: Final state is indicated
- **WHEN** both infrastructure phases complete
- **THEN** the diagram SHALL show the end state with both local DNS and tunnel/edge DNS created
