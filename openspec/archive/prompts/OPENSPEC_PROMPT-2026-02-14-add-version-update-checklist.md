# OpenSpec Prompt: Add Unified Version Update Checklist

## Overview

This prompt adds a comprehensive release checklist to CONTRIBUTING.md that ensures all version references across the multi-component unifi-cloudflare-glue repository are updated consistently when releasing a new version.

## Problem Statement

The unifi-cloudflare-glue repository contains multiple components that each maintain their own version:
- **VERSION file** (root) - Single source of truth
- **KCL module** - `kcl.mod` version field
- **Python/Dagger module** - `pyproject.toml` version field  
- **Terraform modules** - `versions.tf` version comments
- **Dagger module** - `dagger.json` engineVersion (less critical)
- **Example configs** - Git tag references in kcl.mod dependencies

Currently, when releasing a new version (e.g., v0.6.0), these versions get out of sync because there's no systematic process to update them all.

## Scope

### In Scope
- Update CONTRIBUTING.md with a comprehensive release checklist
- Ensure all version-affecting files are identified
- Add version override capability for cases where components need different versions
- Document the version format conventions (v prefix for git tags, no v for VERSION file)

### Out of Scope
- Creating automated scripts (can be added separately)
- Modifying CI/CD workflows
- Changing existing version numbering scheme

## Key Requirements

### KR-1: Complete Component List
The checklist must identify ALL files that contain version information:
1. `VERSION` - Root version file (e.g., `0.6.0`)
2. `kcl.mod` - `[package].version` field
3. `pyproject.toml` - `[project].version` field
4. `terraform/modules/unifi-dns/versions.tf` - Version comment
5. `terraform/modules/cloudflare-tunnel/versions.tf` - Version comment
6. `dagger.json` - `engineVersion` (if applicable)
7. `examples/*/kcl.mod` - Git tag in dependencies (e.g., `tag = "v0.6.0"`)

### KR-2: Override Capability
The checklist must support overriding version for specific components:
- Example: `--kcl-version=0.5.0 --terraform-version=0.6.0`
- Default behavior: All components use the same version

### KR-3: Version Format Conventions
Document the correct format:
- `VERSION` file: Plain version (e.g., `0.6.0`) - NO v prefix
- Git tags: With v prefix (e.g., `v0.6.0`)
- kcl.mod dependencies: With v prefix (e.g., `tag = "v0.6.0"`)

### KR-4: Search Verification
Include step to search for any remaining old version strings across the entire repository

## Example Output

The CONTRIBUTING.md should include a section like:

```markdown
## Release Checklist

When releasing version X.Y.Z:

### Step 1: Update Root Version
- [ ] Update `VERSION` file to `X.Y.Z`

### Step 2: Update Module Versions
- [ ] Update `kcl.mod` version to `X.Y.Z`
- [ ] Update `pyproject.toml` version to `X.Y.Z`
- [ ] Update `terraform/modules/unifi-dns/versions.tf` version comment
- [ ] Update `terraform/modules/cloudflare-tunnel/versions.tf` version comment

### Step 3: Update Example Dependencies
- [ ] Update all `examples/*/kcl.mod` git tags to `vX.Y.Z`

### Step 4: Verify
- [ ] Run `grep -r "X.Y.Z-1" .` to find any missed references
- [ ] Run `grep -r "vX.Y.Z-1" .` for git tag references

### Override Syntax (if needed)
# To use different versions for specific components:
./scripts/bump-version.sh X.Y.Z --kcl-version=0.5.0 --terraform-version=0.6.0
```

## Success Criteria

- [ ] CONTRIBUTING.md contains complete release checklist
- [ ] All version-containing files are identified
- [ ] Override capability is documented
- [ ] Version format conventions are clearly stated
- [ ] Verification steps are included
- [ ] Examples directory version updates are covered

## Dependencies

- None - this is a standalone documentation improvement

## Constraints

- Must not break existing functionality
- Must not modify any version numbers (documentation only)
- Should be consistent with existing CONTRIBUTING.md tone and style
