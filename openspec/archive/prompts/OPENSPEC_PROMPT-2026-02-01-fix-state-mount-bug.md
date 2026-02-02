# OpenSpec Prompt: Fix State File Mounting in Cleanup Phase

## Context

The [`test_integration`](../src/main/main.py:837) function exports Terraform state files after successful resource creation (lines 1131-1136 for Cloudflare, 1205-1210 for UniFi). However, during the cleanup phase (Phase 5), the state files are incorrectly mounted, causing Terraform `destroy` operations to fail.

**Current broken behavior** (lines 1368-1370 and 1457-1459):
```python
if cloudflare_state_dir:
    cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", cloudflare_state_dir)
```

This **overwrites** the entire `/module` directory (which contains the Terraform module files like `main.tf`, `variables.tf`, etc.) with just the state directory. When Terraform runs, it has the state file but no module files, causing destruction to fail.

## Goal

Fix the state file mounting logic to mount the state **file** at `/module/terraform.tfstate` without overwriting the Terraform module files.

## Scope

**In scope:**
- Fix Cloudflare state file mounting logic (around line 1368)
- Fix UniFi state file mounting logic (around line 1457)
- Preserve existing error handling and warning messages
- Maintain backward compatibility with existing state export logic

**Out of scope:**
- Changing state export logic (lines 1131-1136, 1205-1210) - this already works correctly
- Modifying Terraform modules themselves
- Changing the cleanup retry logic for Cloudflare (lines 1393-1430)
- Altering the container creation or module mounting steps

## Desired Behavior

### Cloudflare Cleanup State Mounting

**Before line 1368:**
```python
# Mount the Cloudflare Tunnel Terraform module
try:
    tf_module = source.directory("terraform/modules/cloudflare-tunnel")
    cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
except Exception:
    # fallback logic...
```

**After line 1368 (to fix):**
```python
# Mount preserved state file if available
if cloudflare_state_dir:
    try:
        state_file = cloudflare_state_dir.file("terraform.tfstate")
        cf_cleanup_ctr = cf_cleanup_ctr.with_file("/module/terraform.tfstate", state_file)
        report_lines.append("    ✓ Cloudflare state file mounted for state-based destroy")
    except Exception as e:
        report_lines.append(f"    ⚠ Failed to mount Cloudflare state file: {str(e)}")
        cloudflare_state_dir = None
else:
    report_lines.append("    ⚠ No state file available for Cloudflare cleanup")
```

### UniFi Cleanup State Mounting

**After line 1457 (to fix):**
```python
# Mount preserved state file if available
if unifi_state_dir:
    try:
        state_file = unifi_state_dir.file("terraform.tfstate")
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_file("/module/terraform.tfstate", state_file)
        report_lines.append("    ✓ UniFi state file mounted for state-based destroy")
    except Exception as e:
        report_lines.append(f"    ⚠ Failed to mount UniFi state file: {str(e)}")
        unifi_state_dir = None
else:
    report_lines.append("    ⚠ No state file available for UniFi cleanup")
```

### Key Changes

1. **Extract the file from the directory:** `state_file = cloudflare_state_dir.file("terraform.tfstate")`
2. **Mount as a file, not directory:** `.with_file("/module/terraform.tfstate", state_file)`
3. **Add success log message** to confirm state-based destroy is being used
4. **Wrap in try/except** to handle cases where state file might not be in expected location
5. **Set state_dir to None on error** to trigger the warning path

## Constraints & Assumptions

- The state files are already correctly exported and stored in Dagger Directory objects
- The state files are named `terraform.tfstate` (Terraform default)
- The module files must remain at `/module` (already mounted before state mounting)
- Both Cloudflare and UniFi use the same pattern
- Error handling should be graceful - cleanup should attempt to proceed even if state mounting fails

## Acceptance Criteria

- [ ] Cloudflare state file is mounted at `/module/terraform.tfstate` using `.with_file()` method
- [ ] UniFi state file is mounted at `/module/terraform.tfstate` using `.with_file()` method
- [ ] Module files in `/module` are NOT overwritten by state mounting
- [ ] Success message logged when state file is successfully mounted
- [ ] Warning message logged when state file is unavailable or mount fails
- [ ] Existing warning "⚠ No state file available" still displayed when `state_dir` is None
- [ ] Try/except handles errors during file extraction or mounting
- [ ] `terraform destroy` operations successfully delete resources using the mounted state

## Reference

**Files to modify:**
- [`src/main/main.py`](../src/main/main.py): Lines ~1368-1371 (Cloudflare) and ~1457-1460 (UniFi)

**Testing:**
After the fix, run:
```bash
dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY
```

Expected outcome:
- Phase 5 cleanup should successfully destroy both Cloudflare and UniFi resources
- No orphaned test resources left in either system
- Logs should show "✓ Cloudflare state file mounted for state-based destroy"
- Logs should show "✓ UniFi state file mounted for state-based destroy"
