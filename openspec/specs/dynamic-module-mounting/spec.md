## ADDED Requirements

### Requirement: Mount correct Terraform module based on detection
The [`get_tunnel_secrets`](../../../../../src/main/main.py:2713) function SHALL mount the appropriate Terraform module directory structure based on detected module type.

#### Scenario: Mount cloudflare-tunnel module for cloudflare-only deployment
- **WHEN** cloudflare-tunnel module is detected
- **THEN** function SHALL mount `terraform/modules/cloudflare-tunnel` at `/module`

#### Scenario: Mount glue module structure for combined deployment
- **WHEN** glue module is detected
- **THEN** function SHALL mount `terraform/modules/` at `/module` and set working directory to `/module/glue`

#### Scenario: Module mounting with ephemeral state
- **WHEN** using ephemeral state management
- **THEN** module SHALL be mounted without state directory

#### Scenario: Module mounting with persistent local state
- **WHEN** using `--state-dir` for persistent state
- **THEN** function SHALL copy mounted module to state directory and work there

#### Scenario: Module mounting with remote backend
- **WHEN** using remote backend configuration
- **THEN** function SHALL mount module and generate backend.tf appropriately

### Requirement: Preserve existing backend.tf generation
The function SHALL generate backend.tf in the correct location based on mounted module structure.

#### Scenario: Generate backend.tf for cloudflare-tunnel module
- **WHEN** using cloudflare-tunnel module with remote backend
- **THEN** backend.tf SHALL be created at `/module/backend.tf`

#### Scenario: Generate backend.tf for glue module
- **WHEN** using glue module with remote backend
- **THEN** backend.tf SHALL be created at `/module/glue/backend.tf`

### Requirement: Handle module mounting failures
The function SHALL provide clear errors when module directories cannot be accessed.

#### Scenario: Module directory not found
- **WHEN** expected module directory does not exist in source
- **THEN** function SHALL return error indicating missing module path

#### Scenario: Module directory access denied
- **WHEN** module directory permissions prevent access
- **THEN** function SHALL return error indicating permission issue
