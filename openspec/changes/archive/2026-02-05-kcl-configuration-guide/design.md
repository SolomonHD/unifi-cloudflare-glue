## Context

The KCL configuration system is the heart of this project - users define their infrastructure in KCL, which generates Terraform-compatible JSON for both providers. However, documentation has focused on the Terraform modules and Dagger orchestration, leaving KCL schemas minimally documented. Users encounter validation errors without understanding the rules, struggle to debug KCL syntax issues, and lack reference patterns for common scenarios.

The existing [`kcl/README.md`](../../../kcl/README.md) covers generator usage and cross-provider validation but doesn't explain individual schemas, validation rules, or debugging approaches. The existing [`examples/homelab-media-stack/`](../../../examples/homelab-media-stack/) demonstrates one complex scenario but doesn't provide simple starting points or explain the "why" behind configuration choices.

This design addresses purely documentation additions - no schema or generator changes are needed.

## Goals / Non-Goals

**Goals:**
- Comprehensive KCL schema reference covering all base, UniFi, and Cloudflare schemas
- Clear explanation of validation rules with rationale (why these constraints exist)
- Common configuration patterns with working examples
- Systematic debugging guide from syntax errors through validation failures
- Multiple working examples covering different use cases (simple to complex)
- Cross-linked documentation improving discoverability

**Non-Goals:**
- Changes to KCL schemas themselves (existing schemas are correct)
- New KCL features or additional validation rules
- General KCL language tutorial (link to official docs instead)
- Generator implementation details (focus on usage, not internals)
- Terraform module documentation (separate from KCL configuration)

## Decisions

### Decision 1: Single comprehensive guide vs. multiple specialized docs

**Chosen:** Single `docs/kcl-guide.md` with structured sections

**Rationale:**
- Easier to search and navigate one cohesive document
- Users can read sequentially (learn) or jump to sections (reference)
- Reduced maintenance burden (one file to update when schemas evolve)
- Clearer progression: schemas → validation → patterns → debugging

**Alternatives considered:**
- Multiple files (docs/kcl-schemas.md, docs/kcl-validation.md, etc.): Creates fragmentation, harder to cross-reference
- Inline documentation in schema files: Mixes implementation with user docs, not beginner-friendly
- Wiki-style separate pages: Requires hosting/tooling beyond static markdown

### Decision 2: Documentation structure order

**Chosen:** Schema reference → Validation rules → Configuration patterns → Debugging guide → Examples

**Rationale:**
- Progressive disclosure: Learn concepts before patterns
- Schema reference first enables understanding validation rules
- Patterns build on schema knowledge
- Debugging guide references schemas and validation
- Examples demonstrate everything together

**Alternatives considered:**
- Examples first: Confusing without schema understanding
- Debugging first: Can't debug without knowing what's valid
- Alphabetical schemas: Loses pedagogical flow (base → provider-specific)

### Decision 3: Example organization strategy

**Chosen:** Separate example directories (single-service, multiple-services, internal-only, external-only) with complete working code

**Rationale:**
- Each example is self-contained and runnable
- Users can copy entire directory as starting point
- Clear separation of concerns (one pattern per directory)
- Easy to validate examples independently

**Alternatives considered:**
- Inline examples in guide only: Can't run them, harder to copy
- Single examples directory with numbered subdirectories: Less descriptive naming
- Embed examples in existing homelab-media-stack: Already too complex for learning

### Decision 4: Validation rule documentation approach

**Chosen:** Explain WHAT the rule is, WHY it exists, and HOW to fix violations

**Rationale:**
- "What" gives users immediate understanding
- "Why" builds mental model (prevents future mistakes)
- "How" enables self-service debugging
- Reduces support burden by making errors self-explanatory

**Alternatives considered:**
- Just list rules: Users don't understand rationale, repeat mistakes
- Just show fixes: Doesn't build understanding, mechanical copying
- Error messages only: Buried in code, not discoverable

### Decision 5: Cross-reference and linking strategy

**Chosen:** Bidirectional links between main README → docs README → kcl-guide → kcl/README → examples

**Rationale:**
- Users can enter documentation from multiple starting points
- Clear navigation between conceptual docs and working code
- Improved discoverability (users find what they need faster)
- Maintains documentation hierarchy (general → specific)

**Alternatives considered:**
- `Single entry point only: Users miss docs if they start elsewhere
-` Heavy cross-linking within docs: Creates maintenance burden
- No linking: Docs remain siloed and hard to discover

## Risks / Trade-offs

### Risk: Documentation drift from schema implementation
**Mitigation:** Each schema example references actual schema files, making inconsistencies obvious. Link examples in CI validation to catch drift early.

### Risk: Examples become outdated with schema changes
**Mitigation:** Include `kcl run` validation commands in example READMEs. CI can run these to detect breakage.

### Risk: Too much detail Overwhelms beginners
**Mitigation:** Progressive disclosure structure - comprehensive reference sections but simple examples first. Quick start links to minimal examples.

### Trade-off: Single large file vs. multiple small files
**Choice:** Single `kcl-guide.md` (5-10 pages)
**Consequence:** Longer scrolling, but better searchability and contextual understanding. Markdown TOC helps navigation.

### Trade-off: Detailed validation explanations add length
**Choice:** Explain validation rules comprehensively with rationale
**Consequence:** Longer documentation, but users build mental models and make fewer mistakes. Self-service debugging reduces support burden.

## Migration Plan

N/A - Pure documentation addition, no code changes or deployment required.

Documentation will be added to repository and immediately available. No rollback needed (additive change only).

## Open Questions

None - This is a straightforward documentation addition based on existing, stable schemas and validation logic.
