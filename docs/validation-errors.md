# Validation Error Handling

This guide explains how validation errors work in the unifi-cloudflare-glue KCL module and how to troubleshoot common validation failures.

## Overview

The module performs comprehensive cross-provider validation to catch configuration errors before they cause Terraform failures. When validation fails, you'll see clear, actionable error messages that explain what went wrong and how to fix it.

## Validation Functions

### `generate_with_output()`

The recommended way to generate configurations with validation:

```kcl
import .main

# Your configuration
config = main.UnifiedConfig {
    unifi = {...}
    cloudflare = {...}
}

# Generate with validation and error output
result = main.generate_with_output(config)
```

**Behavior:**
- ✓ **When valid**: Prints "✓ VALIDATION PASSED" and returns `GenerateResult` with JSON
- ✗ **When invalid**: Prints formatted errors and returns `GenerateResult` with empty JSON

### `validate_only()`

Run validation without generating configuration (useful for CI/CD):

```kcl
validation_result = main.validate_only(config)
# Returns: {valid: bool, error_count: int, errors: [{str:str}]}
```

## Validation Error Types

### 1. MAC_CONSISTENCY_ERROR

**What it means:** A Cloudflare tunnel references a MAC address that doesn't exist in your UniFi devices.

**Example error:**
```
✗ MAC_CONSISTENCY_ERROR
  Message: Cloudflare tunnels reference MAC addresses not found in UniFi devices
  Missing MACs: [zz:yy:xx:ww:vv:99]
  Available UniFi MACs: [aa:bb:cc:dd:ee:01, aa:bb:cc:dd:ee:02]
  Suggestion: Add UniFi devices with these MAC addresses or update tunnel configurations
```

**How to fix:**
1. Check if you have the correct MAC address for your device
2. Add a `UniFiEntity` with an endpoint matching the MAC address
3. Or update the Cloudflare tunnel to use a MAC that exists in UniFi

**Example:**
```kcl
# ✗ WRONG - MAC mismatch
unifi = {
    devices = [
        {friendly_hostname = "server", endpoints = [{mac_address = "aa:bb:cc:dd:ee:01"}]}
    ]
}
cloudflare = {
    tunnels = {
        "zz:yy:xx:ww:vv:99": {mac_address = "zz:yy:xx:ww:vv:99", ...}  # This MAC doesn't exist!
    }
}

# ✓ CORRECT - MACs match
cloudflare = {
    tunnels = {
        "aa:bb:cc:dd:ee:01": {mac_address = "aa:bb:cc:dd:ee:01", ...}  # MAC exists in UniFi
    }
}
```

### 2. DUPLICATE_HOSTNAME_ERROR

**What it means:** Multiple UniFi devices have the same `friendly_hostname`.

**Example error:**
```
✗ DUPLICATE_HOSTNAME_ERROR
  Message: Duplicate friendly_hostnames found across devices
  Duplicate Hostnames: [media-server]
  Conflicts: [media-server: [media-server, media-server]]
  Suggestion: Use unique friendly_hostnames for each device
```

**How to fix:**
Ensure each device has a unique `friendly_hostname`:

```kcl
# ✗ WRONG - Duplicate hostnames
devices = [
    {friendly_hostname = "server", ...}
    {friendly_hostname = "server", ...}  # Duplicate!
]

# ✓ CORRECT - Unique hostnames
devices = [
    {friendly_hostname = "media-server", ...}
    {friendly_hostname = "nas-server", ...}
]
```

### 3. DUPLICATE_PUBLIC_HOSTNAME_ERROR

**What it means:** Multiple Cloudflare tunnel services use the same `public_hostname`.

**Example error:**
```
✗ DUPLICATE_PUBLIC_HOSTNAME_ERROR
  Message: Duplicate public_hostnames found across tunnel services
  Duplicate Public Hostnames: [app.example.com]
  Conflicts: [app.example.com: [tunnel1, tunnel2]]
  Suggestion: Use unique public_hostnames for each tunnel service
```

