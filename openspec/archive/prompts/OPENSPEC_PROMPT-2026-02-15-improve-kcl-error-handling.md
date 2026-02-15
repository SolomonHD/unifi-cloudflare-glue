# OpenSpec Prompt: Improve KCL Error Messages

## Context

The [`generate_unifi_config()`](src/main/main.py:84) and [`generate_cloudflare_config()`](src/main/main.py:1619) functions in the Dagger module currently pipe KCL output directly to yq:

```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/unifi.k | yq eval -o=json '.'"
]).stdout()
```

When this fails, users cannot see what KCL actually output, making debugging difficult. The error message only shows that the piped command failed, not the actual KCL error or output.

## Goal

Refactor both [`generate_unifi_config()`](src/main/main.py:84) and [`generate_cloudflare_config()`](src/main/main.py:1619) functions to:
1. Execute KCL and capture output separately from yq conversion
2. Provide detailed, actionable error messages when failures occur
3. Show actual KCL output when yq parsing fails
4. Categorize errors by type (KCL execution, empty output, YAML conversion, JSON validation)

## Scope

### In Scope

- Modify [`generate_unifi_config()`](src/main/main.py:84) function (lines 84-162)
- Modify [`generate_cloudflare_config()`](src/main/main.py:1619) function (lines 1619-1698)
- Leverage existing [`KCLGenerationError`](src/main/main.py:41) exception class
- Improve error messages with hints and troubleshooting guidance
- Add truncation for large KCL outputs in error messages

### Out of Scope

- Changes to other functions in the module
- Adding new function parameters (debug flags, etc.) - this is a focused bug fix
- Changes to KCL generators themselves
- Changes to Terraform deployment functions

## Desired Behavior

### Current Behavior (Problematic)

When KCL produces invalid YAML or has syntax errors:
```
✗ KCL execution failed:
Exit code: 1
Stderr: (empty or unhelpful)

Hint: Check your KCL syntax with 'kcl run generators/unifi.k' locally.
```

### Expected Behavior (After Fix)

When yq fails to parse KCL output:
```
✗ YAML to JSON conversion failed:
yq error: (specific yq error)

KCL output that failed to parse:
------------------------------------------------------------
(devices: [name: test  # Note: missing closing brace
... (truncated if very long)
------------------------------------------------------------

Possible causes:
  - KCL validation warnings in output
  - Invalid YAML structure from generator
  - Syntax error in main.k or schemas

Hint: Run 'kcl run generators/unifi.k' locally to see raw output
```

When KCL itself fails:
```
✗ KCL execution failed:
Exit code: (actual exit code)
Stdout: (KCL stdout if any)
Stderr: (KCL stderr with actual error)

Hint: Check your KCL syntax with 'kcl run generators/unifi.k' locally.
```

## Implementation Details

### Step-by-Step Changes

For both functions, replace the single piped execution with:

1. **Pre-validation checks** (already exist - keep these):
   - Check for `kcl.mod` file
   - Check for generator file (`generators/unifi.k` or `generators/cloudflare.k`)

2. **KCL Execution Step** (NEW - separate from yq):
   ```python
   # Run KCL and capture output (don't pipe to yq yet)
   try:
       kcl_output = await ctr.with_exec([
           "kcl", "run", "generators/unifi.k"
       ]).stdout()
   except dagger.ExecError as e:
       # KCL itself failed - show the actual error
       raise KCLGenerationError(
           f"✗ KCL execution failed:\n"
           f"Exit code: {e.exit_code}\n"
           f"Stdout: {e.stdout}\n"
           f"Stderr: {e.stderr}\n"
           f"\nHint: Check your KCL syntax with 'kcl run generators/unifi.k' locally."
       )
   ```

3. **Empty Output Validation** (NEW):
   ```python
   # Validate KCL output is not empty
   if not kcl_output or not kcl_output.strip():
       raise KCLGenerationError(
           "✗ KCL produced empty output\n"
           "\nPossible causes:\n"
           "  - Generator file is empty\n"
           "  - KCL module has no output statements\n"
           "  - All configurations are commented out"
       )
   ```

