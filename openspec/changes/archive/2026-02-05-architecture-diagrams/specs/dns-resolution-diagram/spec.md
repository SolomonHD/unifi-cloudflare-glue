## ADDED Requirements

### Requirement: DNS resolution SHALL show local and remote access paths

The documentation SHALL include a diagram illustrating how client devices resolve DNS differently for local network requests (via UniFi DNS) versus external requests (via Cloudflare Edge).

#### Scenario: Local network path is visualized
- **WHEN** a client makes a local network request
- **THEN** the diagram SHALL show the request path from Client Device → UniFi DNS → Internal Service

#### Scenario: External access path is visualized
- **WHEN** a client makes an external request
- **THEN** the diagram SHALL show the request path from Client Device → Internet → Edge DNS → Tunnel → Internal Service

### Requirement: Domain naming conventions SHALL be illustrated

The diagram SHALL show example domain names for local (.internal.lan) versus external (.example.com) access patterns.

#### Scenario: Local domain example
- **WHEN** viewing the local resolution path
- **THEN** the diagram SHALL include an example like "media.internal.lan"

#### Scenario: External domain example
- **WHEN** viewing the external resolution path
- **THEN** the diagram SHALL include an example like "media.example.com"

### Requirement: Network boundaries SHALL be clearly delineated

The diagram SHALL use subgraph containers or visual boundaries to distinguish the Local Network from the Cloudflare Edge.

#### Scenario: Local network components grouped
- **WHEN** viewing the diagram
- **THEN** Client Device, UniFi DNS, and Internal Service SHALL be grouped within a "Local Network" boundary

#### Scenario: Cloudflare Edge components grouped
- **WHEN** viewing the diagram
- **THEN** Edge DNS and Tunnel Connector SHALL be grouped within a "Cloudflare Edge" boundary

### Requirement: Secure tunnel connection SHALL be distinguished

The diagram SHALL visually differentiate the secure tunnel connection from regular network paths (e.g., using a different line style).

#### Scenario: Tunnel connection is visually distinct
- **WHEN** viewing the connection from Tunnel to Internal Service
- **THEN** the connection SHALL use a different visual style (dotted line, different color, etc.) than direct connections

#### Scenario: Security is indicated
- **WHEN** viewing the tunnel connection
- **THEN** the connection SHALL be labeled or annotated to indicate it's a secure connection
