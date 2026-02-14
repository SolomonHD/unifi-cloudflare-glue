# OpenSpec Change Prompt

## Context

The KCL schema in `kcl/schemas/cloudflare.k` currently validates `local_service_url` in `TunnelService` against a hardcoded list of internal domain suffixes (`.internal.lan`, `.local`, `.home`, `.home.arpa`, `.localdomain`). This restriction prevents users from using real domains locally or custom internal domain schemes.

## Goal

Replace the hardcoded domain suffix validation with general domain syntax validation, allowing any valid domain format while still ensuring the URL is well-formed.

## Scope

**In scope:**
- Modify `is_internal_domain` lambda in `kcl/schemas/cloudflare.k` to validate domain syntax instead of specific suffixes
- Rename function to `is_valid_domain` to reflect new purpose
- Validate domain format (hostname portion of URL):
  - Valid hostname characters (letters, digits, hyphens, dots)
  - At least one dot separator (e.g., `example.com`)
  - Each label follows RFC 1123 (starts/ends with alphanumeric, may contain hyphens)
  - TLD is at least 2 characters
- Update the check block in `TunnelService` schema with new validation
- Update error message to reflect syntax validation
- Update docstrings and comments

**Out of scope:**
- DNS resolution or reachability checks
- Validating URL protocol (http/https already handled elsewhere)
- Validating port numbers (already handled by URL parsing)
- Changing any other schemas or validation logic

## Desired Behavior

### Before (Current)
```kcl
# Only accepts specific suffixes
is_internal_domain("http://jellyfin.internal.lan:8096")  # True
is_internal_domain("http://jellyfin.mycompany.com:8096") # False - rejected!
```

### After (Proposed)
```kcl
# Accepts any valid domain syntax
is_valid_domain("http://jellyfin.internal.lan:8096")  # True
is_valid_domain("http://jellyfin.mycompany.com:8096") # True
is_valid_domain("http://invalid..domain:8096")        # False - syntax error
is_valid_domain("http://-invalid.com:8096")           # False - label starts with hyphen
```

### Validation Rules
- Extract hostname from URL (strip protocol, port, path)
- Validate hostname structure:
  - Contains only alphanumeric, hyphens, and dots
  - No consecutive dots
  - No leading/trailing dots
  - Each label: 1-63 chars, starts/ends with alphanumeric
  - TLD: minimum 2 characters

## Constraints & Assumptions

**Assumptions:**
- Users are responsible for ensuring their domain resolves correctly
- The validation is for syntax only, not semantic correctness
- KCL regex or string operations can implement the validation

**Constraints:**
- Must not break existing valid configurations
- Error messages must clearly indicate what's invalid about the domain
- Keep the lambda function approach for consistency with existing code style

## Acceptance Criteria

- [ ] `is_valid_domain` lambda function implemented in `kcl/schemas/cloudflare.k`
- [ ] Function validates domain syntax per RFC 1123
- [ ] `TunnelService` schema check updated to use new validation
- [ ] Error message updated to indicate syntax validation failure
- [ ] Docstrings updated to reflect new behavior
- [ ] Test file `kcl/test_validation.k` updated with new test cases
- [ ] Test cases cover: valid domains, invalid syntax, edge cases
- [ ] Existing valid configurations continue to pass validation
