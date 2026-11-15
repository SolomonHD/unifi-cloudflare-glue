# Spec: Plan Generation

## Purpose

Define Terraform plan inputs, execution behavior, and export formats.

## Requirements
### Requirement: Plan Function Signature

The module SHALL accept source, scoped authentication, state selection and explicit tool identity for non-mutating previews. Provider and credential-bearing backend inputs SHALL use secret-typed channels; live freshness SHALL be automatic.

#### Scenario: Plan function accepts authentication parameters
- **WHEN** a caller selects full, UniFi-only or Cloudflare-only planning
- **THEN** only credentials required for that scope are requested, using API-key or complete username/password UniFi authentication and secret Cloudflare tokens
- **AND** insecure TLS requires explicit opt-in

#### Scenario: Plan function accepts state management parameters
- **WHEN** a caller supplies a protected local-state input or remote-backend selection
- **THEN** those modes are mutually exclusive and credential-bearing backend input is Secret-typed with an explicit supported format

#### Scenario: Plan function accepts version control parameters
- **WHEN** no tool override is supplied
- **THEN** accepted exact tool identities are selected rather than latest tags

#### Scenario: Plan function accepts cache control parameters
- **WHEN** the caller supplies no timestamp or cache flag
- **THEN** live observations are fresh automatically without invalidating deterministic source generation

### Requirement: Plan Generation Process

Planning SHALL validate selected configuration and use the same scope, root, backend identity and resource address layout as the corresponding execution path without applying managed-resource changes.

#### Scenario: Generate plans for both modules
- **WHEN** the caller requests the full deployment preview
- **THEN** both configurations are validated and the existing combined-root state is planned once
- **AND** the preview does not create separate states for its component modules

#### Scenario: Plan execution order matches deployment
- **WHEN** the preview is compared with the corresponding execution mode
- **THEN** root, backend, resource addresses and dependency ordering agree
- **AND** incompatible state/root combinations stop before effects

### Requirement: Plan Output Formats

The `plan()` function MUST default to exportable artifacts that have been reviewed for secret disclosure, while raw Terraform plan formats MUST require explicit sensitive-artifact acknowledgement.

#### Scenario: Export safe default plan artifacts
- **GIVEN** Terraform has generated plans
- **WHEN** the caller exports the default plan result
- **THEN** the output contains a redacted human-readable plan and aggregated summary for each requested component
- **AND** the output does not contain binary plan files or raw JSON plan files

#### Scenario: Explicitly export sensitive plan artifacts
- **GIVEN** the caller has selected the sensitive-artifact option
- **WHEN** plan generation completes
- **THEN** the output may include Terraform binary and JSON plan files
- **AND** each sensitive artifact is owner-readable only
- **AND** a warning manifest explains that Terraform plans can contain credentials and sensitive values

#### Scenario: Provider credentials are absent from plan inputs
- **GIVEN** Terraform providers require Cloudflare or UniFi authentication
- **WHEN** the plan is generated in either output mode
- **THEN** provider credentials are supplied through provider-supported secret environment variables
- **AND** they are not supplied as Terraform input variables serialized into the plan

### Requirement: Plan Summary Generation

Planning SHALL provide accurate aggregated add/change/destroy counts and selected-scope metadata from structured action data, with malformed data treated as an error rather than a misleading zero-drift result.

#### Scenario: Generate plan summary file
- **WHEN** planning succeeds
- **THEN** the summary includes scope, add/change/destroy counts, timestamp, resolved Terraform/KCL identities and backend type
- **AND** sensitive plan values are not copied into the summary

#### Scenario: Parse resource counts from plan output
- **WHEN** structured action arrays contain creates, updates, deletes, replacements or no-ops
- **THEN** their string actions are counted correctly, replacements contribute create and delete, and no-ops contribute neither
- **AND** malformed actions fail summary verification instead of falling back to fragile phrase counting

### Requirement: Output Directory Structure

The `plan()` function MUST return a `dagger.Directory` whose contents match the selected artifact-sensitivity mode.

#### Scenario: Return safe default directory
- **GIVEN** plan generation completed without sensitive-artifact opt-in
- **WHEN** the user exports the returned directory
- **THEN** the directory contains redacted human-readable plans and `plan-summary.txt`
- **AND** it contains no `.tfplan` or raw plan `.json` files

#### Scenario: Return acknowledged sensitive directory
- **GIVEN** plan generation completed with sensitive-artifact opt-in
- **WHEN** the user exports the returned directory
- **THEN** the directory additionally contains the requested `.tfplan` and JSON files
- **AND** it contains a sensitivity warning manifest

### Requirement: Container Reference Management

The `plan()` function MUST preserve container references after Terraform plan execution to enable file export.

#### Scenario: Preserve container reference after plan execution
**Given:** Terraform plan command is executed in a container  
**When:** The plan completes  
**Then:** The function:
1. Assigns the post-execution container back to the variable: `container = container.with_exec(["terraform", "plan", ...])`
2. Uses the updated container reference for subsequent file exports
3. Does NOT use the pre-execution container for file access

#### Scenario: Export plan files from correct container
**Given:** Terraform plan has completed and container reference is preserved  
**When:** Exporting plan artifacts  
**Then:** The function:
- Accesses `container.file("/module/plan.tfplan")` from the POST-execution container
- Accesses `container.file("/module/plan.json")` from the POST-execution container
- Accesses `container.file("/module/plan.txt")` from the POST-execution container

### Requirement: State Management Consistency

Remote planning SHALL use the same remote-backend/root contract as deploy and destroy, with explicit Secret-typed backend configuration and no automatic host Directory write-back. A protected local-state preview is read-only and SHALL NOT imply support or authorization for local deploy/destroy; durable local effects remain deferred to DLR-1.

