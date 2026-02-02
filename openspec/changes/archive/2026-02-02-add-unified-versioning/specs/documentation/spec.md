# Spec Delta: Versioning Documentation

## ADDED Requirements

### Requirement: README Versioning Section

The README.md SHALL document the project's versioning strategy and how to reference specific versions.

#### Scenario: Versioning strategy explained
Given: Users read the README.md file
When: They look for version information
Then: A dedicated section explains:
  - The project uses semantic versioning (MAJOR.MINOR.PATCH)
  - All components (KCL, Terraform, Dagger) share the same version
  - Version is stored in the VERSION file at repository root
  - Git tags use `v` prefix (e.g., `v0.1.0`)

#### Scenario: Current version is visible
Given: The README.md is updated for a release
When: Users view the top of the README
Then: The current version is displayed prominently
And: The version matches the VERSION file content

#### Scenario: Version querying instructions provided
Given: Users want to check the module version
When: They read the README
Then: An example shows how to query version via Dagger:
  - Command: `dagger call version --source=.`
  - Expected output: The version number

#### Scenario: Version referencing explained
Given: Users want to pin to a specific version
When: They read the documentation
Then: Examples show how to reference versions:
  - Git tag format: `v0.1.0`
  - Dagger install: `dagger install github.com/user/repo@v0.1.0`
  - Dagger remote call: `dagger call -m github.com/user/repo@v0.1.0 ...`

### Requirement: Release Process Documentation

The project SHALL document the release workflow in CONTRIBUTING.md.

#### Scenario: CONTRIBUTING.md exists with release section
Given: The repository wants to document the release process
When: CONTRIBUTING.md is created or updated
Then: A "Release Process" section exists
And: The section provides step-by-step instructions

#### Scenario: Release steps are documented
Given: The CONTRIBUTING.md release section
When: A maintainer prepares a release
Then: The documented steps include:
  1. Update CHANGELOG.md (move Unreleased to version section)
  2. Update VERSION file with new version
  3. Update pyproject.toml version to match
  4. Update kcl/kcl.mod version to match
  5. Update Terraform module version comments
  6. Commit: `git commit -m "chore: release vX.Y.Z"`
  7. Create tag: `git tag -a vX.Y.Z -m "Release X.Y.Z"`
  8. Push: `git push origin main --tags`

#### Scenario: Version bumping guidance provided
Given: The release process documentation
When: Maintainers need to decide version number
Then: Guidance explains semantic versioning:
  - MAJOR: Breaking changes in any component
  - MINOR: New features, backward compatible
  - PATCH: Bug fixes, backward compatible

### Requirement: Changelog Integration

The CHANGELOG.md SHALL follow conventions compatible with the versioning system.

#### Scenario: Unreleased section exists
Given: Development is ongoing between releases
When: Changes are made
Then: The CHANGELOG.md has an `[Unreleased]` section
And: New changes are documented under Unreleased

#### Scenario: Version sections follow format
Given: A release is made with version 0.1.0
When: The CHANGELOG is updated
Then: A section exists: `## [0.1.0] - YYYY-MM-DD`
And: The Unreleased content is moved to this section
And: An empty Unreleased section is created for future changes

#### Scenario: Changelog references match VERSION
Given: The VERSION file contains a specific version
When: The CHANGELOG is inspected
Then: The latest version section matches the VERSION file
And: The version format is consistent

### Requirement: Example Documentation

Example projects SHALL document which version they are compatible with.

#### Scenario: Example includes version reference
Given: An example project exists under examples/
When: The example's README is inspected
Then: It documents which project version it was tested with
And: Provides guidance on compatibility

#### Scenario: Examples reference specific versions
Given: An example uses the Dagger module
When: The example shows Dagger commands
Then: It demonstrates version-pinning:
  - `dagger install github.com/user/repo@v0.1.0`
  - Or uses the version query function
