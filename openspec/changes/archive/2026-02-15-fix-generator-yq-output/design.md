## Context

Currently, both KCL generator files (`generators/unifi.k` and `generators/cloudflare.k`) output two YAML documents when run directly:
1. `sample_config` - a demonstration configuration used for testing
2. `result` - the generated configuration output

The Dagger module pipes KCL generator output to `yq eval -o=json '.'` to convert YAML to JSON for Terraform consumption. However, `yq eval` cannot parse multi-document YAML from stdin, resulting in the error:
```
Error: bad file '-': yaml: line 2: mapping values are not allowed in this context
```

The fix requires restructuring the generator files to output only a single document (`result`) while preserving the sample configurations in separate test files for standalone validation.

## Goals / Non-Goals

**Goals:**
- Modify `generators/unifi.k` to output only the `result` variable
- Modify `generators/cloudflare.k` to output only the `result` variable
- Create test files that preserve sample configurations for standalone testing
- Ensure Dagger functions can successfully pipe generator output to yq
- Maintain backward compatibility for users importing generators

**Non-Goals:**
- Changes to Dagger Python code
- Changes to KCL schemas
- Changes to the main.k module entry point
- Changes to Terraform modules

## Decisions

### Decision: Move sample_config to test files (not conditional output)

**Rationale:** The simplest and cleanest approach is to move `sample_config` to dedicated test files rather than using conditional logic.

**Alternative considered:** Wrap `sample_config` in a conditional that only outputs when run directly:
```kcl
# This adds complexity and may not work reliably in KCL
if option("exec") == "direct":
    sample_config = ...
```

**Why chosen:** Moving to test files is cleaner, more explicit, and follows the pattern of separating library code from test/demo code. It also makes the sample configurations more discoverable for users wanting to understand generator usage.

### Decision: Test files import generators (not duplicate code)

**Rationale:** Test files should import the generator modules rather than duplicate the transformation logic.

**Example structure for `generators/test_unifi.k`:**
```kcl
# Import the generator
import .unifi

# Define sample config locally
sample_config = unifi.UniFiConfig {
    # ... sample data
}

# Output both for testing
sample_config
result = unifi.generate_unifi_config(sample_config)
```

**Why chosen:** This ensures test files validate the actual generator functions and don't drift from the implementation.

### Decision: Keep generator functions pure

**Rationale:** The generator functions (`generate_unifi_config`, `generate_cloudflare_config`) should remain pure functions that take config as input and return output.

**Why chosen:** This maintains the existing architecture where users can import and use generators with their own configurations.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Users may have been using sample_config from generators | Document the change in CHANGELOG; test files provide the same functionality |
| Test files add maintenance burden | Test files are simple imports; any generator changes automatically apply |
| Breaking change for users running generators directly | This is the intended fix - users should use Dagger functions or import generators |
| Confusion about where sample configs went | Add README documentation pointing to test files |

## Migration Plan

No migration needed for existing users who:
- Import generators in their KCL configs (no change needed)
- Use Dagger functions (will work after fix)

For users who were running generators directly for testing:
- Use new test files: `kcl run generators/test_unifi.k`
- Or use Dagger functions: `dagger call generate-unifi-config --source=./kcl`

## Open Questions

None - the approach is straightforward and well-understood.
