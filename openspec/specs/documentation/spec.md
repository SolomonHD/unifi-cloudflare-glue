# documentation Specification

## Purpose
TBD - created by archiving change 010-example-homelab-media-stack. Update Purpose after archive.
## Requirements
### Requirement: Overview Section

The README SHALL include an overview section that introduces the example and its purpose.

#### Scenario: Understanding the example purpose
Given a new user discovering the example
When they read the README
Then they must find:
- Clear description of what the example configures
- List of included services by category
- Architecture overview (single server, dual NIC)
- Prerequisites for deployment

### Requirement: Deployment Workflow

The README SHALL include step-by-step deployment instructions that guide users through the complete workflow.

#### Scenario: Step-by-step deployment instructions
Given a user ready to deploy the example
When they follow the documentation
Then they must have clear steps:
1. Copy/cloning the example directory
2. Customizing KCL configuration (replacing placeholders)
3. Running KCL to generate JSON files
4. Configuring Terraform credentials
5. Applying UniFi module first (for internal DNS)
6. Applying Cloudflare module (for external access)
7. Configuring cloudflared with tunnel tokens
8. Verifying service accessibility

### Requirement: Customization Guide

The README SHALL include a customization guide that explains how to adapt the example for different needs.

#### Scenario: Adapting the example for different needs
Given a user wants to modify the example
When they read the customization section
Then they must understand how to:
- Add a new service (choosing distribution type)
- Remove existing services
- Change domain names
- Add additional devices
- Modify port numbers
- Change service hostnames

### Requirement: Placeholder Reference

The README SHALL include a reference table documenting all placeholder values that need customization.

#### Scenario: Identifying all customization points
Given the example uses placeholder values
When users need to customize
Then they must find a table documenting:
| Placeholder | Description | Example Value |
|-------------|-------------|---------------|
| `<your-domain>` | Cloudflare DNS zone | example.com |
| `<your-account-id>` | Cloudflare account ID | 1234567890abcdef |
| `<mac-management>` | Management NIC MAC | aa:bb:cc:dd:ee:f1 |
| `<mac-media>` | Media NIC MAC | aa:bb:cc:dd:ee:f2 |

### Requirement: Troubleshooting Section

The README SHALL include a troubleshooting section covering common deployment issues.

#### Scenario: Common deployment issues
Given users may encounter problems
When issues occur
Then documentation must cover:
- KCL validation errors (MAC format, missing fields)
- Terraform provider authentication issues
- UniFi controller connection problems
- Cloudflare API token permissions
- DNS resolution not working
- Tunnel connectivity issues
- local_service_url causing DNS loops

### Requirement: Architecture Explanation

The README SHALL explain the design decisions and architecture of the example.

#### Scenario: Understanding design decisions
Given users want to understand the architecture
When they read the documentation
Then they must find explanations for:
- Why UniFi-only for *arr stack (security)
- Why dual-exposure for Jellyfin (local performance + remote access)
- How MAC addresses link UniFi and Cloudflare configs
- Why internal domains prevent DNS loops
- How the generators filter services by distribution

---

## ADDED Requirements (from change: add-unified-versioning)

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

---

## ADDED Requirements (from change: create-docs-structure)

### Requirement: README Length Target

The README.md file SHALL be approximately 300 lines or less, serving as an entry point and navigation hub rather than comprehensive documentation.

#### Scenario: Quick README scan
- **WHEN** a user first discovers the project
- **THEN** they can read the entire README in under 5 minutes to understand the project's purpose and navigate to detailed docs

### Requirement: Project Overview Section

The README SHALL include a concise project overview explaining the purpose and high-level architecture in 2-3 paragraphs.

#### Scenario: Understanding project purpose at a glance
- **WHEN** a user reads the README overview
- **THEN** they MUST understand:
  - What problem the project solves
  - The "define once, deploy everywhere" approach
  - How KCL, Terraform, and Dagger integrate
  - The relationship between UniFi local DNS and Cloudflare tunnels

### Requirement: Quick Start Section

The README SHALL include a minimal quick start section with no more than 3-5 commands for initial deployment.

