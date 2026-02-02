# Proposal: Add Unified Versioning

## Problem

The unifi-cloudflare-glue project lacks a unified version management strategy. Currently:

- [`pyproject.toml`](../../pyproject.toml:7) has version `0.0.0`
- [`kcl/kcl.mod`](../../kcl/kcl.mod:4) has version `0.1.0`
- Terraform modules have no version metadata
- Dagger module has no version retrieval function
- No single source of truth for the project version

This creates version drift between components and makes it difficult to track which version of the project users are working with. The project contains three tightly integrated components (KCL schemas, Terraform modules, and Dagger module) that function as a cohesive system where changes in one component typically affect others. Without a unified versioning strategy, it's unclear which components are compatible with each other.

## Solution

Implement a centralized version management system using a single `VERSION` file at the repository root as the single source of truth. All components will reference this file for consistent version reporting.

### Components

1. **VERSION File**: Plain text file at repository root containing semantic version (no `v` prefix)
2. **Version References**: Update all component configurations to match the VERSION file
3. **Version Function**: Add Dagger function to query the module version
4. **Documentation**: Document the versioning strategy and release workflow

### Benefits

- Single source of truth for version management
- Consistent version across all components
- Clear compatibility guarantees (all components share same version)
- Simplified release process
- Easy version querying via Dagger CLI

## Scope

### In Scope

- Create `VERSION` file at repository root with version `0.1.0`
- Update [`pyproject.toml`](../../pyproject.toml:7) from `0.0.0` to `0.1.0`
- Keep [`kcl/kcl.mod`](../../kcl/kcl.mod:4) at `0.1.0` (already correct)
- Add version comments to Terraform module `versions.tf` files
- Add `version()` Dagger function to [`src/main/main.py`](../../src/main/main.py)
- Document versioning strategy in README.md
- Document release process in CONTRIBUTING.md (create if missing)
- Optional: Add `.gitattributes` to enforce LF line endings for VERSION file

### Out of Scope

- Automated version bumping tooling
- Independent versioning for sub-components
- Backfilling historical versions
- Changes to existing git tags
- Container tool version management (already handled via function parameters)

## Constraints

- Git tags use `v` prefix (e.g., `v0.1.0`) per Dagger conventions
- VERSION file contains version without `v` prefix (e.g., `0.1.0`)
- Semantic versioning: `MAJOR.MINOR.PATCH`
- All components share the same version number
- Manual version management (no automated tooling initially)
- Breaking change in any component triggers major version bump

## Impact

- **Low Risk**: Only adds documentation and metadata, no functional changes
- **Version Drift**: Resolves existing version inconsistency between pyproject.toml and kcl.mod
- **Release Process**: Establishes clear workflow for future releases
- **User Visibility**: Users can query version via `dagger call version --source=.`

## Dependencies

None - this is a standalone change that doesn't depend on other work.

## Related Specs

- [`dagger-module`](../../specs/dagger-module/spec.md): Will add version function requirement
- [`documentation`](../../specs/documentation/spec.md): Will add versioning documentation requirement
- [`project-structure`](../../specs/project-structure/spec.md): Will add VERSION file requirement
