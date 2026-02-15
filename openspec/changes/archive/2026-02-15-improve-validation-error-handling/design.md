## Context

Currently, the [`generate()` function in `main.k`](../../main.k:238) handles validation failures by returning a [`GenerateResult`](../../main.k:202) with empty JSON objects (`{}`). The KCL execution completes successfully, these empty objects are written to `unifi.json` and `cloudflare.json` files, and Terraform subsequently fails with cryptic errors like "This object does not have an attribute named 'devices'".

The validation framework is already comprehensive - [`validate_all()`](../../main.k:188-195) runs four validators:
- [`validate_mac_consistency()`](../../main.k:96) - Ensures Cloudflare tunnel MACs exist in UniFi devices
- [`validate_hostname_uniqueness()`](../../main.k:123) - Ensures friendly_hostnames are unique
- [`validate_public_hostname_uniqueness()`](../../main.k:152) - Ensures public_hostnames are unique across tunnels
- [`validate_domain_syntax()`](../../main.k:174) - Ensures local_service_url values use valid RFC 1123 domains

Each validator returns detailed error dictionaries with `error`, `message`, `violations`, and `suggestion` fields. However, these errors are embedded in the [`GenerateResult.errors`](../../main.k:214) field and not prominently surfaced to users.

The Dagger module functions may consume this `GenerateResult` output, but currently they cannot detect validation failures because the KCL process exits successfully (exit code 0) even when validation fails.

## Goals / Non-Goals

**Goals:**
- Make validation errors immediately visible in CLI output with clear visual indicators
- Prevent empty JSON files from being written when validation fails
- Enhance error messages with actionable resolution guidance for all four validation types
- Ensure Dagger functions can detect validation failures
- Provide a validation-only mode for pre-deployment checks
- Maintain backward compatibility with existing valid configurations

**Non-Goals:**
- Changing the validation logic or rules themselves
- Modifying the Terraform modules or providers
- Adding new validation rules (this is purely about error visibility and handling)
- Changing the KCL schema definitions (UnifiedConfig, CloudflareConfig, UniFiConfig)

## Decisions

### Decision 1: Output Validation Errors to KCL Stdout/Stderr

**Choice**: Add explicit error output to [`main.k`](../../main.k) that prints validation errors prominently when [`validate_all()`](../../main.k:188) finds errors.

**Rationale**: 
- KCL supports print() and other output mechanisms
- Error output will be visible in both local development and Dagger container execution
- Users get immediate feedback without needing to parse JSON structures
- This approach works regardless of how the KCL is invoked

**Alternatives Considered**:
- **Python-side error handling**: Modify Dagger module to parse `GenerateResult.errors` - but this misses local KCL runs and adds complexity
- **KCL exit codes**: Use assertions to fail KCL execution - but this loses the detailed error information

**Implementation**:
- Add a helper function `format_validation_errors()` that takes the errors array and produces human-readable output
- Call this function in [`generate()`](../../main.k:238) before returning [`build_error_result()`](../../main.k:227)
- Use Unicode symbols (✗) for visual prominence
- Include all error details: category, message, specific violations, and suggestions

### Decision 2: Conditionally Write JSON Files Based on Validation

**Choice**: Modify the KCL output logic to NOT output JSON to stdout when validation fails, or output a minimal error indicator structure.

**Rationale**:
- Prevents Terraform from receiving empty `{}` objects
- Forces explicit handling of validation failures
- The `GenerateResult` structure already indicates validation state via the `valid` field

**Alternatives Considered**:
- **Write error metadata JSON**: Output JSON with `{"validation_failed": true, "errors": [...]}` - but this still requires downstream tooling changes
- **Write partial JSON**: Output incomplete JSON - but this could cause unpredictable behavior
- **Keep writing empty JSON**: Current behavior - rejected because it causes the original problem

**Implementation**:
- In KCL, only output JSON when `result.valid == True`
- When `result.valid == False`, output error messages only (no JSON)
- Dagger or shell script checks for presence of expected JSON files before proceeding to Terraform

### Decision 3: Enhance Validation Error Messages

**Choice**: Expand each validator function to include more specific details in error messages, following a consistent structure.

