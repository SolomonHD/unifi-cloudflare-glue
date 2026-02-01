# Implementation Tasks: Fix Terraform State Persistence

## 1. State Export Implementation

- [x] 1.1 Export Cloudflare state after Phase 2 apply
  - After successful `terraform apply` in Phase 2
  - Read `/module/terraform.tfstate` using `container.file(path).contents()`
  - Store state in variable `cloudflare_state`
  - Add error handling with warning on failure

- [x] 1.2 Export UniFi state after Phase 3 apply
  - After successful `terraform apply` in Phase 3
  - Read `/module/terraform.tfstate` using `container.file(path).contents()`
  - Store state in variable `unifi_state`
  - Add error handling with warning on failure

## 2. State Import Implementation

- [x] 2.1 Import Cloudflare state before cleanup destroy
  - Before `terraform init` in Cloudflare cleanup
  - Write state file to `/module/terraform.tfstate` using `container.with_new_file(path, contents)`
  - Only write if `cloudflare_state` is not empty
  - Add log message indicating state-based cleanup

- [x] 2.2 Import UniFi state before cleanup destroy
  - Before `terraform init` in UniFi cleanup
  - Write state file to `/module/terraform.tfstate` using `container.with_new_file(path, contents)`
  - Only write if `unifi_state` is not empty
  - Add log message indicating state-based cleanup

## 3. Error Handling

- [x] 3.1 Add state export error handling
  - Wrap state export in try/except
  - Log warning if export fails
  - Continue test execution (don't fail on export error)
  - Set state variable to empty string on failure

- [x] 3.2 Add state import error handling
  - Wrap state import in try/except
  - Log warning if import fails
  - Fall back to config-based destroy
  - Include fallback message in report

## 4. Test Report Updates

- [x] 4.1 Add state persistence status to report
  - State export shows "✓ Cloudflare state exported (X bytes)"
  - Cleanup summary shows state-based vs config-based method

- [x] 4.2 Update cleanup summary with state status
  - Cleanup summary shows provider status with method (e.g., "success (state-based)")
  - Both Cloudflare and UniFi cleanup methods tracked and reported

## 5. Documentation

- [x] 5.1 Update CHANGELOG.md
  - Added entry under [Unreleased] section
  - Described bug fix and state persistence feature
  - Referenced this change ID

## 6. Validation

- [x] 6.1 Run openspec validate
  - Change validated successfully
  - All requirements have proper text and scenarios

- [x] 6.2 Code review
  - State handling reviewed - state files contain potentially sensitive data but are handled in-memory only
  - Error handling complete - try/except blocks around all state operations
  - Backward compatibility maintained - graceful fallback to config-based cleanup
