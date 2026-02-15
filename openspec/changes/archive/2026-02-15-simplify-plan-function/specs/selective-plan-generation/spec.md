## ADDED Requirements

### Requirement: Plan function supports selective component planning
The `plan()` function SHALL support generating Terraform plans for individual components (UniFi-only or Cloudflare-only) in addition to the default full deployment planning.

#### Scenario: Full deployment plan (default behavior)
- **WHEN** user invokes `plan()` without `--unifi-only` or `--cloudflare-only` flags
- **THEN** the function SHALL generate plans for both UniFi DNS and Cloudflare Tunnels
- **AND** the function SHALL require both UniFi and Cloudflare credentials

#### Scenario: UniFi-only plan generation
- **WHEN** user invokes `plan()` with `--unifi-only` flag
- **THEN** the function SHALL generate plan only for UniFi DNS component
- **AND** the function SHALL NOT require Cloudflare credentials
- **AND** the function SHALL NOT generate Cloudflare configuration

#### Scenario: Cloudflare-only plan generation
- **WHEN** user invokes `plan()` with `--cloudflare-only` flag
- **THEN** the function SHALL generate plan only for Cloudflare Tunnel component
- **AND** the function SHALL NOT require UniFi credentials
- **AND** the function SHALL NOT generate UniFi configuration

### Requirement: Mutual exclusion of selective deployment flags
The `plan()` function SHALL validate that `--unifi-only` and `--cloudflare-only` flags are mutually exclusive.

#### Scenario: Both flags provided
- **WHEN** user invokes `plan()` with both `--unifi-only` and `--cloudflare-only` flags
- **THEN** the function SHALL return an error indicating the flags are mutually exclusive

### Requirement: Plan function uses combined Terraform module
The `plan()` function SHALL use the combined Terraform module at `terraform/modules/glue/` for all plan generation operations.

#### Scenario: Plan generation uses combined module
- **WHEN** user invokes `plan()` with any valid flag combination
- **THEN** the function SHALL mount and use the `terraform/modules/glue/` module
- **AND** the function SHALL pass appropriate configuration files based on selected components

### Requirement: Conditional credential requirements
The `plan()` function SHALL adjust credential requirements based on the selected deployment scope.

#### Scenario: Full deployment credential requirements
- **WHEN** user invokes `plan()` without selective flags
- **THEN** the function SHALL require UniFi credentials (API key OR username/password)
- **AND** the function SHALL require Cloudflare credentials (token, account ID, zone name)

#### Scenario: UniFi-only credential requirements
- **WHEN** user invokes `plan()` with `--unifi-only` flag
- **THEN** the function SHALL require UniFi credentials (API key OR username/password)
- **AND** the function SHALL NOT require Cloudflare credentials

#### Scenario: Cloudflare-only credential requirements
- **WHEN** user invokes `plan()` with `--cloudflare-only` flag
- **THEN** the function SHALL require Cloudflare credentials (token, account ID, zone name)
- **AND** the function SHALL NOT require UniFi credentials

### Requirement: Plan artifact generation for selected components
The `plan()` function SHALL generate plan artifacts appropriate to the selected components.

#### Scenario: Full deployment plan artifacts
- **WHEN** user invokes `plan()` without selective flags
- **THEN** the function SHALL generate plan artifacts for both components
- **AND** the output directory SHALL contain combined plan files

#### Scenario: UniFi-only plan artifacts
- **WHEN** user invokes `plan()` with `--unifi-only` flag
- **THEN** the function SHALL generate only UniFi-related plan artifacts
- **AND** the plan summary SHALL reflect UniFi-only planning

#### Scenario: Cloudflare-only plan artifacts
- **WHEN** user invokes `plan()` with `--cloudflare-only` flag
- **THEN** the function SHALL generate only Cloudflare-related plan artifacts
- **AND** the plan summary SHALL reflect Cloudflare-only planning

### Requirement: Plan output directory structure
The `plan()` function SHALL return a Directory containing standardized plan artifacts.

#### Scenario: Plan output files
- **WHEN** plan generation completes successfully
- **THEN** the returned Directory SHALL contain:
  - `plan.tfplan` - Binary plan file for terraform apply
  - `plan.json` - JSON representation of the plan
  - `plan.txt` - Human-readable plan output
  - `plan-summary.txt` - Summary with resource counts and component information
