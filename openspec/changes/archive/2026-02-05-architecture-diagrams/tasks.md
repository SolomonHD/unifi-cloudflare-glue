## 1. Create Architecture Documentation File

- [x] 1.1 Create `docs/architecture.md` with file header and introduction
- [x] 1.2 Add "System Architecture" section with component layers diagram (Mermaid graph)
- [x] 1.3 Add "Data Flow" section with transformation pipeline diagram (Mermaid flowchart)
- [x] 1.4 Add "Deployment Workflow" section with sequence diagram (Mermaid sequenceDiagram)
- [x] 1.5 Add "State Management" section with decision tree diagram (Mermaid graph)
- [x] 1.6 Add "DNS Resolution" section with local/remote paths diagram (Mermaid flowchart)

## 2. System Architecture Diagram

- [x] 2.1 Create Mermaid graph showing Configuration Layer (KCL, User Config)
- [x] 2.2 Add Orchestration Layer (Dagger, Terraform) to diagram
- [x] 2.3 Add Infrastructure Layer (UniFi Controller, Cloudflare API) to diagram
- [x] 2.4 Add Network Layer (Local DNS, Tunnel, Edge DNS) to diagram
- [x] 2.5 Add directional arrows showing relationships between layers and components
- [x] 2.6 Test diagram rendering on GitHub (both light and dark themes)

## 3. Data Flow Diagram

- [x] 3.1 Create flowchart starting with "main.k Configuration"
- [x] 3.2 Add KCL validation step with decision diamond (Valid? Yes/No)
- [x] 3.3 Add error path for validation failure ("Fix Configuration")
- [x] 3.4 Add JSON generation step splitting into UniFi and Cloudflare paths
- [x] 3.5 Add Terraform apply steps for both providers
- [x] 3.6 Add final state nodes (Local DNS Created, Tunnel & Edge DNS Created)
- [x] 3.7 Verify flowchart renders correctly and follows logical sequence

## 4. Deployment Workflow Sequence Diagram

- [x] 4.1 Create sequence diagram with participants (User, Dagger, Terraform, UniFi, Cloudflare)
- [x] 4.2 Add initial user action (`dagger call deploy`)
- [x] 4.3 Add Dagger config generation and terraform init steps
- [x] 4.4 Add Phase 1 box (colored rectangle) for UniFi DNS creation
- [x] 4.5 Add Phase 2 box (different color) for Cloudflare operations
- [x] 4.6 Add success response arrows flowing back from services to user
- [x] 4.7 Test sequence rendering and verify phase separation is visually clear

## 5. State Management Decision Tree

- [x] 5.1 Create decision tree starting with "State Management" root node
- [x] 5.2 Add three main branches (Development, Solo Developer, Team/Production)
- [x] 5.3 Add characteristics for ephemeral state option
- [x] 5.4 Add characteristics for persistent local state option
- [x] 5.5 Add remote backend sub-decision (S3, Azure Blob, GCS)
- [x] 5.6 Add S3 locking sub-decision (S3 lockfile vs DynamoDB)
- [x] 5.7 Add version compatibility note for S3 lockfile (Terraform 1.9+)
- [x] 5.8 Verify decision tree provides clear guidance for option selection

## 6. DNS Resolution Flow Diagram

- [x] 6.1 Create diagram with "Local Network" subgraph containing Client, UniFi DNS, Service
- [x] 6.2 Create "Cloudflare Edge" subgraph containing Edge DNS and Tunnel
- [x] 6.3 Add local resolution path (Client → UniFi DNS → Service) with example domain
- [x] 6.4 Add external resolution path (Client → Internet → Edge DNS → Tunnel → Service)
- [x] 6.5 Use dotted line style for secure tunnel connection
- [x] 6.6 Add color styling to differentiate Service and Tunnel visually
- [x] 6.7 Test rendering and verify subgraph boundaries are clear

## 7. Embed Diagrams in Existing Documentation

- [x] 7.1 Add state management decision tree diagram to `docs/state-management.md`
- [x] 7.2 Optionally add simplified architecture diagram to `docs/getting-started.md`
- [x] 7.3 Verify embedded diagrams render correctly in their target files

## 8. Update Documentation Navigation

- [x] 8.1 Add architecture documentation entry to `docs/README.md` index
- [x] 8.2 Add architecture link to main `README.md` Documentation section
- [x] 8.3 Use format: `[Architecture](docs/architecture.md) - Visual diagrams of system components and data flow`
- [x] 8.4 Verify all cross-reference links resolve correctly

## 9. Validation and Testing

- [x] 9.1 View all diagrams on GitHub web interface to confirm rendering
- [x] 9.2 Test diagrams on both GitHub light and dark themes
- [x] 9.3 Validate Mermaid syntax using Mermaid live editor or CLI
- [x] 9.4 Check diagram terminology matches existing documentation
- [x] 9.5 Verify diagram text is readable at normal zoom levels
- [x] 9.6 Review diagrams with colorblind simulation tool for accessibility
- [x] 9.7 Test all internal documentation links (no 404 errors)

## 10. Documentation Updates

- [x] 10.1 Update CHANGELOG.md with entry for architecture diagrams
- [x] 10.2 Verify diagram file sizes are reasonable (text files should be small)
- [x] 10.3 Add comment in code referencing relevant diagrams (e.g., Dagger deploy function → deployment workflow)
