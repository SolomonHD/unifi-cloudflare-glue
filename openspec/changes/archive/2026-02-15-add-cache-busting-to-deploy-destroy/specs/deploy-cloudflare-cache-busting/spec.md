## ADDED Requirements

### Requirement: Deploy Cloudflare function accepts cache control parameters
The `deploy_cloudflare()` function SHALL accept `no_cache` and `cache_buster` parameters to control Dagger's caching behavior during Cloudflare tunnel configuration deployment.

#### Scenario: User provides no_cache flag
- **WHEN** user invokes `deploy_cloudflare()` with `no_cache=True`
- **THEN** the function SHALL calculate an effective cache buster using the current epoch timestamp
- **AND** the function SHALL set the `CACHE_BUSTER` environment variable on the Terraform container before execution

#### Scenario: User provides custom cache_buster
- **WHEN** user invokes `deploy_cloudflare()` with `cache_buster="custom-key"`
- **THEN** the function SHALL use the provided cache buster value as the effective cache buster
- **AND** the function SHALL set the `CACHE_BUSTER` environment variable on the Terraform container before execution

#### Scenario: User provides both flags
- **WHEN** user invokes `deploy_cloudflare()` with both `no_cache=True` and `cache_buster="custom-key"`
- **THEN** the function SHALL raise a ValueError with message "✗ Failed: Cannot use both --no-cache and --cache-buster"

#### Scenario: Default behavior without cache control
- **WHEN** user invokes `deploy_cloudflare()` without `no_cache` or `cache_buster` parameters
- **THEN** the function SHALL use default values (`no_cache=False`, `cache_buster=""`)
- **AND** no cache buster environment variable SHALL be set on the Terraform container

#### Scenario: Cache buster is set after container setup
- **WHEN** the effective cache buster has a value
- **THEN** the `CACHE_BUSTER` environment variable SHALL be set on the container AFTER all file mounting and setup operations
- **AND** BEFORE the terraform init/apply commands are executed
