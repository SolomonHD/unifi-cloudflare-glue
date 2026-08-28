## REMOVED Requirements

### Requirement: Deploy Cloudflare success message includes credential retrieval guidance
**Reason**: The standalone `deploy_cloudflare()` public function was removed when deployment was consolidated into `deploy()` with component-selection flags, so the old requirement and its tests target an unsupported API.

**Migration**: Exercise Cloudflare-only deployment and credential-retrieval guidance through `deploy(..., cloudflare_only=True)` and the generated Dagger CLI `deploy --cloudflare-only` option.

## ADDED Requirements

### Requirement: Selective combined deployment includes applicable credential guidance
The combined `deploy()` function SHALL include tunnel credential-retrieval guidance after a successful deployment that includes Cloudflare, including a Cloudflare-only deployment, and MUST omit that guidance when Cloudflare is excluded or deployment fails.

#### Scenario: Cloudflare-only combined deployment succeeds
- **WHEN** `deploy()` completes successfully with Cloudflare selected and UniFi excluded
- **THEN** the result MUST include credential-retrieval guidance using the actual deployment and backend parameters

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
