# Design: Fix yq Parsing Bug

## Overview

This change fixes the YAML-to-JSON conversion bug in the Dagger module's KCL configuration generation functions.

## Technical Design

### Current Implementation (Broken)

Both `generate_unifi_config` and `generate_cloudflare_config` use the same problematic pattern:

```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/unifi.k | yq -o=json '.result'"
]).stdout()
```

**Issues:**
1. `yq -o=json '.result'` syntax is ambiguous when piping YAML from stdin
2. The `.result` filter tries to extract a key while the `-o=json` flag tries to convert format
3. yq v4+ uses `eval` as the explicit command for expression evaluation

### Proposed Implementation (Fixed)

```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/unifi.k | yq eval -o=json '.'"
]).stdout()
```

**Changes:**
1. Add explicit `eval` command to yq
2. Use `'.'` to select the entire document instead of just `.result`
3. The `-o=json` flag then converts the entire selected document to JSON

### Why This Works

1. **Explicit eval**: yq v4+ requires explicit `eval` command for expression evaluation when not using the shorthand syntax
2. **Full document selection**: Using `'.'` selects the entire YAML document, which contains the `result` key at the root level
3. **Proper pipe handling**: The explicit syntax handles piped YAML input more reliably

### Files Modified

- `src/main/main.py` - Two line changes at:
  - Line 142: `generate_unifi_config` function
  - Line 1678: `generate_cloudflare_config` function

### Testing Strategy

1. Test with sample KCL configuration
2. Verify JSON output is valid
3. Verify the generated JSON contains expected structure
4. Test both `generate-unifi-config` and `generate-cloudflare-config` Dagger functions

## Alternatives Considered

### Option 1: Use KCL's native JSON output
```python
"kcl run -o json generators/unifi.k"
```
**Rejected**: KCL may not support native JSON output in all versions, and the current approach with yq provides more control.

### Option 2: Use Python yaml library instead of yq
```python
# Parse YAML in Python instead of using yq
```
**Rejected**: Would require significant refactoring and additional dependencies in the container.

### Option 3: Keep `.result` filter but fix syntax
```python
"kcl run generators/unifi.k | yq eval '.result' -o=json"
```
**Rejected**: The `.result` filter is actually unnecessary since the KCL output is already the result object. Using `'.'` is simpler and more reliable.

## Implementation Notes

- The fix is minimal and low-risk
- No changes to the KCL generators or output format
- No changes to downstream Terraform modules
- Container dependencies remain the same (kcllang/kcl base image with yq installed)
