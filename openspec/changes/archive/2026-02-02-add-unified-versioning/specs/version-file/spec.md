# Spec Delta: VERSION File Management

## ADDED Requirements

### Requirement: VERSION File Structure

The repository SHALL contain a VERSION file at the root that serves as the single source of truth for the project version.

#### Scenario: VERSION file exists at repository root
Given: The repository root directory exists
When: The versioning system is implemented
Then: A plain text file named `VERSION` exists at the repository root
And: The file contains a single line with a semantic version number
And: The version uses the format `MAJOR.MINOR.PATCH` (e.g., `0.1.0`)
And: The version does NOT include a `v` prefix
And: The file ends with a single newline character

#### Scenario: VERSION file is readable by all tools
Given: The VERSION file exists at the repository root
When: Any tool or script reads the file
Then: The content is plain ASCII text
And: The file can be read without special parsing
And: The version can be trimmed of whitespace and used directly

### Requirement: Version Synchronization

All component version references SHALL match the version specified in the VERSION file.

#### Scenario: pyproject.toml version matches VERSION
Given: The VERSION file contains `0.1.0`
When: The pyproject.toml file is inspected
Then: The `[project].version` field is set to `"0.1.0"`

#### Scenario: kcl.mod version matches VERSION
Given: The VERSION file contains `0.1.0`
When: The kcl/kcl.mod file is inspected
Then: The `[package].version` field is set to `"0.1.0"`

#### Scenario: Git tags use v prefix
Given: The VERSION file contains `0.1.0`
When: A git tag is created for this version
Then: The tag is named `v0.1.0` (with `v` prefix)
And: The tag follows Dagger module conventions

### Requirement: Version File Best Practices

The VERSION file SHALL follow best practices for version control systems.

#### Scenario: Consistent line endings enforced
Given: The repository uses `.gitattributes` for file normalization
When: The `.gitattributes` file is configured
Then: The VERSION file has an entry `VERSION text eol=lf`
And: Git ensures LF line endings regardless of platform

#### Scenario: VERSION file is tracked in git
Given: The VERSION file exists
When: Git status is checked
Then: The VERSION file is tracked (not in .gitignore)
And: Changes to VERSION file appear in git diff
