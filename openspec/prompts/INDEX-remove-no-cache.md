# OpenSpec Change Index: Remove no_cache Parameter

## Overview

This change removes the `--no-cache` parameter from all Dagger functions due to its unreliable behavior with Dagger's aggressive function-level caching. Users will use explicit `--cache-buster=$(date +%s)` instead.

## Motivation 

Dagger caches function results based on function code and input parameters. When `no_cache=True`, this becomes part of the cache key, and Dagger returns cached results without executing the function body. Various attempts to break this cache (timestamp injection, unique return values, command modification) failed because the caching happens at a level above the function execution.

The explicit `--cache-buster` parameter with shell command substitution is more reliable because each invocation provides a genuinely different input value that Dagger cannot optimize away.

## Breaking Change

**Version Impact**: Minor version bump recommended (e.g., v0.9.3 → v0.10.0)

**Migration Path**:
```bash
# Before
dagger call deploy --no-cache ...

# After  
dagger call deploy --cache-buster=$(date +%s) ...
```

## Change Sequence

The prompts should be executed in order:

1. **01-remove-no-cache-from-python.md** - Remove parameter from all function signatures and logic
2. **02-update-active-documentation.md** - Update README and docs/ directory
3. **03-update-changelog.md** - Document as breaking change

## Out of Scope

- Archive files (`openspec/archive/**`)
- Historical spec files (`openspec/specs/**`)  
- Test files (if any exist)

These contain historical context but don't need updates since they're not user-facing.
