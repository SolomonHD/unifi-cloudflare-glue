# Fix yq Parsing Bug in KCL Configuration Generation

## Problem Statement

The `generate_unifi_config` and `generate_cloudflare_config` functions in `src/main/main.py` fail when attempting to convert KCL YAML output to JSON using yq. The current command syntax causes a YAML parsing error.

### Error Message
```
Error: bad file '-': yaml: line 2: mapping values are not allowed in this context
Hint: Check your KCL syntax with 'kcl run generators/unifi.k' locally.
```

### Affected Functions
- `generate_unifi_config` (line 142)
- `generate_cloudflare_config` (line 1678)

### Current Broken Code
```python
# Line 142 - generate_unifi_config
"kcl run generators/unifi.k | yq -o=json '.result'"

# Line 1678 - generate_cloudflare_config  
"kcl run generators/cloudflare.k | yq -o=json '.result'"
```

## Root Cause

1. KCL outputs YAML format by default
2. The yq syntax `-o=json '.result'` attempts to extract the `.result` key while converting to JSON in one operation
3. When piping YAML from KCL to yq, the combination of parsing YAML from stdin while simultaneously filtering with `.result` creates a parsing conflict

## Proposed Solution

Change the yq command to use explicit `eval` syntax and properly handle the YAML-to-JSON conversion:

```python
# Fixed version for both functions
"kcl run generators/unifi.k | yq eval -o=json '.'"
"kcl run generators/cloudflare.k | yq eval -o=json '.'"
```

## Acceptance Criteria

- [ ] `generate_unifi_config` function works without YAML parsing errors
- [ ] `generate_cloudflare_config` function works without YAML parsing errors
- [ ] Both functions successfully convert KCL YAML output to valid JSON
- [ ] Generated JSON files are valid and can be used by Terraform modules

## Out of Scope

- Changes to KCL schema or generator logic
- Changes to Terraform modules
- Changes to other Dagger functions (deploy, plan, destroy)

## Related

- Bug report in OPENSPEC_PROMPT.md at repository root
- Affects unifi-cloudflare-glue v0.7.1
