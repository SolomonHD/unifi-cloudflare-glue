## Why

The current `is_internal_domain` lambda in `kcl/schemas/cloudflare.k` validates `local_service_url` against a hardcoded list of internal domain suffixes (`.internal.lan`, `.local`, `.home`, `.home.arpa`, `.localdomain`). This restriction prevents users from using real domains locally or custom internal domain schemes, limiting flexibility for diverse network configurations.

## What Changes

- Replace `is_internal_domain` lambda with `is_valid_domain` that validates RFC 1123 domain syntax instead of specific suffixes
- Update the check block in `TunnelService` schema to use the new validation function
- Update error messages to reflect syntax validation rather than suffix matching
- Update docstrings and comments to reflect new behavior
- Add test cases for domain syntax validation in `test_validation.k`

## Capabilities

### New Capabilities

- `domain-syntax-validation`: Validates domain names according to RFC 1123 rules (valid hostname characters, label structure, TLD minimum length) instead of hardcoded suffix matching

### Modified Capabilities

- `kcl-validation-rules`: The DNS loop prevention requirement changes from validating internal domain suffixes to validating domain syntax. The rationale shifts from "must use internal domains" to "must use well-formed domain names" - users are responsible for ensuring their domains resolve correctly.

## Impact

**Code Changes:**
- `kcl/schemas/cloudflare.k`: Replace `is_internal_domain` lambda with `is_valid_domain`, update check block and error messages
- `kcl/test_validation.k`: Add test cases for domain syntax validation (valid domains, invalid syntax, edge cases)

**Documentation Updates:**
- `kcl/schemas/cloudflare.k` docstrings: Update to reflect new validation behavior
- `kcl/README.md`: May need updates if it references internal domain suffix requirements

**Breaking Changes:**
- None - all previously valid configurations (using `.internal.lan`, `.local`, etc.) will continue to pass validation since they are syntactically valid domains
- New capability: Users can now use any valid domain format (e.g., `jellyfin.mycompany.com`) in `local_service_url`
