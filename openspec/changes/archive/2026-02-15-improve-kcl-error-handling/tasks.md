## 1. Refactor generate_unifi_config()

- [x] 1.1 Replace piped KCL+yq execution with separate KCL execution step
- [x] 1.2 Add KCL execution error handling with detailed stdout/stderr capture
- [x] 1.3 Add empty output validation after KCL execution
- [x] 1.4 Write KCL output to temporary file and run yq conversion separately
- [x] 1.5 Add yq conversion error handling with KCL output display (truncated to 1000 chars)
- [x] 1.6 Preserve existing JSON validation step
- [x] 1.7 Ensure container reference is preserved after each operation

## 2. Refactor generate_cloudflare_config()

- [x] 2.1 Replace piped KCL+yq execution with separate KCL execution step
- [x] 2.2 Add KCL execution error handling with detailed stdout/stderr capture
- [x] 2.3 Add empty output validation after KCL execution
- [x] 2.4 Write KCL output to temporary file and run yq conversion separately
- [x] 2.5 Add yq conversion error handling with KCL output display (truncated to 1000 chars)
- [x] 2.6 Preserve existing JSON validation step
- [x] 2.7 Ensure container reference is preserved after each operation

## 3. Validation and Testing

- [x] 3.1 Test with valid KCL config - should produce valid JSON output file
- [x] 3.2 Test with KCL syntax error - should show actual KCL error message
- [x] 3.3 Test with empty KCL output - should show empty output error with causes
- [x] 3.4 Test with invalid YAML from KCL - should show KCL output that failed yq parsing
- [x] 3.5 Test with large KCL output (>1000 chars) that has parsing error - should truncate output
- [x] 3.6 Verify both functions still return valid `dagger.File` objects on success
- [x] 3.7 Verify function signatures and return types remain unchanged

## 4. Documentation

- [x] 4.1 Update CHANGELOG.md with the improvement description
- [x] 4.2 Verify no README updates needed (internal implementation change)
