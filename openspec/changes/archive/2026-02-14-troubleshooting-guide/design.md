## Context

The `docs/troubleshooting.md` file currently contains only placeholder content. Users need a comprehensive troubleshooting resource that covers all components of the unifi-cloudflare-glue system: Dagger, Terraform, KCL, UniFi Controller, and Cloudflare. This design document outlines the structure and approach for creating this resource.

## Goals / Non-Goals

**Goals:**
- Provide systematic troubleshooting guidance for all system components
- Document common error messages with actionable solutions
- Create decision trees for efficient problem diagnosis
- Include diagnostic commands for health checking each component
- Add FAQ section addressing common questions
- Enable self-service troubleshooting to reduce support burden

**Non-Goals:**
- Detailed debugging of user-specific network issues
- Terraform internals documentation (link to official docs)
- KCL language bugs (link to KCL issue tracker)
- Provider-specific bugs (link to provider repositories)
- Real-time troubleshooting assistance

## Decisions

### Document Structure

**Decision:** Organize troubleshooting guide by component, then by error type within each component.

**Rationale:** Users typically know which component is failing (e.g., "Terraform plan failed"). Component-first organization allows quick navigation to relevant solutions.

**Alternatives considered:**
- Error type first (authentication, connectivity, validation) - Rejected because errors manifest differently per component
- Workflow stage first (install, configure, deploy) - Rejected because same errors can occur at multiple stages

### Error Entry Format

**Decision:** Each error entry follows a consistent format: Symptoms, Cause, Solution, Prevention.

**Rationale:** Consistent format enables quick scanning. Prevention tips reduce recurrence.

**Format:**
```markdown
#### Error Name
**Symptoms:** What the user sees
**Cause:** Why it happens
**Solution:** How to fix it
**Prevention:** How to avoid it
```

### Decision Tree Format

**Decision:** Use ASCII-art flowcharts embedded in markdown code blocks.

**Rationale:** Pure text format works in all markdown renderers, no external dependencies, version-control friendly.

**Example:**
```
Deployment fails
├─ At what stage?
   ├─ Configuration generation
   │  └─ KCL validation → See KCL Errors
   ├─ Terraform init
   │  └─ Backend issues → See Terraform Init
   └─ Terraform plan/apply
      ├─ UniFi → See UniFi Errors
      └─ Cloudflare → See Cloudflare Errors
```

### Diagnostic Commands Section

**Decision:** Provide copy-paste ready commands for each component.

**Rationale:** Users in troubleshooting mode need immediate, actionable commands. Each command includes expected output examples.

### FAQ Structure

**Decision:** Organize FAQ by frequency and impact, with cross-references to detailed error entries.

**Rationale:** Common questions should be answerable quickly. Cross-references provide depth when needed.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Error messages become outdated | Use generic error patterns; link to official docs for version-specific details |
| Missing edge cases | Include "Getting Help" section with GitHub issues link |
| Too long to navigate | Use TOC and clear section headers; decision trees for quick routing |
| Solutions don't work in all environments | Note environment-specific variations; test commands on multiple platforms |

## Migration Plan

1. Replace placeholder content in `docs/troubleshooting.md` with comprehensive guide
2. Update `docs/README.md` index to reflect new sections
3. Add troubleshooting link to main `README.md`
4. Add cross-references from related docs (security.md, state-management.md, etc.)

No rollback needed - this is additive documentation.