**Rationale**:
- The error dict structure (`error`, `message`, `violations`, `suggestion`) is already good
- Need to ensure each field has actionable content
- Users should not need to look at code to understand what went wrong

**Alternatives Considered**:
- **External error documentation**: Document errors separately - but users won't see it during failure
- **Error codes only**: Minimal error output - rejected as not user-friendly

**Implementation**:
- Update [`validate_mac_consistency()`](../../main.k:96) to show available MACs clearly
- Update [`validate_hostname_uniqueness()`](../../main.k:123) and [`validate_public_hostname_uniqueness()`](../../main.k:152) to list conflicting devices/services
- Update [`validate_domain_syntax()`](../../main.k:174) to show valid domain examples
- Ensure all `suggestion` fields provide concrete next steps

### Decision 4: Add Validation-Only Mode

**Choice**: Add a new function `validate_only()` that runs validation and returns results without generating JSON.

**Rationale**:
- Enables pre-deployment validation checks in CI/CD
- Allows users to test configurations without full generation
- Lightweight operation for quick feedback loops

**Alternatives Considered**:
- **Flag to generate()**: Add a `validate_only` parameter - but this complicates the function signature
- **No validation-only mode**: Force full generation every time - less flexible for CI

**Implementation**:
- Create `validate_only = lambda cfg: UnifiedConfig -> {str:any}` function
- Return validation summary: `{valid: bool, error_count: int, errors: [{str:str}]}`
- Users can call this separately before running full generation

### Decision 5: Dagger Module Integration

**Choice**: Update Dagger Python functions to check for validation errors by inspecting KCL output or checking for JSON file presence.

**Rationale**:
- Dagger is the primary interface for automated workflows
- Need to ensure Dagger pipelines fail fast on validation errors
- Should not proceed to Terraform when validation fails

**Implementation**:
- After running KCL, check if expected JSON files were created
- If files are missing, parse KCL stderr/stdout for validation error messages
- Return error string from Dagger function to halt the pipeline
- Ensure exit codes reflect validation failure

## Risks / Trade-offs

**[Risk: Breaking change for automated pipelines]** → Mitigation: Only affects invalid configurations; valid configs behave identically. Add migration guide showing how to detect validation failures programmatically.

**[Risk: Large error output in CI logs]** → Mitigation: Format errors concisely while maintaining clarity. Limit redundant information.

**[Risk: Users miss error output]** → Mitigation: Use visual markers (✗), clear headers ("VALIDATION FAILED"), and ensure output appears at end of execution.

**[Risk: KCL print() output interferes with JSON parsing]** → Mitigation: Only print errors when NOT outputting JSON. If validation fails, output errors only; if validation passes, output JSON only.

**[Trade-off: More complex KCL code]** → Accepted: Error formatting adds lines but significantly improves UX.

**[Trade-off: Dagger module needs updates]** → Accepted: Necessary for pipeline integration, but changes are localized to error handling logic.

## Migration Plan

1. **Phase 1: KCL Changes**
   - Add `format_validation_errors()` function to [`main.k`](../../main.k)
   - Modify [`generate()`](../../main.k:238) to call formatter and output errors
   - Conditional JSON output based on `result.valid`
   - Add `validate_only()` function

2. **Phase 2: Testing**
   - Create test configurations with each validation error type
   - Verify error messages are clear and actionable
   - Test that valid configurations still work unchanged
   - Verify JSON is not output when validation fails

3. **Phase 3: Dagger Integration**
   - Update Dagger Python functions to check JSON file presence
   - Capture and surface KCL error output
   - Test in containerized environment

4. **Phase 4: Documentation**
   - Document new validation error format
   - Add examples of common errors and fixes
   - Update examples to show proper error handling

**Rollback Strategy**:
- If issues arise, revert [`main.k`](../../main.k) changes
- Original behavior: validation errors in GenerateResult but empty JSON still written
- No Terraform schema changes, so rollback is safe

## Open Questions

- Should we colorize error output for terminal display? (Not critical, can be added later)
- Should `validate_only()` mode be a separate script or integrated into existing workflow? (Leaning toward separate function)
- Should we add structured JSON error output as an option for machine consumption? (Defer to future improvement)
