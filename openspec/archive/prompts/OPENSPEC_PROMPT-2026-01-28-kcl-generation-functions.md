# OpenSpec Change Prompt: KCL Generation Functions

## Context

The Dagger module scaffolding is in place at the repository root. Now we need to implement functions that generate JSON configurations from KCL schemas. These functions will containerize the KCL toolchain so users don't need KCL installed locally.

**Key requirement**: All sensitive inputs must use Dagger's `Secret` type. For KCL generation, this may include private Git credentials if KCL modules are pulled from private repos.

## Goal

Implement Dagger functions to generate UniFi and Cloudflare JSON configurations from KCL schemas in a containerized environment.

## Scope

**In scope:**
- Add `generate_unifi_config` function
- Add `generate_cloudflare_config` function
- Create containerized KCL environment (no local KCL required)
- Support running KCL generators from `kcl/generators/`
- Return generated JSON as Dagger `File` objects
- Allow output directory configuration

**Out of scope:**
- Terraform deployment (next prompt)
- Integration testing (future prompt)
- Modifying KCL schemas themselves

## Desired Behavior

1. **`generate_unifi_config`**:
   - Takes `source` directory (containing KCL configs)
   - Runs `kcl run generators/unifi.k` in container
   - Returns generated JSON as `dagger.File`
   - Optionally exports to specified path

2. **`generate_cloudflare_config`**:
   - Takes `source` directory (containing KCL configs)
   - Runs `kcl run generators/cloudflare.k` in container
   - Returns generated JSON as `dagger.File`
   - Optionally exports to specified path

3. **Container Setup**:
   - Use official KCL image or install KCL in container
   - Mount source directory for KCL configs
   - Cache KCL modules for performance

## Constraints & Assumptions

- KCL generators exist at `kcl/generators/unifi.k` and `kcl/generators/cloudflare.k`
- Source directory contains valid KCL module with `kcl.mod`
- Functions must be async (Dagger best practice)
- Return `dagger.File` for flexibility (can export or chain)
- Use `dagger.Directory` for source input
- No secrets required for public KCL modules (GitHub public repos)

## Acceptance Criteria

- [ ] `generate_unifi_config` function exists:
  - Parameter: `source: dagger.Directory` (required)
  - Parameter: `kcl_version: str` (optional, default "latest")
  - Returns: `dagger.File`
  - Runs in KCL container with proper working directory
  - Successfully generates UniFi JSON from KCL schemas

- [ ] `generate_cloudflare_config` function exists:
  - Parameter: `source: dagger.Directory` (required)
  - Parameter: `kcl_version: str` (optional, default "latest")
  - Returns: `dagger.File`
  - Runs in KCL container with proper working directory
  - Successfully generates Cloudflare JSON from KCL schemas

- [ ] Both functions:
  - Have comprehensive docstrings
  - Use `Annotated[type, Doc("...")]` for parameters
  - Handle errors gracefully (return descriptive error messages)
  - Support caching (don't regenerate if inputs unchanged)

- [ ] `dagger functions` shows both new functions
- [ ] Example usage works:
  ```bash
  dagger call generate-unifi-config --source=. export --path=./unifi.json
  dagger call generate-cloudflare-config --source=. export --path=./cloudflare.json
  ```

## Files to Modify

**Modify:**
- `src/unifi_cloudflare_glue/main.py` - add generation functions

## Dependencies

- Requires change 01 (Dagger module scaffolding) to be complete
- Existing KCL module structure at `kcl/`

## Example Implementation Pattern

```python
@function
async def generate_unifi_config(
    self,
    source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
    kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
) -> dagger.File:
    """Generate UniFi JSON configuration from KCL schemas."""
    # Create container with KCL
    # Mount source directory
    # Run kcl run generators/unifi.k
    # Return output file
```

## Reference

- Existing KCL structure at `unifi-cloudflare-glue/kcl/`
- Dagger Python SDK container APIs
- KCL CLI documentation: https://kcl-lang.io/docs/user_docs/guides/cli/

## Open Questions

None - straightforward implementation following Dagger patterns.
