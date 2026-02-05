## Context

The project currently has text-based documentation that explains system architecture, data flow, and deployment workflows. Users must mentally construct the relationships between components and understand complex multi-step processes from prose alone. Visual diagrams would significantly improve comprehension, especially for:

- New users trying to understand how KCL, Dagger, Terraform, UniFi, and Cloudflare interact
- Visual learners who grasp systems faster through diagrams than text
- Developers needing to understand deployment sequencing and state management options
- Anyone trying to explain the project to others or create training materials

The diagrams will use **Mermaid**, a text-based diagram language that GitHub renders natively, avoiding the need for external image generation tools and ensuring diagrams remain maintainable as code.

## Goals / Non-Goals

**Goals:**
- Create comprehensive Mermaid diagrams covering all major system aspects
- Establish `docs/architecture.md` as the canonical location for visual documentation
- Embed simplified diagrams in relevant topic documentation where they add value
- Ensure all diagrams render correctly on GitHub without external dependencies
- Maintain consistent terminology with existing documentation
- Use colorblind-friendly styling where color is used

**Non-Goals:**
- Creating diagrams for every function or implementation detail
- Using external diagram tools that require PNG/SVG file management
- Creating UML diagrams or complex sequence diagrams beyond the deployment workflow
- Detailed network topology diagrams (out of scope for this documentation)
- Animated or interactive diagrams (Mermaid limitations)

## Decisions

### Decision: Use Mermaid for all diagrams

**Rationale:** Mermaid diagrams are text-based and rendered natively by GitHub, eliminating the need for external tools or binary image files in the repository. They're versionable, diffable, and maintainable alongside code.

**Alternatives considered:**
- **Draw.io/Lucid chart exports:** Requires external tools, produces binary files hard to review in PRs
- **PlantUML:** Similar to Mermaid but requires Java runtime, less GitHub integration
- **ASCII art:** Limited visual appeal, hard to create complex diagrams

**Trade-off:** Mermaid has syntax limitations and less fine-grained control than graphical tools, but the maintainability and GitHub integration benefits outweigh this.

### Decision: Create five core diagrams

**Selected diagrams:**
1. **System Architecture:** Component layers and relationships
2. **Data Flow:** Configuration transformation pipeline
3. **Deployment Workflow:** Step-by-step sequence diagram
4. **State Management:** Decision tree for backend options
5. **DNS Resolution:** Local vs remote access paths

**Rationale:** These five diagrams cover the most critical aspects users need to understand. They map to common questions: "How does it work?", "What happens during deployment?", "Which state backend should I use?", and "How does DNS resolution differ locally vs remotely?"

**Alternatives considered:**
- **More granular diagrams:** Rejected to avoid diagram overload and maintenance burden
- **Fewer diagrams:** Would leave gaps in visual documentation

### Decision: Organize diagrams in `docs/architecture.md`

**Rationale:** Centralizing diagrams in one location makes them easy to find and reference. This also keeps the main README concise while providing deep visual documentation for those who need it.

**Alternatives considered:**
- **Inline in existing docs:** Would fragment diagrams across multiple files
- **Separate file per diagram:** Excessive file proliferation

**Compromise:** Simplified versions of diagrams can be embedded in topic-specific docs (e.g., state management decision tree in `state-management.md`), but the comprehensive version lives in `architecture.md`.

### Decision: Use subgraphs for layered architecture

**Rationale:** Mermaid's subgraph feature allows visual grouping of components by layer (Configuration, Orchestration, Infrastructure, Network), making boundaries cleardespite the tool's limitations.

**Trade-off:** Subgraphs add verbosity to the Mermaid code but significantly improve diagram clarity.

### Decision: Use sequence diagram for deployment workflow

**Rationale:** Sequence diagrams excel at showing interaction order and message passing between actors (User, Dagger, Terraform, UniFi, Cloudflare). The deployment workflow is inherently sequential with clear phases.

**Alternatives considered:**
- **Flowchart:** Less effective for showing temporal sequence
- **Activity diagram:** Mermaid's activity diagram support is less mature

### Decision: Use decision tree graph for state management

**Rationale:** State backend selection is a decision-making process based on use case criteria. A graph with decision nodes visualizes this naturally.

**Implementation:** Use graph TD (top-down) with diamond-shaped decision nodes and rectangular outcome nodes.

### Decision: Distinguish secure tunnel connection visually

**Rationale:** The Cloudflare Tunnel connection is a critical security boundary. Using a different line style (dotted line) visually differentiates the secure tunnel from regular network connections.

## Risks / Trade-offs

### Risk: Diagrams may become outdated
**Mitigation:** Document diagrams as code in Mermaid, making them reviewable in PRs. Include diagram updates in the Definition of Done for related changes.

### Risk: Mermaid syntax changes break existing diagrams
**Mitigation:** Pin to stable Mermaid syntax patterns. GitHub's Mermaid rendering is conservative about breaking changes.

### Risk: Complex diagrams may be hard to read on mobile
**Mitigation:** Keep diagrams simple with minimal text. Test rendering on different zoom levels. Prefer multiple simple diagrams over one complex diagram.

### Risk: Color-only information encoding excludes colorblind users
**Mitigation:** Use shapes, labels, and line styles in addition to color. The secure tunnel uses dotted lines, not just color. Decision tree uses node shapes (diamond vs rectangle), not just color.

### Risk: Diagrams don't match implementation as code evolves
**Mitigation:** Include references in code to relevant diagrams. For example, the Dagger deployment function could link to the deployment workflow diagram in its docstring.

### Trade-off: Mermaid limitations vs maintainability
Mermaid can't do everything a visual editor can (fine-grained positioning, advanced styling). However, text-based diagrams are far more maintainable in version control and don't require external assets.

## Migration Plan

This is a documentation-only change with no runtime migration required.

**Implementation order:**
1. Create `docs/architecture.md` with all five diagrams
2. Embed simplified state management diagram in `docs/state-management.md`
3. Optionally embed simplified architecture in `docs/getting-started.md`
4. Update `docs/README.md` to reference architecture documentation
5. Add architecture link to main `README.md` in the Documentation section

**Rollback:** If diagrams are problematic, simply remove or comment them out. No runtime impact.

**Validation:** View all diagrams on GitHub web interface to confirm rendering. Test on both light and dark themes.

## Open Questions

- **Should we embed architecture diagram in main README or just link to it?**
  - Option A: Link only (keeps README concise)
  - Option B: Embed simplified version (provides immediate visual context)
  - **Recommendation:** Link only to keep README focused, but revisit if user feedback suggests embedding would help

- **Should diagram colors match any existing project branding?**
  - Currently project has no strong brand colors
  - **Recommendation:** Use default Mermaid colors or subtle professional palette, prioritize clarity over branding

- **Should we add a diagram showing Terraform provider dependency graph?**
  - Could visualize UniFi DNS → Cloudflare Tunnel dependency
  - **Recommendation:** Out of scope for this change, consider in future if users request it
