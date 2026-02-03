# OpenSpec Change Prompt

## Context

The `unifi-cloudflare-glue` project is a Dagger module that provides containerized, reproducible pipelines for managing hybrid DNS infrastructure. It can be consumed as a remote Dagger module from other repositories, but the README.md currently only documents local development patterns (using `--source=.` parameter).

Users attempting to install and use this module remotely will not find clear documentation on:
- How to install the module via `dagger install`
- How to call functions from an installed module
- How to use the module directly without installation
- The critical difference between `--source=.` (local) and `--kcl-source=./your-config` (remote)

## Goal

Add comprehensive documentation for remote Dagger module consumption patterns to README.md, enabling users to discover and use this module from their own repositories without cloning the source.

## Scope

**In scope:**
- Add new "Using as a Dagger Module" section to README.md
- Document three consumption methods: installation, installed usage, and direct remote usage
- Include examples for all major functions: deploy, deploy-unifi, deploy-cloudflare, destroy, plan, test-integration
- Clarify the KCL source parameter difference: local vs remote usage
- Show version pinning best practices
- Provide CI/CD usage patterns

**Out of scope:**
- Code changes to the Dagger module itself
- Changes to function signatures or behavior
- Modifications to existing documentation sections beyond adding the new section
- Changes to KCL schemas or Terraform modules

## Desired Behavior

### Section Placement
- Add new section after "Quickstart" (line 39) and before "Modules" (line 95)
- Follow the same structure as "Using as Terraform Modules" section (lines 461-528)

### Documentation Structure

The new section should include:

1. **Introduction paragraph** explaining remote module consumption
2. **Installation instructions** using `dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0`
3. **Critical parameter distinction**:
   - Local development: `--source=.` uses the module's own KCL files
   - Remote usage: `--kcl-source=./your-config` uses the caller's KCL configuration directory
4. **Function examples** for all major operations:
   - `deploy` - Full orchestration
   - `deploy-unifi` - UniFi only
   - `deploy-cloudflare` - Cloudflare only
   - `destroy` - Teardown
   - `plan` - Plan generation
   - `test-integration` - Testing
5. **Three consumption patterns**:
   - Installed module: `dagger call -m unifi-cloudflare-glue function-name ...`
   - Direct remote: `dagger call -m github.com/...@v0.2.0 unifi-cloudflare-glue function-name ...`
   - CI/CD pattern: Direct remote with version pinning
6. **Version pinning guidance**: Always use `@vX.Y.Z` in production
7. **CI/CD example**: GitHub Actions or similar pattern

### Key Messaging

- Emphasize that remote consumers **must** provide their own KCL configuration via `--kcl-source=./path-to-their-config`
- Highlight that `--source=.` is for local development within this repository only
- Show version pinning as the recommended practice
- Mirror the clarity and structure of the existing "Using as Terraform Modules" section

## Constraints & Assumptions

- Assumption: The module name in dagger.json is "unifi-cloudflare-glue" (verify this)
- Assumption: Current version is v0.2.0 based on VERSION file
- Constraint: This is documentation-only, no code modifications
- Constraint: Must fit cohesively with existing documentation style and tone
- Assumption: Direct Dagger remote syntax follows pattern: `dagger call -m github.com/OWNER/REPO@VERSION MODULE-NAME function-name`

## Acceptance Criteria

- [ ] New "Using as a Dagger Module" section added after "Quickstart" and before "Modules"
- [ ] Section includes installation instructions with `dagger install` command
- [ ] Clear explanation of `--source=.` vs `--kcl-source=./your-config` distinction
- [ ] Examples provided for all major functions: deploy, deploy-unifi, deploy-cloudflare, destroy, plan, test-integration
- [ ] Both installed module and direct remote usage patterns documented
- [ ] Version pinning best practice clearly stated
- [ ] CI/CD usage pattern example included
- [ ] Section structure mirrors "Using as Terraform Modules" for consistency
- [ ] All command examples are accurate and testable
