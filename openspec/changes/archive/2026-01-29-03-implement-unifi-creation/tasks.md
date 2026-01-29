# Tasks: Implement Real UniFi Resource Creation

## Overview

This task list tracks the implementation of real UniFi DNS record creation in the `test_integration` function's Phase 3.

---

## Implementation Tasks

### Task 1: Create Terraform Container for UniFi
- [x] Create container from `hashicorp/terraform:{terraform_version}` image
- [x] Mount UniFi DNS Terraform module from `source.directory("terraform/modules/unifi-dns")` to `/module`
- [x] Create directory with UniFi JSON config and mount to `/workspace`
- [x] Verify container setup matches `deploy_unifi()` pattern

**Validation:** Container can access module files and config JSON

---

### Task 2: Configure Environment Variables
- [x] Set `TF_VAR_unifi_url` from function parameter
- [x] Set `TF_VAR_api_url` (use `api_url` if provided, else `unifi_url`)
- [x] Set `TF_VAR_config_file` to `/workspace/unifi.json`
- [x] Verify all required variables are set before Terraform execution

**Validation:** Environment variables visible in container

---

### Task 3: Configure Authentication Secrets
- [x] Check if `unifi_api_key` is provided (Secret type)
- [x] If API key: set `TF_VAR_unifi_api_key` as secret variable
- [x] If username/password: set `TF_VAR_unifi_username` and `TF_VAR_unifi_password` as secrets
- [x] Ensure only one authentication method is used

**Validation:** Secrets are passed securely (not logged)

---

### Task 4: Execute Terraform Init
- [x] Set working directory to `/module`
- [x] Execute `terraform init` command
- [x] Capture stdout for reporting
- [x] Catch `dagger.ExecError` and report failure
- [x] On failure: raise exception to trigger cleanup phase

**Validation:** Terraform initializes successfully or error is caught

---

### Task 5: Execute Terraform Apply
- [x] Execute `terraform apply -auto-approve` command
- [x] Capture stdout for reporting
- [x] On success:
  - [x] Append success message to `report_lines`
  - [x] Set `validation_results["unifi_dns"] = "created"`
- [x] On failure (`dagger.ExecError`):
  - [x] Append error message to `report_lines`
  - [x] Set `validation_results["unifi_error"] = str(e)`
  - [x] Raise exception to trigger cleanup phase

**Validation:** DNS records are created or error is properly reported

---

### Task 6: Update Report Lines
- [x] Replace simulated message with actual execution results
- [x] Include Terraform output summary in success case
- [x] Ensure error messages are descriptive

**Current code (lines 1023-1026):**
```python
# This would normally run Terraform for UniFi module
report_lines.append(f"  ✓ Created UniFi DNS record: {test_id}.local")
validation_results["unifi_dns"] = "created"
```

**Expected:** Real Terraform execution with output

---

### Task 7: Add Expected Failure Documentation
- [x] Add comment explaining that UniFi may fail
- [x] Document that test MAC (`aa:bb:cc:dd:ee:ff`) won't exist in real controllers
- [x] Note this is expected behavior for integration testing

**Comment location:** Before Phase 3 execution block

---

## Testing Tasks

### Task 8: Test with API Key Authentication
- [ ] Run integration test with `--unifi-api-key`
- [ ] Verify Terraform init succeeds
- [ ] Verify secrets are passed correctly
- [ ] Document results

---

### Task 9: Test with Username/Password Authentication
- [ ] Run integration test with `--unifi-username` and `--unifi-password`
- [ ] Verify Terraform init succeeds
- [ ] Verify secrets are passed correctly
- [ ] Document results

---

### Task 10: Test Error Handling
- [ ] Test with invalid credentials
- [ ] Verify error is caught and reported
- [ ] Verify cleanup phase is triggered
- [ ] Verify `validation_results` contains error details

---

## Documentation Tasks

### Task 11: Update Function Docstring (if needed)
- [x] Review `test_integration` docstring for accuracy
- [x] Update examples if Phase 3 behavior changed significantly
- [x] Document expected UniFi failure mode

---

## Completion Criteria

- [x] All implementation tasks completed
- [ ] All testing tasks completed
- [ ] Error handling verified
- [ ] Code review completed
- [ ] Proposal validated with `openspec validate 03-implement-unifi-creation --strict`

---

## Notes

- **Reference Implementation:** `deploy_unifi()` function (lines 113-220)
- **Target Location:** Phase 3 in `test_integration` (lines 1019-1026)
- **Module Path:** `terraform/modules/unifi-dns/`
- **Expected MAC Issue:** Test MAC `aa:bb:cc:dd:ee:ff` won't exist in real UniFi controllers
