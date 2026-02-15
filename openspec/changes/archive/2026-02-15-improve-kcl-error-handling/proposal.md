## Why

The [`generate_unifi_config()`](src/main/main.py:84) and [`generate_cloudflare_config()`](src/main/main.py:1619) functions currently pipe KCL output directly to yq, making it impossible to see actual KCL errors when failures occur. When yq fails to parse KCL output, users only see that the piped command failed, not the actual KCL error or the problematic YAML output. This makes debugging difficult and time-consuming.

## What Changes

- Refactor [`generate_unifi_config()`](src/main/main.py:84) to execute KCL and capture output separately from yq conversion
- Refactor [`generate_cloudflare_config()`](src/main/main.py:1619) to execute KCL and capture output separately from yq conversion
- Add detailed error categorization for different failure types (KCL execution, empty output, YAML conversion, JSON validation)
- Provide actionable error messages with hints and troubleshooting guidance
- Add truncation for large KCL outputs in error messages (max 1000 characters)
- Leverage existing [`KCLGenerationError`](src/main/main.py:41) exception class
- Preserve all existing pre-validation checks for `kcl.mod` and generator files

## Capabilities

### New Capabilities
- `kcl-error-handling`: Improved error reporting and debugging for KCL configuration generation

### Modified Capabilities
- None - This is a focused bug fix that improves error handling without changing requirements

## Impact

**Affected Code:**
- `src/main/main.py` - Lines 138-159 (generate_unifi_config) and 1674-1695 (generate_cloudflare_config)
- No changes to function signatures or return types

**API Compatibility:**
- No breaking changes - function signatures remain identical
- Functions continue to return `dagger.File` objects on success

**Dependencies:**
- No new dependencies required
- Uses existing `KCLGenerationError` exception class

**User Experience:**
- Users will see detailed error messages instead of generic "pipe failed" errors
- Error messages include the actual KCL output when yq parsing fails
- Hints guide users to run KCL locally for debugging
