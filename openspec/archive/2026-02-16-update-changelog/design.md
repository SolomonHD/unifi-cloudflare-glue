## Context

The `remove-no-cache-from-python` change has removed the `no_cache` boolean parameter from all Dagger functions (`deploy`, `plan`, `destroy`, `test_integration`). This is a breaking change that requires documentation in CHANGELOG.md to inform users about:
1. What was removed
2. Why it was removed (Dagger caching behavior)
3. How to migrate (use `--cache-buster=$(date +%s)`)

The CHANGELOG.md already follows the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format with an existing `[Unreleased]` section at the top.

## Goals / Non-Goals

**Goals:**
- Add clear breaking change documentation to CHANGELOG.md
- Provide actionable migration guidance with before/after examples
- Explain the technical rationale for the change
- List all affected functions

**Non-Goals:**
- Modifying any existing changelog entries
- Changing version numbers in other files
- Implementing code changes (this is documentation-only)

## Decisions

**Decision: Add to existing [Unreleased] section**
- **Rationale:** There is already an `[Unreleased]` section at the top of CHANGELOG.md
- **Approach:** Add the breaking change subsection under the existing `### Breaking Changes` heading, or create one if it doesn't exist
- **Placement:** At the top of the `[Unreleased]` section to maximize visibility

**Decision: Use ⚠️ symbol for visibility**
- **Rationale:** Breaking changes need to stand out for users scanning the changelog
- **Format:** `### ⚠️ BREAKING CHANGES` heading with clear subsections

**Decision: Include technical rationale**
- **Rationale:** Users need to understand WHY the change was made to accept the migration path
- **Content:** Explain Dagger's function-level caching and why `no_cache=True` became part of the cache key

## Risks / Trade-offs

**[Risk] Users may miss the breaking change notice**
→ **Mitigation:** Use prominent ⚠️ symbol, place at top of [Unreleased] section, include in Breaking Changes subsection

**[Risk] Migration example may be unclear**
→ **Mitigation:** Provide exact before/after command examples showing the flag replacement

**[Risk] Users may not understand the technical rationale**
→ **Mitigation:** Keep explanation concise but include the key point about Dagger caching behavior