#### Scenario: Getting started quickly
- **WHEN** a user wants to try the system immediately
- **THEN** they MUST find:
  - Minimal command sequence for installation
  - Link to detailed getting-started guide in docs/
  - Prerequisites clearly stated or linked

### Requirement: Documentation Navigation

The README SHALL include a Documentation section with clear links to all specialized documentation files.

#### Scenario: Finding detailed documentation
- **WHEN** a user needs detailed information on a topic
- **THEN** they MUST find intuitive navigation links organized by:
  - User journey (Getting Started → Advanced Topics)
  - Topic category (Configuration, Security, Troubleshooting)
  - Each link with brief description of content

#### Scenario: Documentation link structure
- **WHEN** viewing the Documentation section
- **THEN** it MUST include links in this format:
  - `[Link Text](docs/filename.md) - Brief description of content`

### Requirement: Architecture Summary

The README SHALL include a high-level architecture section explaining the system's components WITHOUT duplicating detailed content from docs/.

#### Scenario: Understanding system architecture
- **WHEN** a user reads the architecture section
- **THEN** they MUST find:
  - High-level component diagram or description
  - How components interact
  - Link to detailed architecture documentation in docs/

### Requirement: Key Features Highlight

The README SHALL highlight key features that differentiate this project.

#### Scenario: Understanding project value proposition
- **WHEN** a user evaluates whether to use this project
- **THEN** they MUST see key features listed:
  - Unified Configuration
  - DNS Loop Prevention
  - MAC Address Management
  - One Tunnel Per Device
  - Cross-provider validation

### Requirement: Project Structure Overview

The README SHALL include a high-level project structure showing main directories.

#### Scenario: Understanding repository organization
- **WHEN** a user explores the repository
- **THEN** they MUST find a directory tree showing:
  - terraform/modules/ - Terraform infrastructure modules
  - kcl/ - KCL schemas and generators
  - src/ - Dagger module source
  - examples/ - Example configurations
  - docs/ - Detailed documentation

### Requirement: Modular Documentation Structure Support

The documentation system SHALL support a modular structure with specialized topic files organized under a docs/ directory.

#### Scenario: Documentation organized by topic
- **WHEN** project documentation covers multiple aspects
- **THEN** it MUST be organized into separate files by topic area rather than a single monolithic document

#### Scenario: Cross-referencing between documentation files
- **WHEN** one documentation topic relates to another
- **THEN** files MUST include working relative links to related documentation using Markdown link syntax

### Requirement: Documentation Entry Point

The project SHALL maintain a condensed README.md as the primary entry point with navigation to detailed documentation.

#### Scenario: README as navigation hub
- **WHEN** users discover the project
- **THEN** README.md MUST provide:
  - Brief project overview
  - Quick start instructions
  - Clear navigation links to detailed topic documentation
  - Project structure overview

#### Scenario: Documentation index
- **WHEN** users navigate to the docs/ directory
- **THEN** they MUST find a README.md index file listing available documentation files with descriptions

### Requirement: Relative Path Links

All documentation internal links SHALL use relative paths that resolve correctly regardless of viewing context (GitHub web, local filesystem, IDE).

#### Scenario: Links from README to docs/
- **WHEN** README.md links to documentation files
- **THEN** links MUST use format: `[Text](docs/filename.md)`

#### Scenario: Links between docs/ files
- **WHEN** one docs/ file references another
- **THEN** links MUST use format: `[Text](./filename.md)` or `[Text](filename.md)`

#### Scenario: Links from docs/ to README
- **WHEN** a docs/ file references the main README
- **THEN** links MUST use format: `[Text](../README.md)`

### Requirement: Section Anchor Links

Documentation files SHALL support anchor links to specific sections for precise cross-referencing.

#### Scenario: Linking to specific sections
- **WHEN** referencing a specific section of another document
- **THEN** links MAY use format: `[Text](filename.md#section-anchor)`

#### Scenario: GitHub-compatible anchors
- **WHEN** creating section anchors
- **THEN** they MUST follow GitHub anchor rules:
  - Lowercase
  - Spaces become hyphens
  - Special characters removed

### Requirement: Link Validation

