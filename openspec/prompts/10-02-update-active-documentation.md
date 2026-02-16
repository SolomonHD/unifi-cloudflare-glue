# OpenSpec Prompt: Update Active Documentation for cache-buster

## Context

After removing the `no_cache` parameter from Python code, all user-facing documentation needs to be updated to show only the `--cache-buster` pattern.

## Goal

Update README.md and docs/*.md files to replace all `--no-cache` examples with `--cache-buster=$(date +%s)`.

## Scope

### In Scope
- `README.md` - Update all command examples
- `docs/dagger-reference.md` - Update parameter tables and examples
- `docs/deployment-patterns.md` - Update cache busting documentation section

### Out of Scope
- `README.old.md` - Archived file
- `openspec/archive/**` - Historical documentation
- `openspec/specs/**` - Archived specs

## Desired Behavior

### Example Replacements

**Before:**
```bash
# Force fresh execution (bypass Dagger cache)
dagger call deploy \\
    --kcl-source=./kcl \\
    --unifi-url=https://unifi.local:8443 \\
    --unifi-api-key=env:UNIFI_API_KEY \\
    --no-cache
```

**After:**
```bash
# Force fresh execution (bypass Dagger cache)
dagger call deploy \\
    --kcl-source=./kcl \\
    --unifi-url=https://unifi.local:8443 \\
    --unifi-api-key=env:UNIFI_API_KEY \\
    --cache-buster=$(date +%s)
```

### Parameter Table Updates

**Before (docs/dagger-reference.md):**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--no-cache` | ❌ | Bypass Dagger cache |
| `--cache-buster` | ❌ | Custom cache key |

**After:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `--cache-buster` | ❌ |Unique value to bypass cache (use `$(date +%s)`) |

### Text Explanations needed

Add explanation in docs/deployment-patterns.md about why explicit timestamps are required:

```markdown
### Cache Control

Due to Dagger's function-level caching, explicit cache busting is required:

```bash
# Bypass cache with timestamp
dagger call deploy --cache-buster=$(date +%s) ...
```

The `$(date +%s)` shell substitution provides a unique epoch timestamp on each invocation,
forcing Dagger to execute fresh rather than return cached results.
```

## Constraints & Assumptions

- Only update files users actually read (README.md, docs/*.md)
- Don't update archived/historical files
- Maintain consistency across all documentation
- Preserve all other documentation content

## Acceptance Criteria

1. No mention of `--no-cache` flag in README.md
2. No mention of `--no-cache` flag in docs/*.md files
3. All examples consistently use `--cache-buster=$(date +%s)` pattern
4. Parameter tables updated to show only cache-buster
5. Explanation added about why explicit timestamps are needed
6. Examples are syntactically correct and copy-pasteable

## Files to Modify

- `README.md` (~3-5 occurrences)
- `docs/dagger-reference.md` (~5-10 occurrences)
- `docs/deployment-patterns.md` (cache control section)
