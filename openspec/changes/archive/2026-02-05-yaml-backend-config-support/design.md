## Context

The Dagger module currently mounts backend configuration files directly to the Terraform container as `.hcl` files. Users working with secret management tools like `vals` prefer YAML for its native integration, but must manually convert YAML to HCL before using the module. This creates friction in CI/CD pipelines where secret injection happens at runtime.

**Current state:**
- All Dagger module functions (`deploy`, `plan`, `destroy`, `get_tunnel_secrets`) accept `backend_config_file` parameter
- Files are mounted at `/root/.terraform/backend.hcl` and passed to `terraform init -backend-config=...`
- Only HCL format is supported

**Stakeholders:**
- Terraform backend users requiring remote state management
- DevOps engineers using vals for secret injection
- CI/CD pipeline maintainers

## Goals / Non-Goals

**Goals:**
- Accept YAML backend config files transparently without API changes
- Convert YAML to Terraform-compatible HCL syntax with proper type handling
- Maintain 100% backward compatibility with existing HCL files
- Enable direct vals integration without intermediate conversion steps

**Non-Goals:**
- Supporting YAML-specific features (anchors, tags, multi-document files)
- Validating backend config against specific backend requirements (S3, Azure, GCS)
- Automatically running vals or other secret resolution tools
- Changing the parameter name or function signatures

## Decisions

### Decision 1: Content-based format detection vs file extension

**Chosen:** Content-based detection (attempt YAML parse, fall back to HCL)

**Rationale:**
- File extensions can be misleading (`.yaml`, `.yml`, `.hcl`, `.tfbackend`, or none)
- YAML parsing is fast and deterministic
- Graceful degradation ensures backward compatibility

**Alternatives considered:**
- File extension detection: Brittle, users might use `.tfbackend` or no extension
- Additional parameter flag: Adds API complexity, breaks simplicity goal

### Decision 2: Where to perform conversion

**Chosen:** In-memory conversion before container mounting

**Approach:**
- Add private `_process_backend_config(backend_config_file: dagger.File) -> tuple[str, str]` method
- Returns `(content, extension)` tuple where content is HCL and extension is `.tfbackend`
- Create temporary file with converted content using `dag.directory().with_new_file()`

**Rationale:**
- Keeps container layer simple (just receives HCL)
- Conversion happens once per function call, not per terraform command
- Easier to test and debug

**Alternatives considered:**
- In-container conversion: Requires additional dependencies in Terraform container, complicates troubleshooting
- Pre-mount conversion with intermediate file: Unnecessary complexity, same result

### Decision 3: YAML parsing library

**Chosen:** Python's standard `pyyaml` library

**Rationale:**
- Well-tested, mature, widely-used
- Part of Python ecosystem, easy dependency management
- Handles all common YAML structures

**Alternatives considered:**
- `ruamel.yaml`: More features but overkill for this use case
- `strictyaml`: Too restrictive, might reject valid configs

### Decision 4: HCL generation strategy

**Chosen:** Recursive type-based conversion with custom formatting

**Algorithm:**
```python
def _yaml_to_hcl_value(value):
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        return f'[{", ".join(_yaml_to_hcl_value(item) for item in value)}]'
    elif isinstance(value, dict):
        items = [f'{k} = {_yaml_to_hcl_value(v)}' for k, v in value.items()]
        return f'{{{", ".join(items)}}}'
```

**Rationale:**
- Simple, readable, maintainable
- Handles all Terraform backend config types
- Produces clean, aligned output

**Alternatives considered:**
- Using HCL generation library: No mature Python HCL generator exists for Terraform 1.x
- Template-based approach: Too rigid, doesn't handle dynamic structures

### Decision 5: Error handling strategy

**Chosen:** Graceful degradation with clear messaging

**Behavior:**
1. Attempt YAML parse
2. If YAML parse fails → treat as HCL (no error)
3. If both fail → terraform init will error with diagnostic

**Rationale:**
- Users shouldn't see errors for valid HCL files
- Terraform provides better backend config validation than custom checks
- Simplifies implementation

### Decision 6: Function signature changes

**Chosen:** No changes to function signatures or parameter names

**Rationale:**
- Perfect backward compatibility
- Users don't need to know about conversion
- Documentation updates suffice

## Risks / Trade-offs

### Risk: YAML parsing ambiguity
**Description:** YAML might parse successfully but produce unexpected structure

**Mitigation:**
- Document supported YAML patterns with examples
- Add comprehensive test cases covering edge cases
- Users can verify output by checking terraform init logs

### Risk: Type conversion edge cases
**Description:** YAML types might not map cleanly to HCL (e.g., dates, nulls)

**Mitigation:**
- Focus on types used in Terraform backends (strings, numbers, booleans, lists, objects)
- Document unsupported YAML features explicitly
- For unknown types, convert to string with quotes

### Risk: Performance impact
**Description:** YAML parsing adds latency to function calls

**Impact:** Minimal - YAML parsing is fast (<10ms for typical config)

### Risk: Dependency bloat
**Description:** Adding `pyyaml` increases module size

**Impact:** Negligible - `pyyaml` is ~150KB, pure Python

### Trade-off: Not using existing HCL library
**Context:** Could use Python HCL library to generate output

**Decision:** Write custom converter instead

**Rationale:**
- Terraform backend configs use a subset of HCL
- Custom converter is simpler, fewer dependencies
- More control over output formatting

## Open Questions

None - design is straightforward with clear implementation path.
