## ADDED Requirements

### Requirement: Deploy Cloudflare success message includes credential retrieval guidance
After successful Cloudflare tunnel deployment via [`deploy_cloudflare()`](../../../../src/main/main.py:422-571), the success message SHALL include clear, actionable instructions for retrieving tunnel credentials using both Terraform and Dagger commands.

#### Scenario: Successful deploy_cloudflare with local backend
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) completes successfully with local backend
- **THEN** success message includes:
  - Success indicator and backend type
  - Section header "Next Step: Retrieve Tunnel Credentials"
  - Terraform output command: `terraform output -json cloudflare_tunnel_tokens`
  - Dagger command with actual deployment parameters (account ID, zone name, source directory)
  - `cloudflared service install` command example
  - Link to example documentation

#### Scenario: Successful deploy_cloudflare with remote backend
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) completes successfully with remote backend (e.g., S3, GCS)
- **THEN** success message includes:
  - Backend type information
  - Credential retrieval guidance
  - Dagger command WITH backend-specific flags (`--backend-type`, `--backend-config-file`)

#### Scenario: Successful deploy_cloudflare with persistent local state
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) completes successfully with mounted state directory
- **THEN** success message includes:
  - State persistence indicator
  - Dagger command WITH `--state-dir` flag

#### Scenario: Failed deploy_cloudflare
- **WHEN** [`deploy_cloudflare()`](../../../../src/main/main.py:422-571) fails
- **THEN** success message MUST NOT include credential retrieval guidance

### Requirement: Full deploy success message includes credential retrieval guidance
After successful full deployment via [`deploy()`](../../../../src/main/main.py:574-742) where both UniFi and Cloudflare phases succeed, the final summary SHALL include clear instructions for retrieving tunnel credentials.

#### Scenario: Both UniFi and Cloudflare deployments succeed
- **WHEN** [`deploy()`](../../../../src/main/main.py:574-742) completes with both phases successful
- **THEN** final summary includes:
  - Success summary indicator
  - Section header "Next Step: Retrieve Tunnel Credentials"
  - Dagger command with KCL source directory (`--source=./kcl`)
  - Dagger command with actual deployment parameters
  - Backend-specific flags if applicable
  - `cloudflared service install` command example
  - Link to example documentation

#### Scenario: UniFi succeeds but Cloudflare fails
- **WHEN** [`deploy()`](../../../../src/main/main.py:574-742) completes with UniFi success but Cloudflare failure
- **THEN** final summary MUST NOT include credential retrieval guidance

#### Scenario: UniFi fails before Cloudflare deployment
- **WHEN** [`deploy()`](../../../../src/main/main.py:574-742) fails at UniFi phase
- **THEN** final summary MUST NOT include credential retrieval guidance

### Requirement: Guidance commands use actual deployment parameters
Credential retrieval guidance in success messages SHALL use the exact parameters from the deployment function call, not placeholder values.

#### Scenario: Dagger command reflects actual parameter values
- **WHEN** success message includes Dagger command guidance
- **THEN** command MUST include:
  - Actual Cloudflare account ID from deployment
  - Actual zone name from deployment
  - Actual backend type if not local
  - Actual backend config file path if provided
  - Actual state directory path if provided

#### Scenario: Command formatting includes line continuations
- **WHEN** success message includes multi-parameter Dagger command
- **THEN** command MUST use line continuation backslashes (`\`) for readability
- **AND** parameters MUST be indented consistently

### Requirement: Guidance formatting improves readability
Credential retrieval guidance SHALL use visual separators and formatting to distinguish it from deployment output.

#### Scenario: Visual separation from deployment logs
- **WHEN** success message includes guidance section
- **THEN** guidance MUST be preceded by separator line (dashes)
- **AND** guidance MUST be followed by separator line
- **AND** section header MUST be clearly labeled

#### Scenario: Multi-step instructions
- **WHEN** guidance includes multiple retrieval options
- **THEN** options MUST be numbered (1. Terraform, 2. Dagger, 3. Install)
- **AND** each step MUST be on separate lines for clarity
