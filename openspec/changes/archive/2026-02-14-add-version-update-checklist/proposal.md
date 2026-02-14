## Why

The unifi-cloudflare-glue repository contains multiple components (KCL module, Python/Dagger module, Terraform modules) that each maintain their own version. Currently, these versions get out of sync during releases because there's no systematic checklist to update them all. The current CONTRIBUTING.md has a basic "Release Process" section but lacks a comprehensive checklist format, leading to version mismatches (e.g., VERSION file shows 0.6.0 while kcl.mod and pyproject.toml show 0.1.0).

## What Changes

- Add a comprehensive **Release Checklist** section to CONTRIBUTING.md with checkbox-based steps
- Document all version-containing files that need updating during release:
  - `VERSION` file (root)
  - `kcl.mod` version field
  - `pyproject.toml` version field
  - `terraform/modules/*/versions.tf` version comments
  - `dagger.json` engineVersion
  - `examples/*/kcl.mod` git tag dependencies
- Add version override capability documentation for cases where components need different versions
- Document version format conventions (v prefix for git tags, no v for VERSION file)
- Include search verification steps to find any missed version references

## Capabilities

### New Capabilities

list**: A comprehensive- **release-check release checklist in CONTRIBUTING.md that identifies all version-containing files, supports version overrides, documents format conventions, and includes verification steps to ensure version consistency across all components.

### Modified Capabilities

- (none) - This is a documentation-only change that doesn't affect existing spec requirements

## Impact

- **Files Modified**: `CONTRIBUTING.md` only (documentation update)
- **No code changes**: This is a documentation improvement only
- **No breaking changes**: Existing release process remains functional
- **No new dependencies**: Pure documentation task
