## ADDED Requirements

### Requirement: Destroy function accepts cache control parameters
The `destroy()` function SHALL accept `no_cache` and `cache_buster` parameters to control Dagger's caching behavior.

#### Scenario: User provides no_cache flag
- **WHEN** user invokes `destroy()` with `no_cache=True`
- **THEN** the function SHALL calculate an effective cache buster using the current epoch timestamp
- **AND** the function SHALL set the `CACHE_BUSTER` environment variable on Cloudflare and UniFi containers

#### Scenario: User provides custom cache_buster
- **WHEN** user invokes `destroy()` with `cache_buster="custom-key"`
- **THEN** the function SHALL use the provided cache buster value as the effective cache buster
- **AND** the function SHALL set the `CACHE_BUSTER` environment variable on Cloudflare and UniFi containers

#### Scenario: User provides both flags
- **WHEN** user invokes `destroy()` with both `no_cache=True` and `cache_buster="custom-key"`
- **THEN** the function SHALL raise a ValueError with message "✗ Failed: Cannot use both --no-cache and --cache-buster"

#### Scenario: Default behavior without cache control
- **WHEN** user invokes `destroy()` without `no_cache` or `cache_buster` parameters
- **THEN** the function SHALL use default values (`no_cache=False`, `cache_buster=""`)
- **AND** no cache buster environment variable SHALL be set on containers
