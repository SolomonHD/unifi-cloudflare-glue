## ADDED Requirements

### Requirement: Architecture Documentation File

The project SHALL maintain a `docs/architecture.md` file containing comprehensive visual diagrams of the system architecture, data flow, deployment workflow, state management, and DNS resolution.

#### Scenario: Architecture documentation exists
- **WHEN** a user navigates to the docs/ directory
- **THEN** they SHALL find an `architecture.md` file containing Mermaid diagrams

#### Scenario: Diagrams render on GitHub
- **WHEN** viewing `docs/architecture.md` on GitHub
- **THEN** all Mermaid diagrams SHALL render correctly without external tools

### Requirement: Architecture Diagrams in README

The README SHALL include or link to a high-level architecture diagram that provides immediate visual context for the project.

#### Scenario: Visual architecture in README
- **WHEN** a user reads the README.md file
- **THEN** they SHALL find either an embedded architecture diagram or a clear link to `docs/architecture.md`

#### Scenario: Architecture link in navigation
- **WHEN** viewing the README Documentation section
- **THEN** it SHALL include a link to architecture documentation: `[Architecture](docs/architecture.md) - Visual diagrams of system components and data flow`

### Requirement: Embedded Diagrams in Topic Documentation

Relevant documentation files SHALL embed simplified versions of architecture diagrams where they enhance understanding.

#### Scenario: Getting Started includes architecture context
- **WHEN** a user reads `docs/getting-started.md`
- **THEN** it MAY include a simplified architecture diagram showing the main components

#### Scenario: State Management includes decision tree
- **WHEN** a user reads `docs/state-management.md`
- **THEN** it SHALL include the state management decision tree diagram

### Requirement: Architecture Documentation Structure

The `docs/architecture.md` file SHALL organize diagrams with clear section headers and explanatory text.

#### Scenario: Organized diagram sections
- **WHEN** viewing the architecture documentation
- **THEN** it SHALL include sections for:
  - System Architecture (component layers)
  - Data Flow (transformation pipeline)
  - Deployment Workflow (step sequence)
  - State Management (decision criteria)
  - DNS Resolution (local vs remote paths)

#### Scenario: Diagram context provided
- **WHEN** viewing each diagram
- **THEN** it SHALL be accompanied by explanatory text describing what the diagram illustrates

### Requirement: Consistent Diagram Terminology

All architecture diagrams SHALL use terminology consistent with the rest of the documentation.

#### Scenario: Component naming consistency
- **WHEN** a diagram shows a component
- **THEN** the component name SHALL match terminology used in getting-started.md, dagger-reference.md, and other documentation

#### Scenario: Domain example consistency
- **WHEN** diagrams show example domain names
- **THEN** they SHALL use `.internal.lan` for local domains and `.example.com` or actual project domains for external access
