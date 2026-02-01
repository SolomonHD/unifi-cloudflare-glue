# Implementation Tasks: Fix Terraform State Persistence

## 1. State Export Implementation

- [ ] 1.1 Export Cloudflare state after Phase 2 apply
  - After successful `terraform apply` in Phase 2 (line ~1104)
  - Read `/module/terraform.tfstate` using `container.file(path).contents()`
  - Store state in variable `cloudflare_state`
  - Add error handling with warning on failure

- [ ] 1.2 Export UniFi state after Phase 3 apply
  - After successful `terraform apply` in Phase 3 (line ~1171)
  - Read `/module/terraform.tfstate` using `container.file(path).contents()`
  - Store state in variable `unifi_state`
  - Add error handling with warning on failure

## 2. State Import Implementation

- [ ] 2.1 Import Cloudflare state before cleanup destroy
  - Before `terraform init` in Cloudflare cleanup (line ~1349)
  - Write state file to `/module/terraform.tfstate` using `container.with_new_file(path, contents)`
  - Only write if `cloudflare_state` is not empty
  - Add log message indicating state-based cleanup

- [ ] 2.2 Import UniFi state before cleanup destroy
  - Before `terraform init` in UniFi cleanup (line ~1436)
  - Write state file to `/module/terraform.tfstate` using `container.with_new_file(path, contents)`
  - Only write if `unifi_state` is not empty
  - Add log message indicating state-based cleanup

## 3. Error Handling

- [ ] 3.1 Add state export error handling
  - Wrap state export in try/except
  - Log warning if export fails
  - Continue test execution (don't fail on export error)
  - Set state variable to empty string on failure

- [ ] 3.2 Add state import error handling
  - Wrap state import in try/except
  - Log warning if import fails
  - Fall back to config-based destroy
  - Include fallback message in report

## 4. Test Report Updates

- [ ] 4.1 Add state persistence status to report header
  - Add "State Persistence: enabled" to initial test information
  - Only show if state export is attempted

- [ ] 4.2 Update cleanup summary with state status
  - Add state-based vs config-based indicator for each provider
  - Show "State-based: ✓" or "Config-based: ✓" in cleanup summary
  - Include state file size (for debugging)

## 5. Documentation

- [ ] 5.1 Update CHANGELOG.md
  - Add entry under [Unreleased] section
  - Describe bug fix and state persistence feature
  - Reference this change ID

## 6. Validation

- [ ] 6.1 Run openspec validate
  - Validate the change proposal
  - Fix any validation errors

- [ ] 6.2 Code review
  - Review state handling for sensitive data
  - Verify error handling completeness
  - Check backward compatibility
