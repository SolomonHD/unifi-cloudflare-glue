# Tasks: KCL Generation Functions

## Implementation Checklist

### Phase 1: Function Implementation

- [x] **Task 1.1**: Add `generate_unifi_config` function to `UnifiCloudflareGlue` class
  - [x] Define function signature with `source` and `kcl_version` parameters
  - [x] Create container from `kcllang/kcl` image
  - [x] Mount source directory
  - [x] Execute `kcl run generators/unifi.k`
  - [x] Capture and return JSON as `dagger.File`
  - [x] Add comprehensive docstring
  - [x] Use `Annotated[type, Doc(...)]` for parameters

- [x] **Task 1.2**: Add `generate_cloudflare_config` function to `UnifiCloudflareGlue` class
  - [x] Define function signature with `source` and `kcl_version` parameters
  - [x] Create container from `kcllang/kcl` image
  - [x] Mount source directory
  - [x] Execute `kcl run generators/cloudflare.k`
  - [x] Capture and return JSON as `dagger.File`
  - [x] Add comprehensive docstring
  - [x] Use `Annotated[type, Doc(...)]` for parameters

### Phase 2: Error Handling

- [x] **Task 2.1**: Implement error handling for missing `kcl.mod`
  - [x] Check for `kcl.mod` existence before running
  - [x] Return descriptive error if missing

- [x] **Task 2.2**: Implement error handling for KCL syntax errors
  - [x] Capture stderr from KCL execution
  - [x] Include stderr in error message

- [x] **Task 2.3**: Implement error handling for generator file not found
  - [x] Check if generator file exists
  - [x] Return helpful error with available generators

- [x] **Task 2.4**: Implement error handling for invalid JSON output
  - [x] Validate output is valid JSON
  - [x] Return error if parsing fails

### Phase 3: Testing & Validation

- [x] **Task 3.1**: Verify `dagger functions` shows new functions
  - [x] Run `dagger functions` and confirm both functions appear
  - [x] Verify function signatures match specification

- [x] **Task 3.2**: Test `generate_unifi_config` with sample data
  - [x] Use example from `examples/homelab-media-stack/`
  - [x] Verify output is valid JSON
  - [x] Verify JSON matches UniFi Terraform module schema

- [x] **Task 3.3**: Test `generate_cloudflare_config` with sample data
  - [x] Use example from `examples/homelab-media-stack/`
  - [x] Verify output is valid JSON
  - [x] Verify JSON matches Cloudflare Terraform module schema

- [x] **Task 3.4**: Test error scenarios
  - [x] Test with invalid source directory
  - [x] Test with missing `kcl.mod`
  - [x] Test with invalid KCL syntax

### Phase 4: Documentation

- [x] **Task 4.1**: Update function docstrings with examples
  - [x] Add usage example in `generate_unifi_config` docstring
  - [x] Add usage example in `generate_cloudflare_config` docstring

- [x] **Task 4.2**: Verify README.md references new functions
  - [x] Check if README needs updating
  - [x] Add examples if missing

## Dependencies

- Requires existing KCL generators at `kcl/generators/unifi.k` and `kcl/generators/cloudflare.k`
- Requires existing Dagger module scaffolding
- Blocks: Terraform deployment functions (prompt 03)

## Parallelizable Work

- Tasks 1.1 and 1.2 can be done in parallel
- Tasks 2.1 through 2.4 can be done in parallel after Task 1
- Tasks 3.2 and 3.3 can be done in parallel

## Success Criteria Verification

| Criteria | Verification Method |
|----------|---------------------|
| `generate_unifi_config` exists | `dagger functions` output |
| `generate_cloudflare_config` exists | `dagger functions` output |
| Return `dagger.File` | Test export to path |
| Valid JSON output | JSON.parse validation |
| Error handling | Test invalid inputs |
| Example usage works | Run example commands |
