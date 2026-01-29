# Proposal: KCL Generation Functions

## Change ID
`kcl-generation-functions`

## Summary
Implement Dagger functions to generate UniFi and Cloudflare JSON configurations from KCL schemas in a containerized environment. These functions eliminate the need for users to have KCL installed locally by running the KCL toolchain inside Dagger containers.

## Motivation

Currently, users need to have KCL installed locally to generate JSON configurations from the KCL schemas. This creates a barrier to entry and potential version mismatches. By containerizing the KCL toolchain within Dagger functions:

1. **No Local Dependencies**: Users don't need KCL installed
2. **Version Consistency**: Same KCL version used by all team members
3. **CI/CD Ready**: Functions work identically in CI pipelines and locally
4. **Caching**: Dagger's caching optimizes repeated runs

## Scope

### In Scope
- Add `generate_unifi_config` Dagger function
- Add `generate_cloudflare_config` Dagger function
- Create containerized KCL environment using official KCL image
- Support running KCL generators from `kcl/generators/`
- Return generated JSON as Dagger `File` objects for chaining
- Allow configurable KCL version

### Out of Scope
- Terraform deployment functions (prompt 03)
- Integration testing (prompt 04)
- Modifying KCL schemas or generators themselves
- Private Git repository authentication for KCL modules

## Proposed Solution

### Function Design

#### `generate_unifi_config`
```python
@function
async def generate_unifi_config(
    self,
    source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
    kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
) -> dagger.File
```

**Behavior**:
1. Mount source directory into KCL container
2. Run `kcl run generators/unifi.k` in working directory
3. Capture JSON output
4. Return as `dagger.File` for export or chaining

#### `generate_cloudflare_config`
```python
@function
async def generate_cloudflare_config(
    self,
    source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
    kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
) -> dagger.File
```

**Behavior**:
1. Mount source directory into KCL container
2. Run `kcl run generators/cloudflare.k` in working directory
3. Capture JSON output
4. Return as `dagger.File` for export or chaining

### Container Architecture

**Base Image**: `kcllang/kcl:{kcl_version}` (official KCL image)

**Container Setup**:
1. Pull specified KCL version (or `latest`)
2. Mount source directory at `/src`
3. Set working directory to `/src`
4. Execute KCL generator
5. Capture stdout as file

**Caching Strategy**:
- Container image cached by version
- Source directory caching via Dagger's directory hashing
- No caching of generator output (always fresh)

### Error Handling

Both functions will handle:
- Missing `kcl.mod` file (invalid KCL module)
- KCL syntax errors (report stderr)
- Generator file not found
- Invalid JSON output

Error messages should include:
- Clear indication of what failed
- KCL stderr output for debugging
- Suggested fixes

## Dependencies

- **Depends On**: Dagger module scaffolding (existing `src/main/main.py`)
- **Uses**: KCL generators at `kcl/generators/unifi.k` and `kcl/generators/cloudflare.k`
- **Blocks**: Terraform deployment functions (prompt 03)

## Success Criteria

- [ ] `generate_unifi_config` function exists and is callable
- [ ] `generate_cloudflare_config` function exists and is callable
- [ ] Both functions return valid `dagger.File` objects
- [ ] Generated JSON matches expected Terraform module input schemas
- [ ] `dagger functions` shows both new functions
- [ ] Example usage works:
  ```bash
  dagger call generate-unifi-config --source=./kcl export --path=./unifi.json
  dagger call generate-cloudflare-config --source=./kcl export --path=./cloudflare.json
  ```
- [ ] Functions handle errors gracefully with descriptive messages

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| KCL image availability | Low | Use official `kcllang/kcl` with fallback version |
| Large source directories | Medium | Use Dagger's efficient directory syncing |
| KCL module dependency issues | Medium | Mount source as-is; let KCL handle deps |
| Generator output changes | Low | Functions pass through output; schema changes handled elsewhere |

## Related Documents

- Prompt: [`02-kcl-generation-functions.md`](../../prompts/02-kcl-generation-functions.md)
- KCL UniFi Generator: [`kcl/generators/unifi.k`](../../kcl/generators/unifi.k)
- KCL Cloudflare Generator: [`kcl/generators/cloudflare.k`](../../kcl/generators/cloudflare.k)
- Dagger Module: [`src/main/main.py`](../../src/main/main.py)
- OpenSpec Project: [`openspec/project.md`](../project.md)
