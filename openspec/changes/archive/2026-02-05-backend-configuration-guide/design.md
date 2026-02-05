## Context

Users encounter confusion when configuring Terraform backends for this project due to incomplete documentation about S3 state locking options. While the Dagger module already supports both S3 native lockfile (Terraform 1.9+) and traditional DynamoDB locking, the documentation doesn't adequately explain:
- The difference between the two mechanisms
- When to use each approach
- That DynamoDB is NOT deprecated

This leads to suboptimal configuration choices, unnecessary DynamoDB infrastructure for teams that could use the simpler S3 lockfile, or incorrect assumptions that DynamoDB is obsolete.

**Current State:**
- Existing backend config examples exist but don't distinguish locking mechanisms
- [`examples/backend-configs/README.md`](../../examples/backend-configs/README.md) mentions S3 and DynamoDB but lacks comparison
- No centralized documentation explaining backend choices
- Dagger module functions already accept backend configs in YAML/HCL format (no code changes needed)

**Stakeholders:**
- **Users**: Need clear guidance to choose appropriate locking mechanism
- **Maintainers**: Want documentation that prevents support questions
- **Contributors**: Benefit from consistent examples

## Goals / Non-Goals

**Goals:**
- Create comprehensive backend configuration guide at [`docs/backend-configuration.md`](../../docs/backend-configuration.md)
- Provide clear, working examples for both S3 lockfile and DynamoDB approaches
- Establish decision criteria through a decision tree
- Clarify that DynamoDB remains fully supported (not deprecated)
- Document migration path from DynamoDB to S3 lockfile for qualified users
- Update existing example files with notes directing users to specific examples

**Non-Goals:**
- Changing Dagger module code (already supports both mechanisms)
- Deprecating or removing DynamoDB support
- Modifying Terraform module internals
- Adding support for other backend types beyond documentation updates
- Creating automated migration tooling

## Decisions

### Decision 1: Separate Example Files vs Single Parameterized Example

**Chosen:** Create separate [`s3-backend-lockfile.yaml`](../../examples/backend-configs/s3-backend-lockfile.yaml) and [`s3-backend-dynamodb.yaml`](../../examples/backend-configs/s3-backend-dynamodb.yaml)

**Rationale:**
- Makes intent immediately clear from filename
- Users can copy the appropriate file without modification
- Reduces cognitive load (no if/then logic needed)
- Inline comments can be specific to each locking mechanism

**Alternative Considered:** Single file with conditional parameters
- ❌ Rejected: Requires users to understand both mechanisms before making choice
- ❌ Rejected: Comments become cluttered explaining conditional logic

### Decision 2: Documentation Structure - Dedicated Guide vs Inline Examples

**Chosen:** Create comprehensive [`docs/backend-configuration.md`](../../docs/backend-configuration.md) with examples pulled into brief [`examples/backend-configs/README.md`](../../examples/backend-configs/README.md)

**Rationale:**
- Centralizes authoritative backend guidance
- Examples directory README stays focused on quick reference
- Easier to maintain single source of truth
- Supports linking from main README and other docs

**Alternative Considered:** All documentation in examples README
- ❌ Rejected: Examples directory would mix reference with educational content
- ❌ Rejected: Harder to link to specific concepts from other documentation

### Decision 3: Decision Tree Format

**Chosen:** Text-based decision tree with yes/no branches in markdown code block

**Rationale:**
- Works in all markdown renderers (GitHub, IDEs, static site generators)
- No external image hosting or rendering dependencies
- Easy to update as requirements change
- Copy-pastable for user notes

**Alternative Considered:** Flowchart diagram (Mermaid or image)
- ❌ Rejected: Mermaid not supported in all environments
- ❌ Rejected: Images require separate maintenance and accessibility concerns

### Decision 4: Migration Guide Scope

**Chosen:** Provide step-by-step migration from DynamoDB to S3 lockfile, but emphasize it's optional

**Rationale:**
- Users with existing DynamoDB should know migration is safe if they want it
- Must counter any pressure to migrate created by S3 lockfile documentation
- Migration is low-risk (backend config change only, no state modification)

**Alternative Considered:** No migration guide (assume users know Terraform)
- ❌ Rejected: Users might attempt unsafe migration without proper backend reconfiguration
- ❌ Rejected: Some users legitimately want to simplify infrastructure

### Decision 5: Cost Information Inclusion

**Chosen:** Include approximate DynamoDB cost (~$0.25/month) with disclaimer

**Rationale:**
- Cost is often decision factor, especially for small teams
- Transparency builds trust
- Disclaimer prevents stale cost information from causing issues

**Alternative Considered:** Omit cost information
- ❌ Rejected: Users will Google it anyway and find varying answers
- ❌ Rejected: Cost transparency is important for infrastructure decisions

## Risks / Trade-offs

### Risk: Users misinterpret "S3 lockfile" as replacement signal
**Mitigation:** Explicitly state in multiple places that DynamoDB is NOT deprecated and both options remain fully supported. Emphasize "alternative" not "replacement" language.

### Risk: Cost information becomes outdated
**Mitigation:** Use approximation (~$0.25/month) with disclaimer referencing AWS pricing. Include last-verified date in comment.

### Risk: Decision tree oversimplifies edge cases
**Mitigation:** Decision tree addresses common scenarios but documentation includes nuanced discussion. Tree serves as starting point, not absolute rule.

### Risk: Examples may drift from working Dagger module usage
**Mitigation:** Examples include actual Dagger call commands showing integration. Testing with real deployments during implementation validates examples.

### Trade-off: Separate files increase maintenance burden
**Benefit:** Clarity for users outweighs maintenance cost. If backend parameters change, both files need updates, but automation via testing can validate consistency.

### Trade-off: Comprehensive documentation increases onboarding reading
**Benefit:** Users can jump directly to needed section. Quick-start examples in main README still provide fast path. Detailed guide serves as reference.

## Migration Plan

This is a documentation-only change with no deployment steps.

**Implementation Order:**
1. Create [`docs/backend-configuration.md`](../../docs/backend-configuration.md) with full content
2. Create [`s3-backend-lockfile.yaml`](../../examples/backend-configs/s3-backend-lockfile.yaml) example
3. Create [`s3-backend-dynamodb.yaml`](../../examples/backend-configs/s3-backend-dynamodb.yaml) example
4. Update [`examples/backend-configs/s3-backend.hcl`](../../examples/backend-configs/s3-backend.hcl) with notes
5. Update [`examples/backend-configs/s3-backend.yaml`](../../examples/backend-configs/s3-backend.yaml) with notes
6. Update [`examples/backend-configs/README.md`](../../examples/backend-configs/README.md) with section on locking
7. Add link in [`README.md`](../../README.md) to backend configuration guide
8. Update [`docs/README.md`](../../docs/README.md) with link to new guide

**Rollback Strategy:**
Not applicable - documentation can be reverted via git without affecting users. No deployment risk.

**Validation:**
- All example files render correctly in markdown viewers
- YAML syntax validates (linting)
- Dagger commands in examples execute successfully against test infrastructure
- Decision tree logic is consistent with detailed documentation
- All internal links resolve correctly

## Open Questions

None - this is straightforward documentation work with clear requirements from the prompt file.
