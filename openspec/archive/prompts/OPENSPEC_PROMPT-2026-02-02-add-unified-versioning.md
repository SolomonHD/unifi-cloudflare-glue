# OpenSpec Change Prompt

## Context

The `unifi-cloudflare-glue` repository currently lacks a unified versioning strategy. The project contains three tightly integrated components (KCL schemas, Terraform modules, and Dagger module) that function as a cohesive system, where changes in one component typically affect others. The `pyproject.toml` currently uses version `0.0.0`, and there is no centralized version tracking mechanism. The project needs a single source of truth for version management that all components can reference.

## Goal

Implement a unified versioning structure using a single `VERSION` file at the repository root that all components (KCL, Terraform, and Dagger) reference for consistent version management.

## Scope

**In scope:**
- Create a `VERSION` file at repository root with initial version (e.g., `0.1.0`)
- Update `pyproject.toml` to reference the VERSION file or use its value
- Update `kcl/kcl.mod` to include version field
- Add version metadata to Terraform modules (`terraform/modules/unifi-dns/` and `terraform/modules/cloudflare-tunnel/`)
- Add a Dagger function to read and return the module version from VERSION file
- Document the versioning strategy in `README.md`
- Document the release workflow in `CONTRIBUTING.md` (create if needed)
- Add version references to examples where appropriate

**Out of scope:**
- Automated version bumping tooling (manual process is acceptable)
- Backfilling multiple historical versions
- Independent versioning for sub-components
- Container tool version management (already handled via function parameters)
- Changes to existing git tags

## Desired Behavior

### 1. VERSION File

Create `VERSION` at repository root:
```
0.1.0
```

- Plain text file with single line containing semantic version (no `v` prefix)
- This becomes the single source of truth for the module version
- Used by all components for version reference

### 2. Update pyproject.toml

Change version from `0.0.0` to read from VERSION or match its value:
```toml
[project]
name = "main"
version = "0.1.0"  # Matches VERSION file
```

### 3. Update KCL Module

Add version to `kcl/kcl.mod`:
```
[package]
name = "unifi-cloudflare-glue"
version = "0.1.0"
```

### 4. Terraform Module Metadata

Add version comments or metadata to each Terraform module. In `terraform/modules/unifi-dns/versions.tf` and `terraform/modules/cloudflare-tunnel/versions.tf`:
```hcl
# Module Version: 0.1.0
# Part of: unifi-cloudflare-glue
# Source: github.com/yourorg/unifi-cloudflare-glue?ref=v0.1.0

terraform {
  required_version = ">= 1.5.0"
  # existing content
}
```

### 5. Dagger Version Function

Add a new Dagger function in `src/main/main.py`:
```python
@function
async def version(self, source: dagger.Directory) -> str:
    """Get the module version from VERSION file"""
    return await source.file("VERSION").contents()
```

Available as: `dagger call version --source=.`

### 6. Documentation Updates

Update `README.md` to include:
- Version reference section showing current version
- How users should reference specific versions (git tags)
- Link to release process documentation

Create or update `CONTRIBUTING.md` with release workflow:
```markdown
## Release Process

1. Update `CHANGELOG.md`: Move `[Unreleased]` content to new version section
2. Update `VERSION` file: `echo "X.Y.Z" > VERSION`
3. Update `pyproject.toml` version to match
4. Update `kcl/kcl.mod` version to match
5. Update Terraform module version comments
6. Commit changes: `git commit -m "chore: release vX.Y.Z"`
7. Create git tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
8. Push: `git push origin main --tags`
```

### 7. .gitattributes (Optional)

Add `.gitattributes` to mark VERSION as text:
```
VERSION text eol=lf
```

## Constraints & Assumptions

- Git tags will use `v` prefix (e.g., `v0.1.0`) per Dagger conventions
- VERSION file contains plain version without `v` prefix
- Semantic versioning is used: `MAJOR.MINOR.PATCH`
- Breaking change in any component (KCL, Terraform, or Dagger) triggers a major version bump
- All components share the same version number (no independent versioning)
- Manual version management is acceptable (no automated tooling required initially)
- Existing CHANGELOG.md structure is preserved

## Acceptance Criteria

- [ ] `VERSION` file created at repository root with `0.1.0`
- [ ] `pyproject.toml` version updated from `0.0.0` to `0.1.0`
- [ ] `kcl/kcl.mod` includes version field set to `0.1.0`
- [ ] Both Terraform modules have version comments in their `versions.tf` files
- [ ] New `version()` Dagger function added to `src/main/main.py`
- [ ] `dagger call version --source=.` returns `0.1.0`
- [ ] `README.md` documents versioning strategy and how to reference specific versions
- [ ] Release process documented in `CONTRIBUTING.md` or similar file
- [ ] All version references are consistent (all show `0.1.0`)
- [ ] No breaking changes to existing functionality

## Reference

- Current version in `pyproject.toml`: `0.0.0` (line 7)
- Latest CHANGELOG entry: `[Unreleased]` in `CHANGELOG.md`
- Dagger module name: `unifi-cloudflare-glue` in `dagger.json`
- Git follows semantic versioning with `v` prefix for tags (Dagger convention)
- Semantic Versioning specification: https://semver.org/