4. **YAML to JSON Conversion Step** (NEW - separate execution):
   ```python
   # Try to convert YAML to JSON
   try:
       # Write KCL output to file, then convert
       ctr = ctr.with_new_file("/tmp/kcl-output.yaml", kcl_output)
       json_result = await ctr.with_exec([
           "sh", "-c",
           "yq eval -o=json '/tmp/kcl-output.yaml'"
       ]).stdout()
   except dagger.ExecError as e:
       # yq failed - show the problematic YAML
       max_yaml_show = 1000
       yaml_preview = kcl_output[:max_yaml_show]
       if len(kcl_output) > max_yaml_show:
           yaml_preview += "\n... (truncated)"
       
       raise KCLGenerationError(
           f"✗ YAML to JSON conversion failed:\n"
           f"yq error: {e.stderr}\n"
           f"\nKCL output that failed to parse:\n"
           f"{'-' * 60}\n"
           f"{yaml_preview}\n"
           f"{'-' * 60}\n"
           f"\nPossible causes:\n"
           "  - KCL validation warnings in output\n"
           "  - Invalid YAML structure from generator\n"
           "  - Syntax error in main.k or schemas\n"
           f"\nHint: Run 'kcl run generators/unifi.k' locally to see raw output"
       )
   ```

5. **JSON Validation Step** (keep existing, may enhance):
   ```python
   # Validate JSON output
   try:
       json.loads(json_result)
   except json.JSONDecodeError as e:
       raise KCLGenerationError(
           f"✗ Invalid JSON output after conversion:\n{str(e)}\n"
           f"\nRaw output:\n{json_result[:500]}"
       )
   ```

## Constraints & Assumptions

1. **Container Reference Preservation**: Each `with_exec()` returns a new container reference. Ensure proper variable assignment when writing files and executing commands.

2. **File Paths**: Use `/tmp/kcl-output.yaml` for temporary storage within the container.

3. **Truncation Limit**: Use 1000 characters as the maximum YAML preview length in error messages to prevent overwhelming output.

4. **Error Message Format**: Use existing error message format with `✗` prefix for consistency.

5. **Existing Checks**: Preserve existing pre-flight checks for `kcl.mod` and generator files.

6. **Return Type**: Both functions must continue to return `dagger.File` objects.

## Acceptance Criteria

- [ ] [`generate_unifi_config()`](src/main/main.py:84) executes KCL separately from yq conversion
- [ ] [`generate_cloudflare_config()`](src/main/main.py:1619) executes KCL separately from yq conversion
- [ ] When KCL fails, the actual KCL stderr/stdout is included in the error message
- [ ] When KCL produces empty output, a specific error message explains possible causes
- [ ] When yq fails, the actual KCL output (truncated if necessary) is shown in the error
- [ ] Error messages include actionable hints for local debugging
- [ ] JSON validation continues to work after yq conversion
- [ ] Both functions still return valid `dagger.File` objects on success
- [ ] No changes to function signatures (parameters and return types unchanged)

## Files to Modify

| File | Lines | Description |
|------|-------|-------------|
| [`src/main/main.py`](src/main/main.py) | 138-159 | Replace piped execution in `generate_unifi_config()` |
| [`src/main/main.py`](src/main/main.py) | 1674-1695 | Replace piped execution in `generate_cloudflare_config()` |

## Dependencies

- None - this is a standalone improvement
- The [`KCLGenerationError`](src/main/main.py:41) exception class already exists

## Testing Verification

After implementation, test with:

1. **Valid KCL config**: Should produce valid JSON output file
2. **KCL syntax error**: Should show KCL's actual error message
3. **Empty KCL output**: Should show empty output error with causes
4. **Invalid YAML from KCL**: Should show KCL output that failed yq parsing
5. **Large KCL output with error**: Should truncate output in error message
