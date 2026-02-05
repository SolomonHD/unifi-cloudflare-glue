# OpenSpec Prompt: Architecture Diagrams

## Context

The documentation lacks visual representations of the system architecture, data flow, and component interactions, making it harder for users to understand how the pieces fit together.

## Goal

Create visual diagrams using Mermaid to illustrate system architecture, data flow, deployment workflows, and state management options.

## Scope

### In Scope

1. Create [`docs/architecture.md`](../../docs/architecture.md) with diagrams
2. Add Mermaid diagrams for:
   - System architecture (components and relationships)
   - Data flow (KCL → Dagger → Terraform → APIs)
   - Deployment workflow (steps and dependencies)
   - State management comparison
   - DNS resolution flow (local/remote)
3. Embed diagrams in appropriate documentation sections
4. Ensure diagrams render correctly in GitHub

### Out of Scope

- External diagram tools (PNG/SVG) - use Mermaid only
- UML diagrams beyond basic architecture
- Detailed sequence diagrams for every function
- Network topology diagrams

## Desired Behavior

### Documentation Structure: docs/architecture.md

```markdown
# Architecture Documentation

## System Architecture

```mermaid
graph TB
    User[User] --> KCL[KCL Configuration]
    KCL --> Dagger[Dagger Module]
    Dagger --> TF[Terraform]
    TF --> UniFi[UniFi Controller]
    TF --> CF[Cloudflare API]
    
    UniFi --> LocalDNS[Local DNS]
    CF --> Tunnel[Cloudflare Tunnel]
    CF --> EdgeDNS[Edge DNS]
    
    Tunnel --> Service[Internal Service]
    LocalDNS --> Service
```

## Data Flow

Shows KCL configuration transformation to infrastructure

## Deployment Workflow

Shows deploy/destroy orchestration steps

## State Management

Comparison of ephemeral/local/remote state

## DNS Resolution

How requests are routed locally vs remotely
```

### Diagram 1: System Architecture

```mermaid
graph TB
    subgraph "Configuration Layer"
        KCL[KCL Schemas]
        Config[User Configuration]
    end
    
    subgraph "Orchestration Layer"
        Dagger[Dagger Module]
        TFEngine[Terraform Engine]
    end
    
    subgraph "Infrastructure Layer"
        UniFi[UniFi Controller]
        Cloudflare[Cloudflare API]
    end
    
    subgraph "Network Layer"
        LocalDNS[Local DNS Records]
        Tunnel[Cloudflare Tunnel]
        EdgeDNS[Edge DNS  Records]
    end
    
    Config --> KCL
    KCL --> Dagger
    Dagger --> TFEngine
    TFEngine --> UniFi
    TFEngine --> Cloudflare
    UniFi --> LocalDNS
    Cloudflare --> Tunnel
    Cloudflare --> EdgeDNS
```

### Diagram 2: Data Flow

```mermaid
flowchart LR
    A[main.k Configuration] --> B[KCL Validation]
    B --> C{Valid?}
    C -->|No| D[Error: Fix Configuration]
    C -->|Yes| E[Generate JSON]
    E --> F[UniFi JSON]
    E --> G[Cloudflare JSON]
    F --> H[Terraform Apply - UniFi]
    G --> I[Terraform Apply - Cloudflare]
    H --> J[Local DNS Created]
    I --> K[Tunnel & Edge DNS Created]
```

### Diagram 3: Deployment Workflow

```mermaid
sequenceDiagram
    participant User
    participant Dagger
    participant Terraform
    participant UniFi
    participant Cloudflare
    
    User->>Dagger: dagger call deploy
    Dagger->>Dagger: Generate configs
    Dagger->>Terraform: terraform init
    
    rect rgb(200, 220, 250)
    Note right of Terraform: Phase 1: UniFi DNS
    Terraform->>UniFi: Create DNS records
    UniFi-->>Terraform: Success
    end
    
    rect rgb(220, 250, 200)
    Note right of Terraform: Phase 2: Cloudflare
    Terraform->>Cloudflare: Create tunnels
    Terraform->>Cloudflare: Create DNS
    Cloudflare-->>Terraform: Success
    end
    
    Terraform-->>Dagger: Infrastructure ready
    Dagger-->>User: ✓ Deployment complete
```

### Diagram 4: State Management Options

```mermaid
graph TD
    A[State Management] --> B{Choose Option}
    
    B -->|Development| C[Ephemeral State]
    B -->|Solo Developer| D[Persistent Local]
    B -->|Team/Production| E[Remote Backend]
    
    C --> C1[Container only<br/>Lost on exit<br/>No setup required]
    D --> D1[Local filesystem<br/>--state-dir flag<br/>No cloud costs]
    E --> E1{Backend Type}
    
    E1 --> S3[S3]
    E1 --> Azure[Azure Blob]
    E1 --> GCS[GCS]
    
    S3 --> S3a{Locking}
    S3a -->|Terraform 1.9+| S3b[S3 Lockfile]
    S3a -->|All versions| S3c[DynamoDB]
```

### Diagram 5: DNS Resolution Flow

```mermaid
flowchart TB
    subgraph "Local Network"
        Client[Client Device]
        UniFi[UniFi DNS]
        Service[Internal Service]
    end
    
    subgraph "Cloudflare Edge"
        EdgeDNS[Edge DNS]
        Tunnel[Tunnel Connector]
    end
    
    Client -->|Local Request<br/>media.internal.lan| UniFi
    UniFi --> Service
    
    Client -->|External Request<br/>media.example.com| Internet
    Internet --> EdgeDNS
    EdgeDNS --> Tunnel
    Tunnel -.->|Secure Connection| Service
    
    style Service fill:#90EE90
    style Tunnel fill:#87CEEB
```

## Constraints & Assumptions

### Constraints

- Use Mermaid only (GitHub-native rendering)
- Keep diagrams simple and focused
- Ensure text is readable at normal zoom
- Test rendering in GitHub markdown preview

### Assumptions

- Users understand basic network concepts
- Visual learners benefit from diagrams
- Diagrams complement, not replace, text documentation
- GitHub renders Mermaid correctly

## Acceptance Criteria

- [ ] [`docs/architecture.md`](../../docs/architecture.md) created with comprehensive diagrams
- [ ] System architecture diagram shows all components
- [ ] Data flow diagram shows transformation pipeline
- [ ] Deployment workflow diagram shows step sequence
- [ ] State management diagram shows decision tree
- [ ] DNS resolution diagram shows local/remote paths
- [ ] All diagrams render correctly in GitHub
- [ ] Diagrams embedded in relevant documentation sections
- [ ] Links added from main README to architecture docs
- [ ] Diagrams use consistent styling and terminology

## Expected Files/Areas Touched

- `docs/architecture.md` (new)
- `docs/getting-started.md` (embed simplified architecture diagram)
- `docs/state-management.md` (embed state management diagram)
- `docs/README.md` (update index)
- `README.md` (add architecture diagram, link to full docs)

## Dependencies

- Prompt 01 (docs structure must exist)
- Prompt 03 (state management docs for context)

## Notes

- Mermaid is natively supported by GitHub, no external tools needed
- Keep diagrams simple - complex diagrams are hard to maintain
- Use consistent terminology from documentation
- Consider colorblind-friendly colors
- Test rendering on both light and dark GitHub themes
