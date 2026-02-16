## ADDED Requirements

### Requirement: Detect deployment module from Terraform state
The [`get_tunnel_secrets`](../../../../../src/main/main.py:2713) function SHALL automatically detect which Terraform module (cloudflare-tunnel or glue) created the state by inspecting available Terraform outputs before initializing.

#### Scenario: Cloudflare-only deployment detected
- **WHEN** Terraform state contains `tunnel_ids` output (without prefix)
- **THEN** function SHALL detect cloudflare-tunnel module

#### Scenario: Combined deployment detected  
- **WHEN** Terraform state contains `cloudflare_tunnel_ids` output (with prefix)
- **THEN** function SHALL detect glue module

#### Scenario: Detection with ephemeral state
- **WHEN** using ephemeral state management
- **THEN** detection SHALL work by querying outputs directly

#### Scenario: Detection with persistent local state
- **WHEN** using `--state-dir` for persistent local state
- **THEN** detection SHALL work after mounting state directory

#### Scenario: Detection with remote backend
- **WHEN** using remote backend with `--backend-type` and `--backend-config-file`
- **THEN** detection SHALL work after terraform init with backend config

### Requirement: Provide clear detection feedback
The function SHALL include detection results in error messages and output to help users understand which module was detected.

#### Scenario: Detection indicated in output
- **WHEN** function executes successfully
- **THEN** output SHALL clearly indicate which module type was detected

#### Scenario: Detection shown in errors
- **WHEN** function fails to retrieve outputs
- **THEN** error message SHALL show available outputs and indicate which module was expected

### Requirement: Handle detection failures gracefully
The function SHALL handle cases where state exists but outputs are missing or ambiguous.

#### Scenario: No outputs available
- **WHEN** Terraform state has no outputs
- **THEN** function SHALL return error indicating no tunnels found

#### Scenario: Unexpected output structure
- **WHEN** Terraform state has outputs but neither expected pattern
- **THEN** function SHALL fall back to cloudflare-tunnel module for backward compatibility

#### Scenario: Corrupted state
- **WHEN** Terraform state is corrupted or invalid
- **THEN** function SHALL return clear error indicating state issues
