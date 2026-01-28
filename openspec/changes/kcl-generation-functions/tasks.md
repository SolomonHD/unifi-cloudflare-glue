# Tasks: KCL Generation Functions

## Implementation Checklist

### Phase 1: Function Implementation

- [ ] **Task 1.1**: Add `generate_unifi_config` function to `UnifiCloudflareGlue` class
  - [ ] Define function signature with `source` and `kcl_version` parameters
  - [ ] Create container from `kcllang/kcl` image
  - [ ] Mount source directory
  - [ ] Execute `kcl run generators/unifi.k`
  - [ ] Capture and return JSON as `dagger.File`
  - [ ] Add comprehensive docstring
  - [ ] Use `Annotated[type, Doc(...)]` for parameters

- [ ] **Task 1.2**: Add `generate_cloudflare_config` function to `UnifiCloudflareGlue` class
  - [ ] Define function signature with `source` and `kcl_version` parameters
  - [ ] Create container from `kcllang/kcl` image
  - [ ] Mount source directory
  - [ ] Execute `kcl run generators/cloudflare.k`
  - [ ] Capture and return JSON as `dagger.File`
  - [ ] Add comprehensive docstring
  - [ ] Use `Annotated[type, Doc(...)]` for parameters

### Phase 2: Error Handling

- [ ] **Task 2.1**: Implement error handling for missing `kcl.mod`
  - [ ] Check for `kcl.mod` existence before running
  - [ ] Return descriptive error if missing

- [ ] **Task 2.2**: Implement error handling for KCL syntax errors
  - [ ] Capture stderr from KCL execution
  - [ ] Include stderr in error message

- [ ] **Task 2.3**: Implement error handling for generator file not found
  - [ ] Check if generator file exists
  - [ ] Return helpful error with available generators

- [ ] **Task 2.4**: Implement error handling for invalid JSON output
  - [ ] Validate output is valid JSON
  - [ ] Return error if parsing fails

### Phase 3: Testing & Validation

- [ ] **Task 3.1**: Verify `dagger functions` shows new functions
  - [ ] Run `dagger functions` and confirm both functions appear
  - [ ] Verify function signatures match specification

- [ ] **Task 3.2**: Test `generate_unifi_config` with sample data
  - [ ] Use example from `examples/homelab-media-stack/`
  - [ ] Verify output is valid JSON
  - [ ] Verify JSON matches UniFi Terraform module schema

- [ ] **Task 3.3**: Test `generate_cloudflare_config` with sample data
  - [ ] Use example from `examples/homelab-media-stack/`
  - [ ] Verify output is valid JSON
  - [ ] Verify JSON matches Cloudflare Terraform module schema

- [ ] **Task 3.4**: Test error scenarios
  - [ ] Test with invalid source directory
  - [ ] Test with missing `kcl.mod`
  - [ ] Test with invalid KCL syntax

### Phase 4: Documentation

- [ ] **Task 4.1**: Update function docstrings with examples
  - [ ] Add usage example in `generate_unifi_config` docstring
  - [ ] Add usage example in `generate_cloudflare_config` docstring

- [ ] **Task 4.2**: Verify README.md references new functions
  - [ ] Check if README needs updating
  - [ ] Add examples if missing

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
