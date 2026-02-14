## Context

The unifi-cloudflare-glue repository has multiple version files across different components that must stay synchronized:
- `VERSION` (root): Single source of truth (currently shows 0.6.0)
- `kcl.mod`: KCL module version (currently shows 0.1.0)
- `pyproject.toml`: Python package version (currently shows 0.1.0)
- `terraform/modules/*/versions.tf`: Terraform module version comments
- `dagger.json`: Dagger engine version
- `examples/*/kcl.mod`: Git tag references in example dependencies

The current CONTRIBUTING.md has a basic "Release Process" section (lines 84-149) but it lacks a comprehensive checklist format, leading to version mismatches during releases.

## Goals / Non-Goals

**Goals:**
- Add a comprehensive checkbox-based release checklist to CONTRIBUTING.md
- Identify all files that contain version information requiring updates
- Document version format conventions (v prefix for git tags, no v for VERSION file)
- Include verification steps to ensure no version references are missed
- Support version override capability for components that need different versions

**Non-Goals:**
- Creating automated version bump scripts (can be added separately)
- Modifying CI/CD workflows
- Changing existing version numbering scheme
- Updating any actual version numbers (documentation only)

## Decisions

**Decision 1: Add checklist to existing CONTRIBUTING.md vs. separate file**
- Chosen: Add to existing CONTRIBUTING.md under "Release Process" section
- Rationale: Keeps all contribution guidelines in one place, easier for contributors to find

**Decision 2: Checklist format**
- Chosen: Markdown checkbox format (`- [ ]` for unchecked, `- [x]` for checked)
- Rationale: Standard markdown that's widely understood, can be rendered in GitHub UI

**Decision 3: Version override documentation**
- Chosen: Document override syntax as future capability (not implemented yet)
- Rationale: Provides clear path for future automation without implementing scripts now

**Decision 4: Verification approach**
- Chosen: Use grep commands to search for old version strings
- Rationale: Simple, reliable, no external tools required

## Risks / Trade-offs

- **Risk**: Contributors may not notice the new checklist
  - **Mitigation**: Update the existing "Release Process" section introduction to point to the new checklist

- **Risk**: Examples directory kcl.mod files might have complex dependency configurations
  - **Mitigation**: Document the specific grep command to find all examples that need updating

- **Risk**: Version mismatches could still occur if contributors don't follow the checklist
  - **Mitigation**: Add the checklist as a required step in the PR template or CI check