**How to fix:**
Ensure each service has a unique public-facing hostname:

```kcl
# ✗ WRONG - Duplicate public hostnames
tunnels = {
    "mac1": {
        services = [{public_hostname = "app.example.com", ...}]
    }
    "mac2": {
        services = [{public_hostname = "app.example.com", ...}]  # Duplicate!
    }
}

# ✓ CORRECT - Unique public hostnames
tunnels = {
    "mac1": {
        services = [{public_hostname = "app1.example.com", ...}]
    }
    "mac2": {
        services = [{public_hostname = "app2.example.com", ...}]
    }
}
```

### 4. DOMAIN_SYNTAX_ERROR

**What it means:** A `local_service_url` uses invalid domain syntax (not RFC 1123 compliant).

**Note:** This is typically caught at schema validation time, not cross-validation.

**Example error (schema level):**
```
Check failed on the condition: local_service_url has invalid domain syntax
```

**How to fix:**
Use proper domain format with TLD:

```kcl
# ✗ WRONG - No TLD
local_service_url = "http://localhost:8080"

# ✓ CORRECT - Proper domain
local_service_url = "http://myservice.internal.lan:8080"
local_service_url = "http://myservice.local:8080"
local_service_url = "https://myservice.example.com:443"
```

## Validation in CI/CD Pipelines

### Pre-Deployment Checks

Use `validate_only()` to check configurations before deployment:

```bash
#! /bin/bash
# validate-config.sh

# Run validation
kcl run -o json main.k > validation_result.json

# Check if validation passed
if jq -e '.valid == false' validation_result.json > /dev/null; then
    echo "✗ Configuration validation failed"
    jq '.errors' validation_result.json
    exit 1
fi

echo "✓ Configuration is valid"
```

### GitHub Actions Example

```yaml
name: Validate Configuration

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install KCL
        run: |
          curl -fsSL https://kcl-lang.io/script/install.sh | /bin/bash
      
      - name: Validate Configuration
        run: |
          cd your-config-dir
          kcl run main.k
```

## Troubleshooting Tips

### 1. Configuration isn't generating JSON

**Symptom:** Running `kcl run main.k` produces error messages but no JSON output.

**Cause:** Validation failed, so JSON was not generated.

**Solution:** Read the error messages and fix the validation issues.

### 2. Terraform fails with "attribute named 'devices' not found"

**Symptom:** Terraform errors about missing attributes in JSON files.

**Cause:** Empty JSON files were created because validation failed in an older implementation.

**Solution:** 
1. Delete the empty JSON files
2. Fix validation errors in your KCL configuration
3. Regenerate with `kcl run main.k`

### 3. Want to see what would be generated

**Symptom:** Need to see generated JSON even when validation fails (for debugging).

**Solution:** Use the `generate()` function directly instead of `generate_with_output()`:

```kcl
# This will return JSON even if validation fails
result = main.generate(config)

# Check validation status
# result.valid == True/False
# result.errors == list of errors
```

## Best Practices

1. **Always validate before deploying**
   - Run `kcl run main.k` locally before committing
   - Add validation to CI/CD pipelines

2. **Use descriptive hostnames**
   - Makes it easier to spot duplicates
   - Helps with troubleshooting

3. **Keep MACs organized**
   - Use consistent MAC address format (colon-separated)
   - Document which MAC corresponds to which physical device

4. **Test validation with invalid configs**
   - Verify you see clear error messages
   - Helps you understand what the validation catches

## Getting Help

If you encounter validation errors you don't understand:

1. Read the error message carefully - it includes suggestions
2. Check this documentation for your error type
3. Review the examples in `examples/` directory
4. See the [Troubleshooting Guide](troubleshooting.md) for common issues
5. If issues persist, check [GitHub Issues](https://github.com/SolomonHD/unifi-cloudflare-glue/issues)
