# OpenSpec Prompt: Improve Validation Error Handling

**Change ID**: `improve-validation-error-handling`

## Context

When KCL configuration validation fails, the [`generate()` function in `main.k`](../../main.k:238) returns empty JSON objects `{}` for both `unifi_json` and `cloudflare_json`. These empty objects are then written to files and consumed by Terraform, causing cryptic Terraform errors like:

```
Error: Unsupported attribute
  on main.tf line 31: local.effective_config is object with no attributes
  This object does not have an attribute named "devices".
```

Users see Terraform errors instead of the actual KCL validation errors that caused the problem. This makes debugging difficult because:

1. The real validation errors (MAC mismatches, duplicate hostnames, etc.) are hidden in the KCL output
2. Terraform fails with generic "no attributes" errors that don't indicate the root cause
3. Empty JSON files are still created, making it appear that generation succeeded

Current flow:
```
KCL validation fails → generate() returns {} → write {} to JSON → Terraform reads {} → Terraform fails with "no attributes" error
```

The validation errors are available in `result.errors` but are not prominently surfaced to the user.

## Goal

Improve error handling so that validation failures are immediately obvious and prevent writing invalid JSON files that will cause Terraform to fail.

## Scope

**In Scope:**
- Make validation errors more visible in KCL output
- Consider whether to write partial/empty JSON when validation fails
- Improve error messages to guide users to the root cause
- Document common validation errors and how to fix them

**Out of Scope:**
- Changing the validation logic itself
- Modifying the Terraform modules
- Adding new validation rules

## Desired Behavior

When validation fails, the user should:

1. **Immediately see that validation failed** with clear, prominent error output
2. **Understand what validation errors occurred** without needing to parse nested structures
3. **Get actionable guidance** on how to fix the errors
4. **Not get misleading Terraform errors** from empty JSON files

Possible approaches:

**Option A**: Write validation errors to stderr/output prominently
**Option B**: Don't write JSON files at all when validation fails
**Option C**: Write JSON with error metadata that Terraform can detect
**Option D**: Add a validation-only mode that runs before generation

## Constraints & Assumptions

- Backward compatibility with existing workflows
- KCL may be run in automated pipelines (CI/CD)
- Users may pipe KCL output to `jq` or other tools
- The validation framework in [`main.k`](../../main.k:188-195) is already comprehensive

## Acceptance Criteria

- [ ] Validation failures are immediately obvious in CLI output
- [ ] Error messages clearly explain what went wrong
- [ ] Error messages suggest how to fix the issues
- [ ] Users don't see Terraform "no attributes" errors for validation failures
- [ ] Existing valid configurations continue to work
- [ ] Examples in `examples/*/` demonstrate proper error handling

## Expected Files/Areas Touched

- [`main.k`](../../main.k) - Modify `generate()`, `build_error_result()`, or add error output handling
- Potentially [`generators/unifi.k`](../../generators/unifi.k) and [`generators/cloudflare.k`](../../generators/cloudflare.k)
- Documentation of error handling behavior
- Possibly Dagger integration in [`src/`](../../src/) that consumes the KCL output

## Dependencies

None. This is a standalone improvement.

## Common Validation Errors to Handle Better

Based on [`main.k`](../../main.k:188-195), these validation functions can fail:

1. **MAC_CONSISTENCY_ERROR**: Cloudflare tunnels reference MACs not in UniFi devices
2. **DUPLICATE_HOSTNAME_ERROR**: Multiple devices have the same friendly_hostname
3. **DUPLICATE_PUBLIC_HOSTNAME_ERROR**: Multiple tunnel services use the same public_hostname  
4. **DOMAIN_SYNTAX_ERROR**: Service URLs don't use valid domain syntax
