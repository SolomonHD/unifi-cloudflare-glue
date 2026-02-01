# Change: Add --no-cache Flag to test_integration

## Why

The `test_integration` function currently uses a `cache_buster` string parameter that requires users to manually provide a unique value (e.g., `--cache-buster=$(date +%s)`) to force Dagger cache invalidation. This is awkward UX and not user-friendly. Users want a simple boolean flag that automatically handles cache invalidation without needing to generate timestamps manually.

## What Changes

- Add `no_cache: bool` parameter to `test_integration` function with default `False`
- When `no_cache=True`, automatically generate epoch timestamp using `int(time.time())` and set as `cache_buster`
- Keep existing `cache_buster` parameter for advanced use cases requiring custom cache keys
- Add validation to prevent using both `--no-cache` and `--cache-buster` simultaneously
- Update function docstring with new parameter and usage examples
- Update CHANGELOG.md with the new feature under [Unreleased] section

## Impact

- **Affected specs**: `test-integration` (enhancement to existing capability)
- **Affected code**: `src/main/main.py` - `test_integration` function signature and logic
- **Backward compatibility**: Maintained - existing `cache_buster` usage continues to work
- **CLI UX**: Improved - users can now use `--no-cache` instead of `--cache-buster=$(date +%s)`

## Desired Behavior

| Command | Result |
|---------|--------|
| `dagger call test-integration --no-cache` | Automatically uses epoch time as cache buster |
| `dagger call test-integration --cache-buster=1234567890` | Uses provided value (existing behavior) |
| `dagger call test-integration --no-cache --cache-buster=1234567890` | Error: "Cannot use both --no-cache and --cache-buster" |
| Neither flag provided | Normal caching behavior (existing) |
