# OpenSpec Change Prompt

## Context
The `test_integration` function in `src/main/main.py` currently uses a `cache_buster` string parameter that requires users to manually provide a unique value (e.g., `--cache-buster=$(date +%s)`) to force Dagger cache invalidation. This is awkward UX and not user-friendly.

## Goal
Add a `--no-cache` boolean flag that automatically generates epoch time internally, providing a cleaner CLI experience while maintaining backward compatibility with the existing `cache_buster` parameter.

## Scope

**In scope:**
- Add `no_cache: bool` parameter to `test_integration` function
- When `no_cache=True`, automatically set `cache_buster` to current epoch time
- Keep existing `cache_buster` parameter for advanced use cases
- Update docstring with new parameter and usage examples
- Add validation: error if both `no_cache` and `cache_buster` are provided
- Update CHANGELOG.md with the new feature

**Out of scope:**
- Removing the `cache_buster` parameter
- Changes to other functions
- Documentation outside CHANGELOG.md

## Desired Behavior
- `dagger call test-integration --no-cache` → automatically uses epoch time as cache buster
- `dagger call test-integration --cache-buster=1234567890` → uses provided value (existing behavior)
- `dagger call test-integration --no-cache --cache-buster=1234567890` → error: "Cannot use both --no-cache and --cache-buster"
- Neither flag provided → normal caching behavior (existing)

## Constraints & Assumptions
- Use `int(time.time())` to generate epoch timestamp
- Must import `time` module if not already present
- Backward compatibility: existing `cache_buster` usage must continue to work
- The `no_cache` parameter should default to `False`

## Acceptance Criteria
- [ ] `test_integration` has new `no_cache: bool = False` parameter
- [ ] When `no_cache=True`, `cache_buster` is automatically set to str(int(time.time()))
- [ ] Validation prevents using both flags simultaneously with clear error message
- [ ] Docstring updated with `--no-cache` examples
- [ ] CHANGELOG.md updated under [Unreleased] section
