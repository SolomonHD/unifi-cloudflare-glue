## ADDED Requirements

### Requirement: Embedded Terraform modules load from module source
The Dagger module SHALL load embedded Terraform modules from its own source directory, regardless of where the module is called from.

#### Scenario: Module called from external project
- **WHEN** the module is called from an external project (e.g., `portainer-docker-compose`)
- **AND** a function attempts to load the UniFi DNS Terraform module
- **THEN** the module SHALL be loaded from `unifi-cloudflare-glue/terraform/modules/unifi-dns/`
- **AND** NOT from the calling project's directory

#### Scenario: Module called locally
- **WHEN** the module is called from within its own repository
- **AND** a function attempts to load the Cloudflare Tunnel Terraform module
- **THEN** the module SHALL be loaded from `unifi-cloudflare-glue/terraform/modules/cloudflare-tunnel/`

### Requirement: Consistent module loading pattern
All functions that load embedded Terraform modules SHALL use the same Dagger API pattern.

#### Scenario: Deploy functions use correct pattern
- **WHEN** `deploy_unifi()` or `deploy_cloudflare()` is called
- **THEN** Terraform modules SHALL be loaded using `dagger.dag.current_module().source().directory("terraform/modules/...")`
- **AND** NOT using `dagger.dag.directory().directory("terraform/modules/...")`

#### Scenario: Plan function uses correct pattern
- **WHEN** `plan()` is called for either UniFi or Cloudflare
- **THEN** Terraform modules SHALL be loaded using `dagger.dag.current_module().source().directory("terraform/modules/...")`

#### Scenario: Destroy function uses correct pattern
- **WHEN** `destroy()` is called for either UniFi or Cloudflare
- **THEN** Terraform modules SHALL be loaded using `dagger.dag.current_module().source().directory("terraform/modules/...")`

#### Scenario: Integration test uses correct pattern
- **WHEN** `test_integration()` is called
- **THEN** The UniFi DNS Terraform module SHALL be loaded using `dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")`

#### Scenario: Tunnel secrets function uses correct pattern
- **WHEN** `get_tunnel_secrets()` is called
- **THEN** The Cloudflare Tunnel Terraform module SHALL be loaded using `dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")`

### Requirement: Error handling preserved
The fix SHALL preserve existing error handling patterns around module loading.

#### Scenario: Module loading error is caught
- **WHEN** Terraform module loading fails for any reason
- **THEN** the existing try/except blocks SHALL catch the error
- **AND** return an appropriate error message to the caller