#### Scenario: Plan with persistent local state
- **WHEN** a supported local-state preview is requested
- **THEN** it uses the specified state and preserved module layout with explicit protected artifact custody

#### Scenario: Plan with remote backend
- **WHEN** S3 planning is selected with Secret-typed backend settings
- **THEN** initialization and refresh use the existing remote state identity and locking configuration

#### Scenario: Mutually exclusive state options
- **WHEN** both local state and a remote backend are supplied
- **THEN** validation fails nonzero before execution and explains the supported alternatives without disclosing backend contents

### Requirement: Authentication Validation

The `plan()` function MUST validate authentication parameters with the same logic as `deploy()` function.

#### Scenario: UniFi authentication mutual exclusivity
**Given:** User provides both API key and username/password  
**When:** They call `dagger call plan --unifi-api-key=env:KEY --unifi-username=env:USER --unifi-password=env:PASS`  
**Then:** The function returns error indicating authentication method conflict

#### Scenario: UniFi authentication completeness (username/password)
**Given:** User provides username without password  
**When:** They call `dagger call plan --unifi-username=env:USER`  
**Then:** The function returns error: `"✗ Failed: Both --unifi-username and --unifi-password required when using username/password authentication"`

#### Scenario: Valid API key authentication
**Given:** User provides UniFi API key  
**When:** They call `dagger call plan --unifi-api-key=env:UNIFI_API_KEY --cloudflare-token=env:CF_TOKEN ...`  
**Then:** The function accepts authentication and proceeds with plan generation

### Requirement: Cache Control

Live planning SHALL enforce automatic freshness at function and execution boundaries, without requiring or accepting an ineffective no-cache boolean as a guarantee.

#### Scenario: Force fresh execution with no-cache
- **WHEN** a caller attempts to use the removed no-cache interface
- **THEN** migration guidance identifies automatic live freshness rather than instructing the caller to create timestamps

#### Scenario: Custom cache buster value
- **WHEN** a supported transitional call includes a manual run label
- **THEN** it is handled only as bounded data and freshness is enforced independently

#### Scenario: Mutually exclusive cache control options
- **WHEN** unsupported legacy cache options are supplied
- **THEN** argument validation rejects them before contacting the backend or providers

### Requirement: Error Handling

Planning SHALL fail nonzero with useful sanitized diagnostics for execution, generation and argument errors, without exposing provider/backend output or proceeding after a required phase fails.

#### Scenario: Terraform plan failure
- **WHEN** Terraform planning fails
- **THEN** command status is unsuccessful, phase/exit metadata is retained and dependent work stops without reproducing raw provider output

#### Scenario: KCL generation failure
- **WHEN** source generation fails validation
- **THEN** planning fails with bounded non-secret validation context before provider operations

#### Scenario: Missing required parameters
- **WHEN** required selected-scope parameters are absent
- **THEN** argument validation fails before backend or provider access

### Requirement: Documentation

The `plan()` function MUST be documented with comprehensive examples and usage guidance.

#### Scenario: Function docstring includes usage example
**Given:** User inspects the function  
**When:** They run `dagger call plan --help`  
**Then:** The help output shows:
- Function description
- All parameter descriptions
- Example usage with realistic values
- Note about exporting with `export --path=./plans`

#### Scenario: README includes plan function documentation
**Given:** User reads the README  
**When:** They navigate to the "Dagger Functions" section  
**Then:** The documentation includes:
- `plan` function description and purpose
- Example with persistent local state
- Example with remote backend
- Explanation of output formats
- Link to plan summary format

#### Scenario: Changelog documents new feature
**Given:** User reads the CHANGELOG
**When:** They review the Unreleased section
**Then:** The changelog includes:
- "Added Terraform plan function" entry
- Description of capabilities
- Example usage snippet
- Security note about plan file contents

<!-- Requirements added by selective-plan-generation -->

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
Full previews SHALL preserve the existing combined Terraform root. Selective previews SHALL use the same qualified root and state ownership as the corresponding execution mode rather than choosing a different root solely because the operation is plan.

#### Scenario: Plan generation uses combined module
- **WHEN** the caller selects full deployment against the combined state
- **THEN** planning and execution both use the combined root with stable addresses

#### Scenario: Selective root matches state ownership
- **WHEN** a caller selects a standalone component
- **THEN** its preview and execution use the same previously qualified standalone state/root combination or reject an incompatible combination before mutation

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
Default plan output SHALL contain reviewed human-readable preview and summary artifacts only. Raw binary and JSON plans SHALL require explicit sensitive-artifact acknowledgement and protected storage.

#### Scenario: Plan output files
- **WHEN** the default result is exported
- **THEN** it contains plan text and an aggregated summary without raw plan JSON, binary state or credentials
- **AND** explicitly acknowledged raw plans retain owner-only permissions and handling warnings

### Requirement: Plan output has secret-disclosure regression coverage
The plan implementation MUST be tested with sentinel provider credentials to detect disclosure in default artifacts and command output.

#### Scenario: Default plan export is scanned
- **WHEN** automated tests generate and inspect a default plan result with sentinel secrets
- **THEN** no sentinel credential MUST appear in any exported file or captured execution output

### Requirement: Preview is not saved-plan execution approval
The interface SHALL state whether execution consumes the exact reviewed plan. A preview followed by independent replanning SHALL NOT be represented as approved saved-plan execution.

#### Scenario: Deploy follows preview
- **WHEN** a caller requests deployment after inspecting a preview
- **THEN** documentation and command guidance explain that deploy replans against fresh state and needs its own authorization
- **AND** raw preview artifacts are not implicitly promoted to execution inputs
