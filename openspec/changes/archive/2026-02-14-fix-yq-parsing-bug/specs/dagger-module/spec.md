# Dagger Module Specification: Fix yq Parsing Bug

## Scope

This specification covers the fix for the yq parsing bug in the Dagger module's KCL configuration generation functions.

## Changes

### File: `src/main/main.py`

#### Change 1: Fix `generate_unifi_config` function (line 142)

**Before:**
```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/unifi.k | yq -o=json '.result'"
]).stdout()
```

**After:**
```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/unifi.k | yq eval -o=json '.'"
]).stdout()
```

#### Change 2: Fix `generate_cloudflare_config` function (line 1678)

**Before:**
```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/cloudflare.k | yq -o=json '.result'"
]).stdout()
```

**After:**
```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/cloudflare.k | yq eval -o=json '.'"
]).stdout()
```

## Technical Details

### yq Command Syntax

The fix addresses a syntax issue with yq v4+:

- **Old (broken)**: `yq -o=json '.result'`
  - Omits the explicit `eval` command
  - Uses `.result` filter which may not work correctly with piped YAML

- **New (fixed)**: `yq eval -o=json '.'`
  - Uses explicit `eval` command (required in yq v4+)
  - Uses `.` to select the entire document
  - The `-o=json` flag then converts to JSON format

### Why This Works

1. KCL outputs YAML format containing the `result` variable at the root level
2. The `.` selector selects the entire document (which is the `result` object)
3. `-o=json` converts the selected YAML to JSON
4. The explicit `eval` command ensures proper expression evaluation

## Testing

### Test Command for UniFi Config
```bash
dagger call generate-unifi-config --source=./kcl export --path=./test-unifi.json
cat test-unifi.json | jq '.'  # Verify valid JSON
```

### Test Command for Cloudflare Config
```bash
dagger call generate-cloudflare-config --source=./kcl export --path=./test-cloudflare.json
cat test-cloudflare.json | jq '.'  # Verify valid JSON
```

### Expected Output

Both commands should:
1. Complete without errors
2. Produce valid JSON files
3. Not show "mapping values are not allowed in this context" error

## Dependencies

No changes to dependencies:
- Still uses `kcllang/kcl` base container image
- Still installs yq via curl
- No new Python dependencies

## Backwards Compatibility

This is a bug fix with no breaking changes:
- Function signatures remain the same
- Input/output behavior remains the same
- Only fixes the internal yq command syntax
