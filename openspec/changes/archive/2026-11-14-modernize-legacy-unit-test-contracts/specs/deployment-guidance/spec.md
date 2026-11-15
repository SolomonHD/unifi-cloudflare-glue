## REMOVED Requirements

### Requirement: Deploy Cloudflare success message includes credential retrieval guidance
**Reason**: The standalone `deploy_cloudflare()` public function was removed when deployment was consolidated into `deploy()` with component-selection flags, so the old requirement and its tests target an unsupported API.

**Migration**: Exercise Cloudflare-only deployment and credential-retrieval guidance through `deploy(..., cloudflare_only=True)` and the generated Dagger CLI `deploy --cloudflare-only` option.

## ADDED Requirements

### Requirement: Selective combined deployment includes applicable credential guidance
The combined `deploy()` function SHALL include tunnel credential-retrieval guidance after a successful deployment that includes Cloudflare, including a Cloudflare-only deployment, and MUST omit that guidance when Cloudflare is excluded or deployment fails.

#### Scenario: Cloudflare-only combined deployment succeeds
- **WHEN** `deploy()` completes successfully with Cloudflare selected and UniFi excluded
- **THEN** the result MUST include credential-retrieval guidance using actual account, zone, and backend selections and explicitly labeled placeholders for unavailable original host paths

#### Scenario: Combined deployment excludes Cloudflare
- **WHEN** `deploy()` completes successfully with UniFi selected and Cloudflare excluded
- **THEN** the result MUST NOT include Cloudflare tunnel credential-retrieval guidance

#### Scenario: Combined deployment fails
- **WHEN** `deploy()` fails before completing the selected Cloudflare deployment
- **THEN** a success guidance section MUST NOT be emitted

### Requirement: Deployment guidance tests use supported public functions
Deployment-guidance unit tests MUST invoke the supported combined deployment interface and MUST NOT require compatibility wrappers for deleted standalone functions.

#### Scenario: Guidance unit tests construct the module
- **WHEN** deployment-guidance tests exercise Cloudflare-only, UniFi-only, or combined behavior
- **THEN** they MUST call `deploy()` with the corresponding selection flags
- **AND** their mocks MUST match the current combined Terraform execution path

### Requirement: Guidance is parameter-correct and secret-safe
Guidance SHALL describe supported credential retrieval without emitting resolved credentials or raw state, using actual non-secret account, zone, and backend selections. Original host paths unavailable from opaque Dagger inputs MUST be represented by clearly labeled, shell-quoted placeholders with instructions to reuse deployment inputs; no new path-hint parameters are required.

#### Scenario: Local remote or persistent-state deployment succeeds
- **WHEN** Cloudflare is included in a successful deployment using a local backend, remote backend, or explicit persistent state
- **THEN** guidance MUST use the actual account, zone, and backend type and include only applicable source/backend/state flags
- **AND** original source, backend-file, and state-directory paths MUST be explicitly labeled placeholders, not invented conventional paths
- **AND** guidance MUST instruct the caller to replace placeholders with the same inputs used for deployment
- **AND** secret inputs MUST remain runtime references rather than rendered values

## MODIFIED Requirements

### Requirement: Full deploy success message includes credential retrieval guidance
After successful full deployment via `deploy()` using one combined Terraform operation, the final summary SHALL include clear instructions for retrieving tunnel credentials.

#### Scenario: Both UniFi and Cloudflare deployments succeed
- **WHEN** the combined operation for both components succeeds
- **THEN** the final summary MUST include a success indicator, a labeled credential-retrieval section, supported Dagger retrieval guidance with actual account/zone/backend selections and a labeled KCL-source path placeholder, an installation example, and the example documentation link

#### Scenario: UniFi succeeds but Cloudflare fails
- **WHEN** a combined operation partially affects UniFi but fails before completing the selected Cloudflare deployment
- **THEN** the final summary MUST NOT include success credential-retrieval guidance
- **AND** tests MUST NOT require separate UniFi and Cloudflare apply cycles

#### Scenario: UniFi fails before Cloudflare deployment
- **WHEN** the combined operation fails before completing the selected components
- **THEN** the final summary MUST NOT include success credential-retrieval guidance

### Requirement: Guidance commands use actual deployment parameters
Credential retrieval guidance SHALL use actual account, zone, and backend selections while clearly distinguishing unavailable original host paths from known parameter values.

#### Scenario: Dagger command reflects actual parameter values
- **WHEN** a successful deployment includes Dagger retrieval guidance
- **THEN** the command MUST include the actual account ID, zone name, and applicable backend type
- **AND** unavailable original source, backend-file, and state-directory paths MUST be shell-quoted placeholders with instructions to reuse deployment inputs
- **AND** it MUST NOT imply that conventional example paths are the original deployment paths

#### Scenario: Command formatting includes line continuations
- **WHEN** guidance includes a multi-parameter command
- **THEN** parameters MUST use consistent indentation and line-continuation backslashes

### Requirement: Deploy function uses combined Terraform module
The `deploy()` function SHALL use `terraform/modules/glue/` for full deployment and the current provider-specific module for selective deployment, with one Terraform init/apply cycle for every scope.
Historical scenario titles are retained as identifiers; their bodies define the reconciled module selection.

#### Scenario: Full deployment uses combined module
- **WHEN** `deploy()` runs without selective flags
- **THEN** it MUST apply both providers using `terraform/modules/glue/` in one operation

#### Scenario: UniFi-only deployment uses combined module
- **WHEN** the combined `deploy()` entry point runs with `unifi_only`
- **THEN** it MUST use `terraform/modules/unifi-dns/`
- **AND** unselected provider credentials and configuration generation MUST NOT be required
- **AND** it MUST NOT run separate UniFi and Cloudflare apply cycles

#### Scenario: Cloudflare-only deployment uses combined module
- **WHEN** the combined `deploy()` entry point runs with `cloudflare_only`
- **THEN** it MUST use `terraform/modules/cloudflare-tunnel/`
- **AND** unselected provider credentials and configuration generation MUST NOT be required
- **AND** it MUST NOT run separate UniFi and Cloudflare apply cycles

### Requirement: Guidance formatting improves readability
Credential retrieval guidance SHALL use visual separators, a labeled section,
and separate numbered options for supported Dagger retrieval and cloudflared
installation without requiring raw Terraform output instructions.

#### Scenario: Visual separation from deployment logs
- **WHEN** a successful deployment includes credential retrieval guidance
- **THEN** the section MUST have dash separators and a clearly labeled header

#### Scenario: Multi-step instructions
- **WHEN** guidance describes retrieval and installation
- **THEN** it MUST label Dagger retrieval as Option 1 and installation as Option 2 on separate lines
- **AND** it MUST NOT require printing raw Terraform state or token output
