## Why

After removing the `no_cache` parameter from the Python Dagger module code, all user-facing documentation still references the old `--no-cache` flag. This creates confusion for users who follow the documentation but receive errors since the parameter no longer exists. The documentation must be updated to consistently show the `--cache-buster=$(date +%s)` pattern which is the correct way to bypass Dagger's aggressive caching.

## What Changes

- Update `README.md` to replace all `--no-cache` examples with `--cache-buster=$(date +%s)`
- Update `docs/dagger-reference.md` parameter tables and examples to remove `--no-cache` references
- Update `docs/deployment-patterns.md` cache control section with new pattern and explanation
- Remove `--no-cache` from all command examples across user-facing documentation
- Add explanation about why explicit timestamps are required for cache busting

## Capabilities

### New Capabilities
- `documentation-cache-buster`: Update all user-facing documentation to use `--cache-buster=$(date +%s)` pattern instead of `--no-cache`

### Modified Capabilities
- None (this is a documentation-only change, no spec behavior changes)

## Impact

- **Files Affected**: `README.md`, `docs/dagger-reference.md`, `docs/deployment-patterns.md`
- **User Experience**: Users will see consistent, working examples that match the actual code
- **Breaking Change**: None (documentation correction)
- **Exclusions**: `README.old.md`, `openspec/archive/**`, `openspec/specs/**` (archived/historical files)
