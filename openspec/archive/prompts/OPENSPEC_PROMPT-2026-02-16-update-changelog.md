# OpenSpec Prompt: Update CHANGELOG for Breaking Change

## Context

Removing the `no_cache` parameter is a breaking change that requires documentation in CHANGELOG.md under a new version section.

## Goal

Add a new section to CHANGELOG.md documenting the removal of `--no-cache` flag as a breaking change with migration guidance.

## Scope

### In Scope
- Add new version section (## [Unreleased] or ## [0.10.0])
- Document `no_cache` parameter removal as breaking change
- Provide migration guidance showing `--cache-buster=$(date +%s)` replacement
- Explain rationale (Dagger function-level caching limitation)

### Out of Scope
- Modifying any existing CHANGELOG entries
- Updating version in other files (separate version bump task)

## Desired Behavior

Add a new section at the top of CHANGELOG.md:

```markdown
## [Unreleased]

### ⚠️ BREAKING CHANGES

**Removed `--no-cache` Flag**

Removed the `no_cache` boolean parameter from all Dagger functions (`deploy`, `plan`, `destroy`, `test_integration`) due to Dagger's aggressive function-level caching making it ineffective with remote backends.

**Migration:**
```bash
# Before (v0.9.x)
dagger call deploy --no-cache ...

# After (v0.10.0+)
dagger call deploy --cache-buster=$(date +%s) ...
```

**Rationale:** Dagger caches function results based on input parameters. The boolean `no_cache=True` became part of the cache key, causing Dagger to return cached results without executing the function. The explicit `--cache-buster` with shell command substitution provides a truly unique value on each invocation.

**Affected Functions:**
- `deploy()` - Remove `--no-cache`, use `--cache-buster=$(date +%s)`
- `plan()` - Remove `--no-cache`, use `--cache-buster=$(date +%s)`
- `destroy()` - Remove `--no-cache`, use `--cache-buster=$(date +%s)`
- `test_integration()` - Remove `--no-cache`, use `--cache-buster=$(date +%s)`
```

## Constraints & Assumptions

- Add as the first section in CHANGELOG.md
- Use "⚠️ BREAKING CHANGES" heading for visibility
- Include migration guidance with before/after examples
- Explain the technical rationale  
- Link to relevant Dagger caching documentation if available

## Acceptance Criteria

1. New [Unreleased] or version section added at top of CHANGELOG.md
2. Breaking change clearly marked with ⚠️ symbol
3. Migration guidance shows exact command replacement
4. Rationale explains Dagger's caching behavior
5. Lists all four affected functions
6. Follows existing CHANGELOG.md formatting conventions

## Expected Changes

- ~20-30 new lines at top of CHANGELOG.md
- Clear, actionable migration path for users
