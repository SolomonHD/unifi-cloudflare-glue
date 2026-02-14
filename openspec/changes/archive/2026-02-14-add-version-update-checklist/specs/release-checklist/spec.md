## ADDED Requirements

### Requirement: Complete Component List
The release checklist in CONTRIBUTING.md SHALL identify ALL files that contain version information including:
1. `VERSION` - Root version file (e.g., `0.6.0`)
2. `kcl.mod` - `[package].version` field
3. `pyproject.toml` - `[project].version` field
4. `terraform/modules/unifi-dns/versions.tf` - Version comment
5. `terraform/modules/cloudflare-tunnel/versions.tf` - Version comment
6. `dagger.json` - `engineVersion` (if applicable)
7. `examples/*/kcl.mod` - Git tag in dependencies (e.g., `tag = "v0.6.0"`)

#### Scenario: All version files are documented
- **WHEN** a contributor looks at the release checklist in CONTRIBUTING.md
- **THEN** they SHALL see a complete list of all files that need version updates

### Requirement: Version Format Conventions
The release checklist SHALL document the correct version format for each location:
- `VERSION` file: Plain version (e.g., `0.6.0`) - NO v prefix
- Git tags: With v prefix (e.g., `v0.6.0`)
- kcl.mod dependencies: With v prefix (e.g., `tag = "v0.6.0"`)

#### Scenario: Version format is clear
- **WHEN** a contributor updates versions during a release
- **THEN** they SHALL know whether to use the v prefix based on the checklist

### Requirement: Override Capability
The release checklist SHALL support documenting version override capability for specific components when they need different versions:
- Example: `--kcl-version=0.5.0 --terraform-version=0.6.0`
- Default behavior: All components use the same version

#### Scenario: Override syntax is documented
- **WHEN** a component needs a different version than others
- **THEN** the contributor SHALL find documented syntax for version overrides in CONTRIBUTING.md

### Requirement: Search Verification
The release checklist SHALL include steps to search for any remaining old version strings across the entire repository to ensure complete version update.

#### Scenario: Verification commands are provided
- **WHEN** a contributor completes the version updates
- **THEN** they SHALL have grep commands to verify no old version references remain

### Requirement: Examples Directory Updates
The release checklist SHALL include steps to update version references in all example kcl.mod files under the `examples/` directory.

#### Scenario: Example configs are updated
- **WHEN** a new version is released
- **THEN** the contributor SHALL know to update git tag references in `examples/*/kcl.mod` files
