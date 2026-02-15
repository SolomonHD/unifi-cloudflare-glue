## Context

The current implementation of [`generate_unifi_config()`](src/main/main.py:84) and [`generate_cloudflare_config()`](src/main/main.py:1619) uses a single piped shell command:

```python
result = await ctr.with_exec([
    "sh", "-c",
    "kcl run generators/unifi.k | yq eval -o=json '.'"
]).stdout()
```

When this command fails, the error only indicates that the piped command failed, not which specific step failed or what the actual KCL output was. This creates a poor debugging experience for users.

## Goals / Non-Goals

**Goals:**
- Separate KCL execution from yq conversion to isolate failure points
- Provide detailed error messages showing actual KCL stdout/stderr when KCL fails
- Display problematic KCL output when yq parsing fails (with truncation for large outputs)
- Categorize errors by type (KCL execution, empty output, YAML conversion, JSON validation)
- Maintain backward compatibility with existing function signatures and return types

**Non-Goals:**
- Adding new function parameters (debug flags, etc.) - this is a focused bug fix
- Changes to KCL generators themselves
- Changes to Terraform deployment functions
- Changes to other functions in the module

## Decisions

### Decision: Execute KCL and yq as separate steps
**Rationale:** Piping KCL directly to yq loses the intermediate output. By executing KCL first and capturing its output, we can inspect it before passing to yq.

**Implementation:**
```python
# Step 1: Run KCL and capture output
kcl_output = await ctr.with_exec(["kcl", "run", "generators/unifi.k"]).stdout()

# Step 2: Write to file and convert with yq
ctr = ctr.with_new_file("/tmp/kcl-output.yaml", kcl_output)
json_result = await ctr.with_exec([
    "sh", "-c", "yq eval -o=json '/tmp/kcl-output.yaml'"
]).stdout()
```

### Decision: Use temporary file for yq input
**Rationale:** yq works best with file inputs. Writing KCL output to `/tmp/kcl-output.yaml` allows yq to process it reliably.

**Alternative considered:** Passing KCL output directly via stdin. Rejected because it would require complex shell escaping and doesn't improve error visibility.

### Decision: Truncate large outputs at 1000 characters
**Rationale:** Very large KCL outputs can overwhelm error messages. A 1000-character limit provides enough context while keeping messages readable.

### Decision: Preserve existing `KCLGenerationError` exception class
**Rationale:** The exception class already exists and provides the right semantics. We'll enhance the error messages passed to it.

### Decision: Maintain backward compatibility
**Rationale:** This is a bug fix, not a breaking change. Function signatures, return types, and behavior on success remain unchanged.

## Risks / Trade-offs

**[Risk] Container reference management complexity**
Each `with_exec()` and `with_new_file()` returns a new container reference. Failing to reassign could cause file access issues.

→ **Mitigation:** Careful code review and explicit variable reassignment at each step.

**[Risk] Temporary file cleanup**
`/tmp/kcl-output.yaml` is created but not explicitly deleted.

→ **Mitigation:** This is acceptable since the container is ephemeral. The file will be discarded when the container exits.

**[Risk] Performance impact from separate executions**
Two separate `with_exec()` calls instead of one piped command may have slight overhead.

→ **Mitigation:** The overhead is negligible compared to the value of improved error visibility. No user-facing performance degradation expected.

**[Risk] Error message length**
Including full KCL output in errors could produce very long messages.

→ **Mitigation:** Truncation at 1000 characters with ellipsis indicator.

## Migration Plan

No migration needed. This is a backward-compatible bug fix:

1. Deploy the updated Dagger module
2. Existing calls to `generate_unifi_config()` and `generate_cloudflare_config()` continue to work unchanged
3. Users benefit from improved error messages immediately on next failure

## Open Questions

None. The implementation approach is clear from the prompt file requirements.
