# Generator Output Validation Tests Design

## Overview

This document describes the design for comprehensive validation tests of KCL generator output. The goal is to ensure that the output from [`generators/unifi.k`](../../generators/unifi.k) and [`generators/cloudflare.k`](../../generators/cloudflare.k) matches the expectations of the Terraform modules in [`terraform/modules/`](../../terraform/modules/).

## Testing Strategy

### Test Architecture

The validation tests follow a layered approach:

1. **Static Structure Validation**: Verify the JSON output has all required fields with correct types
2. **Content Validation**: Verify field values are valid (e.g., MAC address format)
3. **Edge Case Handling**: Verify generators handle empty arrays, null values, etc.
4. **Integration Validation**: Verify output matches Terraform module variable schemas

### Test Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Test Execution Flow                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Run KCL Generator                                       │
│     └─> Execute `kcl run generators/unifi.k`               │
│     └─> Capture JSON output                                 │
│                                                             │
│  2. Parse JSON Output                                       │
│     └─> Validate JSON is well-formed                        │
│     └─> Convert to Python dict for validation               │
│                                                             │
│  3. Structure Validation                                    │
│     └─> Check required top-level fields exist               │
│     └─> Verify field types (array, string, object)          │
│                                                             │
│  4. Content Validation                                      │
│     └─> Validate MAC address format                         │
│     └─> Validate hostname format                            │
│     └─> Check URL format for service endpoints              │
│                                                             │
│  5. Edge Case Testing                                       │
│     └─> Empty arrays                                        │
│     └─> Null/optional fields                                │
│     └─> Special characters in names                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Test Fixtures

### Sample Configurations

The tests use sample KCL configurations that exercise different scenarios:

1. **Minimal Config**: Single device, single NIC, single service
2. **Full Config**: Multiple devices, multiple NICs, mixed service distributions
3. **Empty Config**: No devices (edge case)
4. **No Services Config**: Devices with no services attached

### Fixture Structure

```python
# pytest fixture pattern
@pytest.fixture
def sample_unifi_output():
    """Load sample UniFi generator output for testing."""
    # Run KCL generator in test mode
    result = subprocess.run(
        ["kcl", "run", "generators/unifi.k"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

## Validation Rules

### UniFi Generator Validation

#### Required Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `devices` | array | List of device configurations |
| `default_domain` | string | Default domain for DNS entries |
| `site` | string | UniFi controller site identifier |

#### Device Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `friendly_hostname` | string | Yes | Human-readable device name |
| `domain` | string | Yes | DNS domain for device |
| `service_cnames` | array[string] | Yes | CNAME records from services |
| `nics` | array | Yes | Network interfaces |

#### NIC Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mac_address` | string | Yes | Normalized MAC (aa:bb:cc:dd:ee:ff) |
| `nic_name` | string/null | No | Optional interface name |
| `service_cnames` | array[string] | Yes | CNAMEs for this NIC |

### Cloudflare Generator Validation

#### Required Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `zone_name` | string | Cloudflare DNS zone name |
| `account_id` | string | Cloudflare account identifier |
| `tunnels` | object | Map of MAC -> tunnel config |

#### Tunnel Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tunnel_name` | string | Yes | Human-readable tunnel name |
| `mac_address` | string | Yes | Normalized MAC address |
| `services` | array | Yes | List of tunnel services |

#### Service Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `public_hostname` | string | Yes | Public DNS hostname |
| `local_service_url` | string | Yes | Internal service URL |
| `no_tls_verify` | bool/null | No | Skip TLS verification |

## Error Message Format

Validation errors follow a consistent format:

```
✗ Generator Output Validation Failed

Field:      devices[0].nics[0].mac_address
Expected:   string matching pattern "^[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}$"
Found:      "AA-BB-CC-DD-EE-FF" (wrong format: uppercase with dashes)
Hint:       MAC addresses should be normalized to lowercase colon format (aa:bb:cc:dd:ee:ff)
```

## Test Organization

### File Structure

```
tests/unit/test_generator_output.py
├── TestUniFiGeneratorOutput
│   ├── test_has_required_top_level_fields
│   ├── test_device_structure
│   ├── test_nic_structure
│   ├── test_mac_normalization
│   └── test_edge_cases
├── TestCloudflareGeneratorOutput
│   ├── test_has_required_top_level_fields
│   ├── test_tunnel_structure
│   ├── test_service_structure
│   └── test_edge_cases
└── TestValidationErrors
    ├── test_missing_field_message
    ├── test_type_mismatch_message
    └── test_mac_format_message
```

## Implementation Notes

### Running KCL from Python

The tests will execute KCL generators using subprocess to get actual JSON output:

```python
def run_kcl_generator(generator_name: str) -> dict:
    """Run a KCL generator and return parsed JSON output."""
    result = subprocess.run(
        ["kcl", "run", f"generators/{generator_name}.k"],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout)
```

### Schema Validation

Consider using `jsonschema` for structured validation:

```python
from jsonschema import validate, ValidationError

UNIFI_SCHEMA = {
    "type": "object",
    "required": ["devices", "default_domain", "site"],
    "properties": {
        "devices": {"type": "array"},
        "default_domain": {"type": "string"},
        "site": {"type": "string"}
    }
}

def validate_unifi_output(output: dict) -> None:
    validate(instance=output, schema=UNIFI_SCHEMA)
```

### Test Isolation

Each test should be independent and not rely on state from other tests. Use fresh KCL runs for each test case.

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Run Generator Validation Tests
  run: pytest tests/unit/test_generator_output.py -v
  working-directory: ${{ github.workspace }}
```

### Pre-commit Hook

Optional: Add a pre-commit hook to run generator validation before commits:

```yaml
- repo: local
  hooks:
    - id: generator-validation
      name: Generator Output Validation
      entry: pytest tests/unit/test_generator_output.py -q
      language: system
      pass_filenames: false
      always_run: true
```

## Future Enhancements

1. **Snapshot Testing**: Compare generator output against known-good snapshots
2. **Property-Based Testing**: Use Hypothesis to generate random valid configs
3. **Terraform Plan Testing**: Run actual Terraform plan to verify module compatibility
4. **Performance Testing**: Measure generator execution time for large configurations
