## Context

The `kcl/schemas/cloudflare.k` file contains a lambda function `is_internal_domain` that validates `local_service_url` values in `TunnelService` schemas. Currently, this function checks if the hostname ends with one of five hardcoded suffixes: `.internal.lan`, `.local`, `.home`, `.home.arpa`, or `.localdomain`.

This approach has limitations:
- Users cannot use real domains for local resolution (e.g., split-horizon DNS scenarios)
- Custom internal domain schemes are rejected
- The validation is based on convention rather than correctness

The proposed change replaces suffix matching with RFC 1123 domain syntax validation.

## Goals / Non-Goals

**Goals:**
- Implement `is_valid_domain` lambda that validates domain syntax per RFC 1123
- Support any valid domain format in `local_service_url`
- Maintain backward compatibility with existing configurations
- Provide clear error messages for invalid domain syntax

**Non-Goals:**
- DNS resolution or reachability checks
- Validating URL protocol (http/https already handled elsewhere)
- Validating port numbers (already handled by URL parsing)
- Changing any other schemas or validation logic

## Decisions

### Decision 1: Validation Approach

**Chosen:** Pure syntax validation using KCL string operations

**Alternatives considered:**
1. **Regex matching** - KCL has limited regex support; string operations are more portable
2. **External validation** - Would add complexity and break offline validation

**Rationale:** KCL string operations (`split`, `len`, string slicing, `in` operator) are sufficient for RFC 1123 validation without requiring regex or external dependencies.

### Decision 2: Validation Rules

**Chosen:** Implement RFC 1123 hostname validation with these rules:
- Valid characters: alphanumeric, hyphens, dots
- No consecutive dots
- No leading/trailing dots
- Each label: 1-63 characters
- Labels must start and end with alphanumeric
- TLD: minimum 2 characters
- At least one dot separator required

**Rationale:** These rules align with DNS standards and catch common typos while allowing flexibility in domain choice.

### Decision 3: Function Naming

**Chosen:** Rename `is_internal_domain` to `is_valid_domain`

**Rationale:** The new name accurately reflects the validation purpose. The old name implied checking for "internal" domains, which is no longer the intent.

### Decision 4: Error Message Strategy

**Chosen:** Specific error messages indicating what failed

**Example:** `"local_service_url has invalid domain syntax: label cannot start with hyphen"`

**Rationale:** Helps users quickly identify and fix configuration errors.

## Risks / Trade-offs

### Risk: Users may configure unresolvable domains
**Mitigation:** Documentation should clarify that users are responsible for DNS resolution. The validation ensures syntax only, not semantic correctness.

### Risk: Breaking change perception
**Mitigation:** This is not a breaking change - all previously valid configurations continue to work. The change expands valid inputs rather than restricting them.

### Risk: KCL string operation limitations
**Mitigation:** The validation logic uses basic string operations available in KCL. If edge cases are discovered, the lambda can be extended without breaking existing behavior.

## Implementation Approach

### Step 1: Extract hostname from URL
```kcl
# Remove protocol
without_protocol = url.replace("http://", "").replace("https://", "")
# Split on '/' to get host:port
parts = without_protocol.split("/")
host_part = parts[0] if len(parts) > 0 else without_protocol
# Remove port
host_parts = host_part.split(":")
hostname = host_parts[0] if len(host_parts) > 0 else host_part
```

### Step 2: Validate hostname structure
```kcl
# Check for empty hostname
len(hostname) == 0 -> False

# Check for invalid characters
# Check for leading/trailing dots
# Check for consecutive dots
# Check each label
# Check TLD length
```

### Step 3: Update schema check block
Replace the current check:
```kcl
is_internal_domain(local_service_url), \
"local_service_url must use an internal domain..."
```

With:
```kcl
is_valid_domain(local_service_url), \
"local_service_url has invalid domain syntax"
```

## Migration Plan

No migration required. This is a non-breaking change:
1. Deploy the updated `cloudflare.k` schema
2. Existing configurations continue to validate successfully
3. Users can optionally adopt new domain formats

## Open Questions

None. The scope is well-defined and the implementation approach is straightforward.