All internal documentation links SHALL resolve to existing files after restructuring.

#### Scenario: No broken links after migration
- **WHEN** content is migrated from monolithic README
- **THEN** all internal links MUST be updated to point to correct new locations

#### Scenario: Link checking
- **WHEN** documentation structure changes
- **THEN** a mechanism MUST exist to verify all links resolve (manual review or automated check)

### Requirement: External Link Preservation

External links (to APIs, third-party docs, GitHub resources) SHALL be preserved unchanged during restructuring.

#### Scenario: External links remain functional
- **WHEN** migrating content with external links
- **THEN** URLs to external resources MUST remain unchanged and functional

### Requirement: Example Code Links

Links to example configurations and code SHALL point to actual files in the repository.

#### Scenario: Example file references
- **WHEN** documentation references an example configuration
- **THEN** it MUST link directly to the file: `[Example](../examples/homelab-media-stack/main.k)`

#### Scenario: Example directory references
- **WHEN** pointing users to explore examples
- **THEN** link to the directory: `[Examples Directory](../examples/)`

### Requirement: Documentation Directory Structure

The project SHALL maintain a `docs/` directory containing specialized topic-based documentation files organized by user journey and technical depth.

#### Scenario: Finding topic-specific documentation
- **WHEN** a user needs information about a specific aspect of the system
- **THEN** they can navigate to the appropriate docs/ file without searching through a monolithic document

#### Scenario: Documentation organization
- **WHEN** examining the project structure
- **THEN** the docs/ directory MUST contain:
  - `getting-started.md` - Installation and quickstart guide
  - `dagger-reference.md` - Complete Dagger module function reference
  - `terraform-modules.md` - Standalone Terraform module usage patterns
  - `state-management.md` - State backend options and configuration
  - `security.md` - Security best practices and credential handling
  - `backend-configuration.md` - Backend configuration guides
  - `troubleshooting.md` - Common issues and solutions
  - `README.md` - Documentation index with navigation

### Requirement: Content Preservation

The documentation restructuring SHALL preserve all existing content from the original monolithic README.

#### Scenario: No content loss during migration
- **WHEN** comparing original README.md to the modular docs/
- **THEN** all sections, examples, warnings, and technical details MUST be preserved in appropriate topic files

#### Scenario: Original README backup
- **WHEN** the restructuring is performed
- **THEN** the original README.md MUST be backed up as README.old.md before modification

### Requirement: Cross-Reference Links

All documentation files SHALL use working relative links to reference related documentation.

#### Scenario: Following documentation cross-references
- **WHEN** a documentation file references another topic
- **THEN** it MUST include a working relative link to the relevant docs/ file

#### Scenario: Link integrity validation
- **WHEN** documentation is restructured
- **THEN** all internal links MUST resolve correctly without 404 errors

### Requirement: No Detailed Content Duplication

The README SHALL NOT duplicate detailed content that belongs in specialized docs/ files.

#### Scenario: Avoiding content duplication
- **WHEN** examining the README
- **THEN** it MUST NOT contain:
  - Complete function reference (belongs in dagger-reference.md)
  - Detailed security practices (belongs in security.md)
  - Troubleshooting guides (belongs in troubleshooting.md)
  - Complete configuration examples (belongs in getting-started.md or examples/)

#### Scenario: README focus
- **WHEN** content could go in either README or a specialized doc
- **THEN** prefer the specialized doc and link to it from README

### Requirement: Link Text Clarity

Link text SHALL clearly describe the destination content without requiring users to click to understand relevance.

#### Scenario: Descriptive link text
- **WHEN** creating a documentation link
- **THEN** use descriptive text: `[State Management Guide](docs/state-management.md)`
- **NOT** generic text: `[Click here](docs/state-management.md)`

### Requirement: Consistent Link Style

All documentation links SHALL follow consistent formatting conventions.

#### Scenario: Markdown link syntax
- **WHEN** creating any internal documentation link
- **THEN** use Markdown link syntax: `[Text](path)` NOT HTML `<a href>` tags

#### Scenario: Link with description
- **WHEN** listing documentation links
- **THEN** use format: `[Link Text](path) - Brief description of content`

