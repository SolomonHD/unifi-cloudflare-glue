# Proposal: Add Remote Dagger Module Documentation

## Summary

Add comprehensive documentation to README.md explaining how external users can install and use the unifi-cloudflare-glue Dagger module remotely from their own repositories, covering installation, function calling patterns, and the critical difference between local development (`--source=.`) and remote usage (`--kcl-source=./your-config`).

## Problem Statement

The README.md currently focuses on local development usage patterns, assuming users have cloned the repository. For users discovering unifi-cloudflare-glue as a remote Dagger module, the documentation does not address:

- How to install the module using `dagger install`
- How to call module functions after installation
- How to use the module directly without installing (CI/CD pattern)
- The critical parameter difference: `--source=.` (reads module's KCL files) vs `--kcl-source=./your-config` (reads user's KCL files)
- Version pinning best practices
- CI/CD integration patterns

Without this documentation, remote users must reverse-engineer usage patterns from the codebase or may incorrectly assume local development examples work for remote consumption.

## Proposed Solution

Add a new "Using as a Dagger Module" section to README.md after the "Quickstart" section (line 39) and before the "Modules" section (line 95), following the same structure as the existing "Using as Terraform Modules" section (lines 461-528).

The section will:

1. **Explain remote module consumption** - Introduce the concept of using Dagger modules remotely
2. **Document installation** - Show `dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0`
3. **Clarify parameter distinction** - Emphasize that:
   - Local development: `--source=.` uses the module's own KCL files (for module developers)
   - Remote usage: `--kcl-source=./your-config` uses the caller's KCL configuration (for module users)
4. **Provide function examples** - Show usage for all major functions:
   - `deploy` - Full orchestration
   - `deploy-unifi` - UniFi only deployment
   - `deploy-cloudflare` - Cloudflare only deployment
   - `destroy` - Infrastructure teardown
   - `plan` - Plan generation
   - `test-integration` - Integration testing
5. **Document consumption patterns** - Show three ways to call the module:
   - Installed module: `dagger call -m unifi-cloudflare-glue function-name ...`
   - Direct remote: `dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0 unifi-cloudflare-glue function-name ...`
   - CI/CD pattern with version pinning
6. **Recommend version pinning** - Always use `@vX.Y.Z` in production
7. **Show CI/CD example** - GitHub Actions workflow snippet

### Key Messaging

- Remote consumers **must** provide their own KCL configuration via `--kcl-source=./path-to-their-config`
- `--source=.` is for local development within this repository only and will fail when called remotely
- Version pinning prevents unexpected changes in production
- The module naming follows Dagger conventions: repository name matches module name

## Scope

### In Scope
- New "Using as a Dagger Module" section in README.md
- Installation instructions with `dagger install` command
- Clear explanation of `--source=.` vs `--kcl-source=./your-config` distinction
- Usage examples for all major functions (deploy, deploy-unifi, deploy-cloudflare, destroy, plan, test-integration)
- Three consumption patterns: installed, direct remote, CI/CD
- Version pinning guidance
- GitHub Actions CI/CD example
- Section placement: after "Quickstart", before "Modules"

### Out of Scope
- Changes to Dagger function implementations
- Changes to function signatures or behavior
- Modifications to KCL schemas or Terraform modules
- Changes to existing documentation sections beyond adding the new section
- Changes to dagger.json or module configuration
- Additional examples beyond the CI/CD workflow snippet

## Requirements

### Functional Requirements

1. **FR-1**: New section "Using as a Dagger Module" added to README.md
2. **FR-2**: Section placed after "Quickstart" (line 39), before "Modules" (line 95)
3. **FR-3**: Installation command documented: `dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0`
4. **FR-4**: Parameter distinction clearly explained with examples
5. **FR-5**: Usage examples provided for `deploy` function
6. **FR-6**: Usage examples provided for `deploy-unifi` function
7. **FR-7**: Usage examples provided for `deploy-cloudflare` function
8. **FR-8**: Usage examples provided for `destroy` function
9. **FR-9**: Usage examples provided for `plan` function
10. **FR-10**: Usage examples provided for `test-integration` function
11. **FR-11**: Installed module pattern documented: `dagger call -m unifi-cloudflare-glue`
12. **FR-12**: Direct remote pattern documented: `dagger call -m github.com/...@version unifi-cloudflare-glue`
13. **FR-13**: Version pinning best practice stated explicitly
14. **FR-14**: CI/CD usage pattern example included
15. **FR-15**: Section structure mirrors "Using as Terraform Modules" for consistency

### Non-Functional Requirements

1. **NFR-1**: All command examples are syntactically correct and testable
2. **NFR-2**: Documentation tone and style match existing README sections
3. **NFR-3**: Section length proportional to "Using as Terraform Modules" section
4. **NFR-4**: Markdown formatting consistent with existing documentation
5. **NFR-5**: Code blocks use appropriate syntax highlighting (```bash)
6. **NFR-6**: Cross-references to other sections where appropriate

## Dependencies

- Current version 0.2.0 from VERSION file
- Module name "unifi-cloudflare-glue" from dagger.json
- Repository URL: github.com/SolomonHD/unifi-cloudflare-glue
- Existing Dagger functions: deploy, deploy-unifi, deploy-cloudflare, destroy, plan, test-integration
- Existing README.md structure and style conventions

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Documentation becomes outdated as functions evolve | Medium | Document examples link to function signatures which include docstrings |
| Users still confused about parameter differences | High | Use WARNING or IMPORTANT callouts for critical distinctions |
| Section placement disrupts flow | Low | Review before/after sections to ensure smooth narrative transition |
| Examples don't match actual module behavior | High | Test all examples before documenting (or note untested) |
| Version in examples (0.2.0) becomes outdated | Low | Use placeholder pattern like "vX.Y.Z" with note to check releases |

## Success Criteria

- [ ] New "Using as a Dagger Module" section exists in README.md
- [ ] Section placed after "Quickstart" and before "Modules"
- [ ] Installation instructions with `dagger install` command present
- [ ] Clear explanation of `--source=.` vs `--kcl-source=./your-config` included
- [ ] Examples provided for all six major functions
- [ ] Both installed module and direct remote patterns documented
- [ ] Version pinning best practice clearly stated
- [ ] CI/CD usage pattern example included
- [ ] Section structure parallels "Using as Terraform Modules"
- [ ] All command examples are syntactically valid

## Open Questions

None. Requirements are well-defined from the prompt file.
