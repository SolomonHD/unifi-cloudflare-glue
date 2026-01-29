# OpenSpec Change Prompt: Upgrade Dagger Engine Version

## Context

The project currently uses Dagger engine version `v0.19.7` in `dagger.json`. The latest stable version includes bug fixes, performance improvements, and new features that may be needed for the Cloudflare provider v5 migration.

## Goal

Update the Dagger engine version to the latest stable release.

## Scope

**In scope:**
- Update `engineVersion` in `dagger.json` from `v0.19.7` to latest stable
- Verify SDK compatibility after upgrade

**Out of scope:**
- Changes to SDK source configuration
- Changes to Python code
- Changes to Terraform modules

## Desired Behavior

### Dagger Engine Version Update

- **File:** `dagger.json`
- **Current:** `"engineVersion": "v0.19.7"`
- **Target:** `"engineVersion": "v0.19.8"` (or latest stable)

The engine version should be updated to a stable release that maintains compatibility with the Python SDK.

## Constraints & Assumptions

- The Python SDK (`dagger-io`) must remain compatible with the new engine version
- No breaking changes should be introduced to existing Dagger function signatures
- The change should be minimal and focused only on the version bump

## Acceptance Criteria

- [ ] `dagger.json` engineVersion updated to latest stable version
- [ ] `dagger functions` command still works after version change
- [ ] No breaking changes to existing module functionality
- [ ] CHANGELOG.md updated to reflect the change

## Reference

- Target file: `dagger.json` (line 3)
- Dagger releases: https://github.com/dagger/dagger/releases

## Dependencies

None - this is an independent change that can be applied first.
