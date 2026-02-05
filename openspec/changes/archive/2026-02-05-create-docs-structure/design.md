## Context

The current README.md is 1355 lines and has grown organically over time as features were added. Users report difficulty finding specific information, and maintainers struggle to keep sections synchronized when making updates. The monolithic structure combines quickstart guides, detailed API references, security practices, and troubleshooting in a single scrolling document.

This change restructures documentation into a modular system where the README becomes a navigation hub (~300 lines) linking to specialized topic files in a `docs/` directory.

## Goals / Non-Goals

**Goals:**
- Create topic-based documentation files organized by user journey and technical depth
- Reduce README to ~300 lines while preserving all existing content
- Establish clear navigation paths for different user personas (new users, advanced users, CI/CD)
- Improve maintenance by separating concerns into independent files
- Maintain all existing examples, warnings, and technical details (no content loss)

**Non-Goals:**
- Creating new documentation content (subsequent prompts will add backend guides, troubleshooting, etc.)
- Expanding KCL documentation (separate change)
- Automated link checking infrastructure (manual verification acceptable for this change)
- Changing documentation format/tooling (remains Markdown)

## Decisions

### Decision: docs/ Directory Structure

**Choice:** Organize by topic (getting-started, dagger-reference, security) rather than by audience (beginner/, advanced/) or component (kcl/, terraform/, dagger/).

**Rationale:**
- Topic-based organization maps to user intent ("I need to configure a backend") better than skill level
- Component-based structure would create artificial boundaries (e.g., state management involves both Terraform and Dagger)
- Most documentation systems (Django, Rails, AWS) use topic-based organization successfully

**Alternatives considered:**
- Audience-based (beginner/advanced): Users don't self-identify accurately, same person may be beginner in one area and advanced in another
- Component-based (kcl/, terraform/, dagger/): Many topics cross components, would require duplication or confusing cross-references

### Decision: README Target Length (~300 Lines)

**Choice:** Target 300 lines for condensed README with enforcement through clear guidance in specs, not strict validation.

**Rationale:**
- 300 lines is readable in ~5 minutes at typical reading speed
- Enough space for overview, quick start, navigation, and project structure
- Too strict enforcement would compromise quality if important information needs inclusion

**Alternatives considered:**
- Strict 300-line limit: Could force artificial terseness or loss of important context
- No target: "Make it shorter" without specifics provides unclear guidance

### Decision: Content Migration Strategy

**Choice:** Split content semantically by preserving complete sections (move entire "State Management" section to state-management.md rather than splitting across files).

**Rationale:**
- Preserves context and flow within topics
- Easier to verify completeness (whole sections move, nothing lost)
- Reduces broken internal references within migrated sections

**Alternatives considered:**
- Split by size: Would break logical topic flow, harder to verify completeness
- Complete rewrite: Higher risk, time-consuming, unnecessary when existing content is accurate

### Decision: Backup Original README

**Choice:** Create README.old.md as backup before transformation.

**Rationale:**
- Provides safety net if migration has issues
- Users with bookmarks to specific sections can reference old structure
- Enables easy rollback if problems discovered post-migration

**Alternatives considered:**
- No backup: Git history provides backup, but README.old.md is more accessible to users
- Version suffix (README.v1.md): Less clear that it's deprecated/backup

### Decision: Placeholder Files for Future Content

**Choice:** Create backend-configuration.md and troubleshooting.md as placeholders (with brief "Coming soon" notes) now, to be populated by subsequent prompts.

**Rationale:**
- Establishes complete documentation structure immediately
- Links from README work even before content added
- Later prompts know exact file locations to populate

**Alternatives considered:**
- Don't create until needed: Would require updating README navigation later, breaks link integrity temporarily
- Create with stub content: Could be misleading if stub doesn't match eventual content

## Risks / Trade-offs

### Risk: Link Breakage
**Issue:** Internal links could break during content migration, causing 404s for users.
**Mitigation:** 
- Manual verification of all internal links after migration
- Relative path testing in both GitHub web view and local rendering
- Include link format examples in specs to ensure consistency

### Risk: Incomplete Content Migration
**Issue:** Sections could be accidentally omitted during split, losing important information.
**Mitigation:**
- Compare line count of original README vs sum of all new files
- Checklist in tasks.md for each major section to migrate
- Keep README.old.md for comparison reference

### Risk: User Bookmark Breakage
**Issue:** Users with bookmarked README#section-name URLs will get 404s after restructuring.
**Mitigation:**
- README could include brief redirect notes for major removed sections
- README.old.md remains accessible for transitional period
- Update CHANGELOG.md to note documentation restructuring

### Risk: Documentation Synchronization
**Issue:** With content split across files, keeping related information synchronized becomes harder. **Trade-off:** Accept this in exchange for better organization - proper cross-linking and clear ownership of sections will minimize this risk.

### Trade-off: Navigation Overhead
**Benefit:** Topic-focused files improve findability for specific information.
**Cost:** Users reading linearly must click through multiple files instead of scrolling one document.
**Justification:** Most users access documentation via search or direct links (GitHub search, IDE search), not linear reading - modular structure optimizes for the common case.

### Trade-off: Maintenance Complexity
**Benefit:** Changes to specific topics don't require editing the entire README.
**Cost:** Cross-cutting changes (e.g., updating authentication approach) might require updates across multiple files.
**Justification:** Cross-cutting changes are rarer than topic-specific updates, and clear cross-linking will make identifying related files straightforward.

## Open Questions

None - the design is straightforward content reorganization with well-established patterns.
