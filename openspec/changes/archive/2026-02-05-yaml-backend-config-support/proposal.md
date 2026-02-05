## Why

Terraform backend configuration currently requires HCL format files (`.hcl`), making it cumbersome to integrate with modern secret management tools like `vals` which natively work with YAML. Users must either convert YAML to HCL manually or use complex templating workarounds, creating friction in automated deployment pipelines.

## What Changes

- Add automatic YAML-to-Terraform-backend-config conversion in the Dagger module
- Implement content-based format detection (YAML vs HCL)
- Convert YAML structures to Terraform `.tfbackend` HCL syntax with proper type handling
- Maintain backward compatibility with existing HCL files
- Update function docstrings with YAML usage examples
- Add comprehensive test coverage for YAML backend configs

## Capabilities

### New Capabilities
- `yaml-backend-config-parsing`: Parse YAML backend configuration files and convert to Terraform-compatible HCL format, supporting strings, numbers, booleans, lists, and nested objects with proper type preservation

### Modified Capabilities
- `dagger-module`: Extends existing Dagger module functions (`deploy`, `plan`, `destroy`, `get_tunnel_secrets`) to accept YAML backend config files through the `--backend-config-file` parameter while maintaining HCL backward compatibility

## Impact

**Code Changes:**
- `src/main/main.py`: Add `_process_backend_config()` private method, update all backend-using functions
- `pyproject.toml`: Add `pyyaml` dependency

**API Impact:**
- No breaking changes - existing HCL files continue to work unchanged
- Parameter name `--backend-config-file` remains the same
- Automatic format detection makes it transparent to users

**Dependencies:**
- Add Python `pyyaml` library for YAML parsing

**User Impact:**
- Positive: Enables seamless vals integration without manual format conversion
- Positive: Simplifies secret injection workflows
- No negative impact: Backward compatible with existing HCL configs
