## Why

When KCL configuration validation fails, the system returns empty JSON objects that are written to files and consumed by Terraform. This causes cryptic Terraform errors like "This object does not have an attribute named 'devices'" instead of showing the actual KCL validation errors (MAC mismatches, duplicate hostnames, etc.). Users see misleading Terraform failures instead of the root cause validation errors, making debugging difficult and time-consuming.

## What Changes

- **Improve visibility of KCL validation errors**: Make validation failures immediately obvious in CLI output with clear, prominent error messages
- **Enhance error message quality**: Provide actionable guidance on how to fix common validation errors (MAC_CONSISTENCY_ERROR, DUPLICATE_HOSTNAME_ERROR, DUPLICATE_PUBLIC_HOSTNAME_ERROR, DOMAIN_SYNTAX_ERROR)
- **Prevent misleading Terraform errors**: Consider not writing JSON files when validation fails, or write files with error metadata that Terraform can detect
- **Document common validation patterns**: Add documentation for common validation errors and their resolution steps
- **Maintain backward compatibility**: Ensure existing valid configurations continue to work without changes

## Capabilities

### New Capabilities
- `validation-error-output`: Clear, prominent output of validation errors with actionable guidance
- `validation-error-prevention`: Preventing write of empty/invalid JSON files that cause misleading Terraform errors

### Modified Capabilities
- `kcl-validation-rules`: Enhanced error messages for existing validation rules with resolution guidance

## Impact

**Affected Code:**
- [`main.k`](../../main.k): Modify [`generate()`](../../main.k:238), [`build_error_result()`](../../main.k:227), or add error output handling
- Validation functions: [`validate_all()`](../../main.k:188-195) and related validators
- Potentially generators: [`generators/unifi.k`](../../generators/unifi.k) and [`generators/cloudflare.k`](../../generators/cloudflare.k)
- Dagger module: Python code in [`src/`](../../src/) that consumes KCL output

**User Experience:**
- Users will immediately see validation errors instead of cryptic Terraform failures
- Error messages will guide users to fixes rather than requiring investigation

**Documentation:**
- New/updated documentation on validation error handling and common fixes
- Updated examples demonstrating proper error handling
