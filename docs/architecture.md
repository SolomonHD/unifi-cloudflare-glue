# Architecture

This document provides visual diagrams of the `unifi-cloudflare-glue` system architecture, data flow, deployment workflow, and DNS resolution paths. All diagrams use [Mermaid](https://mermaid.js.org/) syntax for native GitHub rendering.

## Table of Contents

- [System Architecture](#system-architecture)
- [Data Flow](#data-flow)
- [Deployment Workflow](#deployment-workflow)
- [State Management](#state-management)
- [DNS Resolution](#dns-resolution)

---

## System Architecture

The system is organized into four distinct layers, each responsible for a specific aspect of the infrastructure management pipeline.

```mermaid
graph TB
    subgraph "Configuration Layer"
        KCL[KCL Schemas<br/>schemas/]
        USER[User Config<br/>main.k]
    end

    subgraph "Orchestration Layer"
        DAGGER[Dagger Module<br/>Containerized Pipeline]
        TF[Terraform Engine]
    end

    subgraph "Infrastructure Layer"
        UNIFI[UniFi Controller API]
        CF[Cloudflare API]
    end

    subgraph "Network Layer"
        LOCAL[Local DNS<br/>.internal.lan]
        TUNNEL[Cloudflare Tunnel]
        EDGE[Edge DNS<br/>.example.com]
    end

    USER -->|Defines Services| KCL
    KCL -->|Generates Config| DAGGER
    DAGGER -->|Orchestrates| TF
    TF -->|Manages| UNIFI
    TF -->|Manages| CF
    UNIFI -->|Creates| LOCAL
    CF -->|Creates| TUNNEL
    CF -->|Creates| EDGE
    TUNNEL -.->|Secure Connection| LOCAL

    style USER fill:#e1f5ff
    style DAGGER fill:#fff4e1
    style UNIFI fill:#e8f5e9
    style CF fill:#e8f5e9
    style LOCAL fill:#fce4ec
    style TUNNEL fill:#fce4ec
    style EDGE fill:#fce4ec
```

### Layer Descriptions

| Layer | Components | Purpose |
|-------|------------|---------|
| **Configuration** | KCL schemas, user `main.k` | Define services once in a unified format |
| **Orchestration** | Dagger module, Terraform | Containerized pipeline for reproducible deployments |
| **Infrastructure** | UniFi Controller, Cloudflare API | Target APIs for DNS and tunnel management |
| **Network** | Local DNS, Tunnel, Edge DNS | Runtime name resolution and access paths |

---

## Data Flow

This diagram illustrates the complete transformation pipeline from KCL configuration through validation to infrastructure deployment.

```mermaid
flowchart TD
    A[main.k Configuration] --> B[KCL Validation]
    B -->|Valid?| C{Decision}
    C -->|No| D[Fix Configuration]
    D --> A
    C -->|Yes| E[Generate JSON]
    E --> F[unifi.json]
    E --> G[cloudflare.json]
    F --> H[Terraform Apply<br/>UniFi Module]
    G --> I[Terraform Apply<br/>Cloudflare Module]
    H --> J[Local DNS Created<br/>media.internal.lan]
    I --> K[Tunnel Created]
    I --> L[Edge DNS Created<br/>media.example.com]

    style A fill:#e1f5ff
    style C fill:#fff9c4
    style D fill:#ffebee
    style J fill:#e8f5e9
    style K fill:#e8f5e9
    style L fill:#e8f5e9
```

### Flow Description

1. **Configuration**: User defines services in `main.k` using KCL schemas
2. **Validation**: KCL validates the configuration for correctness
3. **Error Path**: Invalid configurations must be fixed before proceeding
4. **JSON Generation**: Valid configurations generate provider-specific JSON
5. **Parallel Deployment**: UniFi and Cloudflare deployments happen sequentially
6. **Final State**: Both local DNS and remote access are established

---

## Deployment Workflow

The sequence diagram shows the step-by-step interaction between components during a deployment.

```mermaid
sequenceDiagram
    actor User
    participant Dagger
    participant Terraform
    participant UniFi
    participant Cloudflare

    User->>Dagger: dagger call deploy
    Dagger->>Dagger: Generate KCL configs
    Dagger->>Terraform: terraform init

    rect rgb(225, 245, 254)
        Note over Dagger,UniFi: Phase 1: UniFi DNS
        Dagger->>Terraform: terraform apply (unifi-dns)
        Terraform->>UniFi: Create DNS records
        UniFi-->>Terraform: Success
        Terraform-->>Dagger: UniFi complete
    end

    rect rgb(255, 243, 224)
        Note over Dagger,Cloudflare: Phase 2: Cloudflare Tunnel & DNS
        Dagger->>Terraform: terraform apply (cloudflare-tunnel)
        Terraform->>Cloudflare: Create tunnel
        Cloudflare-->>Terraform: Tunnel created
        Terraform->>Cloudflare: Create edge DNS records
        Cloudflare-->>Terraform: DNS records created
        Terraform-->>Dagger: Cloudflare complete
    end

    Dagger-->>User: Deployment successful
```

### Phase Breakdown

| Phase | Provider | Resources Created | Dependencies |
|-------|----------|-------------------|--------------|
| **Phase 1** | UniFi | DNS A records for local resolution | None |
| **Phase 2** | Cloudflare | Tunnel, Edge DNS records, Config | UniFi DNS (for local_service_url validation) |

---

## State Management

The decision tree helps you choose the appropriate state management strategy based on your use case.

```mermaid
graph TD
    A[State Management] --> B{Use Case?}

    B -->|Development<br/>Testing<br/>CI/CD| C[Ephemeral State]
    B -->|Solo Developer<br/>Local Dev| D[Persistent Local State]
    B -->|Team/Production| E[Remote Backend]

    C --> C1[Container-only storage]
    C --> C2[Lost on exit]
    C --> C3[No setup required]

    D --> D1[Local filesystem]
    D --> D2[--state-dir flag]
    D --> D3[No cloud costs]

    E --> F{Backend Type?}
    F -->|AWS| G[S3 Backend]
    F -->|Azure| H[Azure Blob]
    F -->|GCP| I[GCS Backend]

    G --> J{Locking?}
    J -->|Terraform 1.9+| K[S3 Lockfile<br/>Native locking]
    J -->|All Versions| L[DynamoDB<br/>Lock table]

    H --> M[Built-in locking]
    I --> N[Built-in locking]

    style A fill:#e1f5ff
    style C fill:#ffebee
    style D fill:#fff9c4
    style E fill:#e8f5e9
    style K fill:#e1f5ff
    style L fill:#e1f5ff
```

### State Management Options

| Option | Persistence | Setup | Best For |
|--------|-------------|-------|----------|
| **Ephemeral** | Container only | None | Quick tests, CI/CD |
| **Persistent Local** | Host filesystem | `--state-dir` flag | Solo development |
| **Remote Backend** | Cloud storage | Backend config file | Team environments, production |

### S3 Locking Compatibility

| Method | Terraform Version | Notes |
|--------|-------------------|-------|
| S3 Lockfile | 1.9+ | Native S3 locking, no extra resources |
| DynamoDB | All versions | Requires DynamoDB table for locking |

---

## DNS Resolution

This diagram shows how DNS resolution differs for local network access versus external access.

```mermaid
flowchart TB
    subgraph "Local Network"
        CLIENT[Client Device]
        UNIFI_DNS[UniFi DNS]
        SERVICE[Internal Service<br/>media.internal.lan]
    end

    subgraph "Internet"
        INTERNET[Internet]
    end

    subgraph "Cloudflare Edge"
        EDGE_DNS[Edge DNS]
        TUNNEL[Cloudflare Tunnel]
    end

    CLIENT -->|Local Request<br/>media.internal.lan| UNIFI_DNS
    UNIFI_DNS -->|Returns 192.168.x.x| SERVICE

    CLIENT -.->|External Request<br/>media.example.com| INTERNET
    INTERNET --> EDGE_DNS
    EDGE_DNS --> TUNNEL
    TUNNEL -.->|Secure Tunnel| SERVICE

    style CLIENT fill:#e1f5ff
    style SERVICE fill:#e8f5e9
    style TUNNEL fill:#fce4ec
    style UNIFI_DNS fill:#fff9c4
    style EDGE_DNS fill:#fff9c4
```

### Resolution Paths

| Path | Domain Example | Flow | Use Case |
|------|----------------|------|----------|
| **Local** | `media.internal.lan` | Client → UniFi DNS → Service | Home network access |
| **External** | `media.example.com` | Client → Internet → Edge DNS → Tunnel → Service | Remote access |

### Security Note

The tunnel connection (dotted line) represents an encrypted connection through Cloudflare's network, providing secure access to internal services without exposing them directly to the internet.

---

## Related Documentation

- [Getting Started](getting-started.md) - Installation and first deployment
- [State Management](state-management.md) - Detailed state backend configuration
- [Dagger Reference](dagger-reference.md) - Complete function reference
- [KCL Configuration Guide](kcl-guide.md) - Schema reference and examples
