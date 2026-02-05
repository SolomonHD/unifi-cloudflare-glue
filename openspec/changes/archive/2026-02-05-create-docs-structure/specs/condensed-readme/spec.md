# condensed-readme Specification

## ADDED Requirements

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

### Requirement: Contributing and License Sections

The README SHALL include concise Contributing and License sections with appropriate links.

#### Scenario: Contributing information
- **WHEN** a user wants to contribute
- **THEN** they find a link to CONTRIBUTING.md or contribution guidelines

#### Scenario: License information
- **WHEN** a user checks project licensing
- **THEN** they find the license type (MIT) clearly stated

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
