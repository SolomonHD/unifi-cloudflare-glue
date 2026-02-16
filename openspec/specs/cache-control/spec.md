## REMOVED Requirements

### Requirement: Boolean no_cache parameter
**Reason**: The `no_cache` boolean parameter was ineffective due to Dagger's function-level caching behavior. When passed as a static boolean value (`True`), it became part of the function's cache key, causing Dagger to return cached results instead of bypassing the cache.

**Migration**: Use `--cache-buster=$(date +%s)` instead of `--no-cache`. This provides a unique value on each invocation, correctly bypassing Dagger's cache.

```bash
# Before (removed, never worked correctly)
dagger call deploy --kcl-source=./kcl --no-cache

# After (correct approach)
dagger call deploy --kcl-source=./kcl --cache-buster=$(date +%s)
```

#### Scenario: Cache bypass with timestamp
dagger call deploy --kcl-source=./kcl --cache-buster=$(date +%s)

## MODIFIED Requirements

### Requirement: Deploy function supports cache busting
The `deploy` function SHALL support cache busting through the `cache_buster` parameter. The function SHALL use the provided cache buster value to invalidate Dagger's cache at multiple levels.

#### Scenario: Deploy with cache buster
- **WHEN** the user invokes `deploy` with `--cache-buster=unique-value-123`
- **THEN** the function uses `unique-value-123` to bust cache on KCL source directory
- **AND** the function adds `CACHE_BUSTER` environment variable to Terraform container
- **AND** the function includes the cache buster in Terraform apply command

### Requirement: Plan function supports cache busting  
The `plan` function SHALL support cache busting through the `cache_buster` parameter. The function SHALL use the provided cache buster value to invalidate Dagger's cache at multiple levels.

#### Scenario: Plan with cache buster
- **WHEN** the user invokes `plan` with `--cache-buster=unique-value-456`
- **THEN** the function uses `unique-value-456` to bust cache on KCL source directory
- **AND** the function adds `CACHE_BUSTER` environment variable to Terraform container

### Requirement: Destroy function supports cache busting
The `destroy` function SHALL support cache busting through the `cache_buster` parameter. The function SHALL use the provided cache buster value to invalidate Dagger's cache at multiple levels.

#### Scenario: Destroy with cache buster
- **WHEN** the user invokes `destroy` with `--cache-buster=unique-value-789`
- **THEN** the function uses `unique-value-789` to bust cache on KCL source directory
- **AND** the function adds `CACHE_BUSTER` environment variable to Terraform container

### Requirement: Test integration function supports cache busting
The `test_integration` function SHALL support cache busting through the `cache_buster` parameter. The function SHALL use the provided cache buster value to invalidate Dagger's cache at multiple levels.

#### Scenario: Test integration with cache buster
- **WHEN** the user invokes `test_integration` with `--cache-buster=unique-value-abc`
- **THEN** the function uses `unique-value-abc` to bust cache on all operations
- **AND** the function adds `CACHE_BUSTER` environment variable to test containers
