## Context

The `no_cache` boolean parameter has been removed from the Python Dagger module code in the `remove-no-cache-from-python` change. However, user-facing documentation still references `--no-cache` in examples and parameter tables. This creates a disconnect between the documentation and the actual code, leading to user confusion when commands fail due to the removed parameter.

Dagger's function-level caching is extremely aggressive. The `--no-cache` flag was a boolean that became part of the cache key itself, making it ineffective. The correct approach is using `--cache-buster=$(date +%s)` which provides a unique timestamp on each invocation, forcing fresh execution.

## Goals / Non-Goals

**Goals:**
- Update all user-facing documentation to use `--cache-buster=$(date +%s)` pattern
- Remove all references to `--no-cache` from README.md and docs/*.md
- Ensure parameter tables accurately reflect available options
- Add explanation about why explicit timestamps are required
- Maintain consistency across all documentation

**Non-Goals:**
- Modifying any code (this is documentation-only)
- Updating archived/historical files (README.old.md, openspec/archive/**)
- Changing the underlying cache-busting mechanism
- Adding new functionality

## Decisions

### Decision: Replace all `--no-cache` with `--cache-buster=$(date +%s)`
**Rationale**: The `--no-cache` parameter no longer exists in the code. Users need working examples that match the actual API.

### Decision: Add explanation about Dagger's caching behavior
**Rationale**: Users need to understand why `$(date +%s)` is required. Simply showing the command without context doesn't teach the underlying concept.

### Decision: Exclude archived files from updates
**Rationale**: README.old.md and openspec/archive/** are historical records. Updating them would obscure the evolution of the codebase.

### Decision: Use consistent `--cache-buster=$(date +%s)` syntax everywhere
**Rationale**: Consistency reduces cognitive load. Users can copy-paste examples without modification.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Users with old documentation bookmarks may be confused | Add prominent note in README about the change |
| Missing some `--no-cache` references | Perform case-insensitive search across all target files |
| Inconsistent updates across files | Review all changes in single PR for consistency |

## Migration Plan

This is a documentation-only change with no migration needed for users. The `--cache-buster` parameter has been available and functional; users simply need to update their command invocations if they were using `--no-cache`.

## Open Questions

None. The scope is well-defined from the prompt file.
