## 1. KCL Error Formatting Function

- [x] 1.1 Create `format_validation_errors()` helper function in main.k that takes errors array and produces human-readable output
- [x] 1.2 Add Unicode symbol (✗) prefix for visual prominence in error messages
- [x] 1.3 Format each error with category, message, violations, and suggestions in structured layout
- [x] 1.4 Test formatting function with sample errors from each validator type

## 2. Enhanced Validator Error Messages

- [x] 2.1 Update `validate_mac_consistency()` to include available UniFi MACs in error message
- [x] 2.2 Update `validate_hostname_uniqueness()` to clearly list conflicting devices
- [x] 2.3 Update `validate_public_hostname_uniqueness()` to clearly list conflicting tunnels/services
- [x] 2.4 Update `validate_domain_syntax()` to include valid domain format examples (http://service.internal.lan:8080)
- [x] 2.5 Verify all error messages include actionable `suggestion` fields

## 3. Conditional JSON Output in KCL

- [x] 3.1 Modify `generate()` function to call `format_validation_errors()` when validation fails
- [x] 3.2 Implement logic to output formatted errors to stderr/stdout when `result.valid == False`
- [x] 3.3 Implement logic to output JSON only when `result.valid == True`
- [x] 3.4 Add validation success indicator (✓) when validation passes
- [x] 3.5 Test that invalid configs produce error output with no JSON
- [x] 3.6 Test that valid configs produce JSON output with no errors

## 4. Validation-Only Mode

- [x] 4.1 Create `validate_only()` function that runs validation without generation
- [x] 4.2 Return validation summary: `{valid: bool, error_count: int, errors: [{str:str}]}`
- [x] 4.3 Test validation-only mode with both valid and invalid configurations
- [x] 4.4 Document usage of validation-only mode for pre-deployment checks

## 5. Test Configurations

- [x] 5.1 Create test configuration with MAC_CONSISTENCY_ERROR (Cloudflare MAC not in UniFi)
- [x] 5.2 Create test configuration with DUPLICATE_HOSTNAME_ERROR
- [x] 5.3 Create test configuration with DUPLICATE_PUBLIC_HOSTNAME_ERROR
- [x] 5.4 Create test configuration with DOMAIN_SYNTAX_ERROR (invalid local_service_url)
- [x] 5.5 Verify each test produces clear, actionable error messages
- [x] 5.6 Verify valid sample configuration still works unchanged

## 6. Dagger Module Integration

- [x] 6.1 Update Dagger Python functions to check for JSON file presence after KCL execution
- [x] 6.2 Capture KCL stderr/stdout output in Dagger container
- [x] 6.3 Return error string from Dagger function when JSON files are missing
- [x] 6.4 Ensure Dagger functions fail with appropriate exit code on validation failure
- [x] 6.5 Test Dagger pipeline with invalid configuration to verify error detection
- [x] 6.6 Test Dagger pipeline with valid configuration to ensure normal operation

## 7. Documentation

- [x] 7.1 Document validation error format and structure in docs/validation-errors.md
- [x] 7.2 Add examples of each validation error type with resolution steps
- [x] 7.3 Document validation-only mode usage for CI/CD pipelines
- [x] 7.4 Update README with reference to validation error documentation
- [x] 7.5 Add troubleshooting section for common validation failures

## 8. Example Updates

- [x] 8.1 Review examples in examples/*/ to ensure none trigger validation errors
- [x] 8.2 Add example showing proper error handling workflow
- [x] 8.3 Update example READMEs to reference validation documentation

## 9. Integration Testing

- [x] 9.1 Test full workflow: invalid config → validation error → pipeline halts
- [x] 9.2 Test full workflow: valid config → JSON generation → Terraform success
- [x] 9.3 Test validation-only mode in CI/CD context
- [x] 9.4 Verify backward compatibility with existing valid configurations
- [x] 9.5 Test error visibility in containerized Dagger environment
