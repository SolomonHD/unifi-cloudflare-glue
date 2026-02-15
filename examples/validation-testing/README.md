# Validation Testing Example

This example demonstrates the validation error handling workflow in unifi-cloudflare-glue. It shows how validation errors are caught, what they look like, and how to fix them.

## Overview

The unifi-cloudflare-glue module includes comprehensive validation to catch configuration errors before they reach Terraform. This example demonstrates:

1. **Validation-Only Mode**: Test configurations without generating JSON
2. **Error Detection**: See how MAC consistency errors are caught
3. **Error Messages**: Understand the structured error output
4. **Fixing Errors**: Learn how to resolve validation failures

## Validation Types

The module performs four types of cross-provider validation:

| Validation | Description | Error Code |
|------------|-------------|------------|
| MAC Consistency | Ensures Cloudflare tunnel MACs exist in UniFi | `MAC_CONSISTENCY_ERROR` |
| Hostname Uniqueness | Ensures device hostnames are unique | `DUPLICATE_HOSTNAME_ERROR` |
| Public Hostname Uniqueness | Ensures public hostnames are unique | `DUPLICATE_PUBLIC_HOSTNAME_ERROR` |
| Domain Syntax | Ensures local_service_url uses valid domains | `DOMAIN_SYNTAX_ERROR` |

## Quick Start

### Prerequisites

```bash
# Install KCL
brew install kcl-lang/tap/kcl

# Install the example dependencies
cd examples/validation-testing
kcl mod add unifi_cloudflare_glue --git https://github.com/SolomonHD/unifi-cloudflare-glue --tag v0.4.0
```

### Running the Example

```bash
# Run validation tests
kcl run main.k

# See detailed error output
kcl run test_mac_error.k
```

## Example Scenarios

### Scenario 1: MAC Consistency Error

**Problem**: Cloudflare tunnel references a MAC address not in UniFi.

```kcl
# UniFi device has this MAC
mac_address = "aa:bb:cc:dd:ee:01"

# But Cloudflare tunnel uses a different MAC
mac_address = "aa:bb:cc:dd:ee:99"  # ERROR: Not in UniFi!
```

**Error Output**:
```
✗ VALIDATION FAILED

Found 1 validation error(s):

✗ MAC_CONSISTENCY_ERROR
  Message: Cloudflare tunnels reference MAC addresses not found in UniFi devices
  Missing MACs: [aa:bb:cc:dd:ee:99]
  Available UniFi MACs: [aa:bb:cc:dd:ee:01]
  Suggestion: Add UniFi devices with these MAC addresses or update tunnel configurations
```

**Solution**: Either:
1. Add the missing MAC to UniFi devices, or
2. Update the Cloudflare tunnel to use an existing MAC

### Scenario 2: Duplicate Hostname Error

**Problem**: Two devices have the same friendly_hostname.

```kcl
devices = [
    { friendly_hostname = "server" },  # Duplicate!
    { friendly_hostname = "server" },  # Duplicate!
]
```

**Error Output**:
```
✗ DUPLICATE_HOSTNAME_ERROR
  Message: Duplicate friendly_hostnames found across devices
  Duplicate Hostnames: [server]
  Suggestion: Use unique friendly_hostnames for each device
```

**Solution**: Use unique hostnames for each device.

### Scenario 3: Duplicate Public Hostname Error

**Problem**: Two services share the same public_hostname.

```kcl
services = [
    { public_hostname = "app.example.com" },  # Duplicate!
    { public_hostname = "app.example.com" },  # Duplicate!
]
```

**Error Output**:
```
✗ DUPLICATE_PUBLIC_HOSTNAME_ERROR
  Message: Duplicate public_hostnames found across tunnel services
  Duplicate Public Hostnames: [app.example.com]
  Conflicts: [app.example.com: [tunnel1, tunnel2]]
  Suggestion: Use unique public_hostnames for each tunnel service
```

**Solution**: Use unique public hostnames for each service.

## Validation-Only Mode

Use `validate_only()` to check configurations without generating JSON:

```kcl
import unifi_cloudflare_glue.main as main

# Run validation
result = main.validate_only(config)

# Check results
if not result["valid"]:
    print("Found ${result["error_count"]} errors")
    for error in result["errors"]:
        print(error["message"])
```

## Integration with CI/CD

Use validation-only mode in CI/CD pipelines to catch errors early:

```yaml
# .github/workflows/validate.yml
name: Validate Configuration

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install KCL
        run: |
          curl -sSL https://kcl-lang.io/script/install-cli.sh | bash
      
      - name: Validate KCL Configuration
        run: |
          cd kcl/
          kcl run validate.k
```

## Dagger Integration

The Dagger module automatically detects validation failures:

```bash
# This will fail with a clear error message if validation fails
dagger call generate-unifi-config --source=./kcl export --path=./unifi.json

# Error output in Dagger:
# ✗ KCL validation failed:
# ✗ MAC_CONSISTENCY_ERROR
#   Message: Cloudflare tunnels reference MAC addresses not found in UniFi devices
#   ...
```

## Best Practices

1. **Validate Early**: Run validation before committing configurations
2. **Use validation-only mode**: For quick checks during development
3. **Fix all errors**: Don't ignore validation warnings
4. **Check MAC consistency**: Most common error - ensure MACs match
5. **Use unique names**: Both hostnames and public_hostnames must be unique

## Troubleshooting

### "No JSON output generated"

This means validation failed. Check the error output above the JSON section.

### "KCL validation failed" in Dagger

The configuration has validation errors. Read the error message and fix the issues.

### Empty error array but validation fails

Check that your KCL module version supports the validation functions. Update to the latest version:

```bash
kcl mod update unifi_cloudflare_glue
```

## See Also

- [Validation Errors Documentation](../../docs/validation-errors.md)
- [KCL Guide](../../docs/kcl-guide.md)
- [Troubleshooting Guide](../../docs/troubleshooting.md)
