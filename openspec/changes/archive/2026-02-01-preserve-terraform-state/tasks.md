## Implementation Tasks

### 1. State Export After Cloudflare Apply
- [x] Initialize `cloudflare_state_dir = None` at the start of `test_integration()` try block
- [x] After successful Cloudflare `terraform apply` (line ~1117), export state file:
  ```python
  try:
      cf_state_file = await cf_ctr.file("/module/terraform.tfstate")
      cloudflare_state_dir = dagger.dag.directory().with_file("terraform.tfstate", cf_state_file)
  except Exception as e:
      report_lines.append(f"  ⚠ Cloudflare state export failed: {str(e)}")
      cloudflare_state_dir = None
  ```

### 2. State Export After UniFi Apply
- [x] Initialize `unifi_state_dir = None` at the start of `test_integration()` try block
- [x] After successful UniFi `terraform apply` (line ~1183), export state file:
  ```python
  try:
      unifi_state_file = await unifi_ctr.file("/module/terraform.tfstate")
      unifi_state_dir = dagger.dag.directory().with_file("terraform.tfstate", unifi_state_file)
  except Exception as e:
      report_lines.append(f"  ⚠ UniFi state export failed: {str(e)}")
      unifi_state_dir = None
  ```

### 3. Mount State During Cloudflare Cleanup
- [x] In the cleanup phase (line ~1328), mount state directory before `terraform init`:
  ```python
  if cloudflare_state_dir:
      cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", cloudflare_state_dir)
  else:
      report_lines.append("    ⚠ No state file available for Cloudflare cleanup")
  ```

### 4. Mount State During UniFi Cleanup
- [x] In the cleanup phase (line ~1411), mount state directory before `terraform init`:
  ```python
  if unifi_state_dir:
      unifi_cleanup_ctr = unifi_cleanup_ctr.with_directory("/module", unifi_state_dir)
  else:
      report_lines.append("    ⚠ No state file available for UniFi cleanup")
  ```

### 5. Validation
- [x] Run `openspec validate preserve-terraform-state --strict` and fix any issues
- [x] Review the modified code to ensure:
  - State variables are in scope for the finally block
  - State export failures don't fail the test
  - Cleanup uses existing retry logic (2 attempts with 5s delay for Cloudflare)
  - Report includes appropriate warnings when state is unavailable

### 6. Testing Considerations
- [x] Document that the fix requires running actual integration tests to validate
- [x] Note that state file behavior can only be verified against real Cloudflare/UniFi APIs
