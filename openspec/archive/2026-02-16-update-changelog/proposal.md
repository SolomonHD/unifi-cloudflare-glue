## Why

The removal of the `--no-cache` flag from all Dagger functions is a breaking change that affects user workflows. Without proper documentation in CHANGELOG.md, users upgrading to the new version will encounter unexpected errors when their existing commands fail. Clear changelog entries with migration guidance are essential for maintaining user trust and enabling smooth version transitions.

## What Changes

- **Add breaking change documentation to CHANGELOG.md:**
  - Document the removal of `no_cache` boolean parameter from all Dagger functions
  - Mark as **BREAKING** change with ⚠️ symbol for visibility
  - Provide before/after migration examples showing the `--cache-buster=$(date +%s)` replacement
  - Explain the technical rationale (Dagger's aggressive function-level caching behavior)
  - List all four affected functions: `deploy()`, `plan()`, `destroy()`, `test_integration()`
  - Add the new section at the top of the existing `[Unreleased]` section

## Capabilities

### New Capabilities
<!-- This is a documentation-only change that doesn't introduce new functional capabilities -->

### Modified Capabilities
<!-- This change updates documentation but doesn't modify spec-level requirements -->

## Impact

- **File:** `CHANGELOG.md` - Addition of ~25-30 lines to the `[Unreleased]` section
- **Users:** Anyone upgrading from v0.9.x to v0.10.0+ will see clear migration guidance
- **Documentation:** Follows existing CHANGELOG.md formatting conventions (Keep a Changelog format)
- **Breaking Change Notification:** Users currently using `--no-cache` will understand the required change
