## Why

The documentation lacks visual representations of the system architecture, data flow, and component interactions. Without diagrams, users must piece together mental models from text-only documentation, making it harder to understand how KCL configurations flow through Dagger containers to Terraform modules and ultimately to UniFi and Cloudflare APIs. Visual learners and newcomers would benefit from seeing the relationships, sequences, and decision trees depicted graphically.

## What Changes

- Create new `docs/architecture.md` with comprehensive Mermaid diagrams
- Develop five core diagrams: system architecture, data flow, deployment workflow, state management decision tree, and DNS resolution paths
- Embed simplified diagrams into existing documentation (getting-started.md, state-management.md)
- Update `docs/README.md` index to reference architecture documentation
- Add architecture diagram link from main README

All diagrams will use GitHub-native Mermaid format to ensure rendering without external tools, with consistent terminology matching existing documentation.

## Capabilities

### New Capabilities

- `architecture-visualization`: Provide visual representations of system components, relationships, and layers (Configuration, Orchestration, Infrastructure, Network)
- `data-flow-diagram`: Illustrate the transformation pipeline from KCL configuration through validation to infrastructure deployment
- `deployment-workflow-diagram`: Show the step-by-step sequence of deployment operations including UniFi and Cloudflare phases
- `state-management-decision-tree`: Present decision criteria for choosing ephemeral, local persistent, or remote backend options
- `dns-resolution-diagram`: Visualize local network vs remote access paths with UniFi DNS and Cloudflare Tunnel connectivity

### Modified Capabilities

- `documentation`: Add architecture.md as a new documentation file and embed diagrams in existing docs

## Impact

**Documentation Files:**
- `docs/architecture.md` (new): Primary location for all architecture diagrams
- `docs/getting-started.md`: Embed simplified architecture diagram
- `docs/state-management.md`: Embed state management decision tree
- `docs/README.md`: Add architecture documentation to index
- `README.md`: Link to architecture documentation

**User Experience:**
- Improved onboarding for visual learners
- Faster comprehension of system design
- Clearer understanding of deployment workflows and state management trade-offs
- Better mental model of DNS resolution paths

**Maintenance:**
- Diagrams must be kept in sync with code changes
- Mermaid syntax limitations may constrain diagram complexity
- Consider colorblind-friendly palette choices
