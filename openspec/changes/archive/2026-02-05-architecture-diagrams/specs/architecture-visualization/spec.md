## ADDED Requirements

### Requirement: System architecture diagram SHALL visualize component layers

The documentation SHALL include a system architecture diagram that shows the four main layers: Configuration Layer (KCL schemas and user config), Orchestration Layer (Dagger module and Terraform engine), Infrastructure Layer (UniFi Controller and Cloudflare API), and Network Layer (local DNS, tunnels, and edge DNS).

#### Scenario: User views architecture diagram
- **WHEN** a user opens the architecture documentation
- **THEN** they SHALL see a diagram clearly showing component relationships across all four layers

#### Scenario: Components are labeled for clarity
- **WHEN** a diagram shows a component
- **THEN** each component SHALL have a clear label indicating its purpose

### Requirement: Architecture diagram SHALL use Mermaid format

The architecture diagrams SHALL be written in Mermaid syntax to ensure native rendering on GitHub without external tools.

#### Scenario: Diagram renders on GitHub
- **WHEN** architecture documentation is viewed on GitHub
- **THEN** all Mermaid diagrams SHALL render correctly without broken syntax

#### Scenario: Diagram syntax validation
- **WHEN** Mermaid code is committed
- **THEN** the syntax SHALL be valid according to Mermaid specifications

### Requirement: Component relationships SHALL be clearly depicted

The system SHALL show directional relationships between components indicating data flow or dependencies.

#### Scenario: Data flow direction is visible
- **WHEN** viewing the architecture diagram
- **THEN** arrows SHALL indicate the direction of data or control flow between components

#### Scenario: Layer boundaries are evident
- **WHEN** viewing the architecture diagram
- **THEN** subgraph containers SHALL clearly separate the four architectural layers
