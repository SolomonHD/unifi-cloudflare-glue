# OpenSpec Prompts Index: Critical Bug Fixes

This index contains prompts for fixing two critical bugs discovered during integration testing that prevent proper resource cleanup and create malformed DNS records.

## Overview

Both issues are production bugs that affect the reliability of the integration test suite and potentially production deployments:

1. **State File Mounting Bug**: Prevents Terraform from destroying test resources, leaving orphaned infrastructure
2. **UniFi FQDN Bug**: Creates incomplete DNS records without domain suffixes

## Prompt Order and Dependencies

### Recommended Execution Order

Execute prompts in the following order:

1. **[01-fix-state-mount-bug.md](01-fix-state-mount-bug.md)** - Critical infrastructure cleanup fix
2. **[02-fix-unifi-fqdn.md](02-fix-unifi-fqdn.md)** - DNS record correctness fix

### Why This Order?

- **01 first**: Ensures test cleanup works properly, preventing resource accumulation during development and testing
- **02 second**: Ensures created records have correct format from the start

These prompts are **independent** and can be executed in parallel if needed, as they modify different files and systems.

## Prompt Summaries

### 01-fix-state-mount-bug.md

**Severity**: 🔴 Critical  
**Impact**: Resource cleanup failure  
**Files Modified**: [`src/main/main.py`](../src/main/main.py)  
**Lines Affected**: ~1368-1371 (Cloudflare), ~1457-1460 (UniFi)

**Problem**: 
State files are correctly exported after resource creation, but during cleanup, the code mounts the state directory with `.with_directory("/module", cloudflare_state_dir)`, which **overwrites** the entire `/module` directory containing Terraform module files. When Terraform `destroy` runs, it has the state file but no module files, causing destruction to fail.

**Fix**:
- Mount state **file** (not directory) at `/module/terraform.tfstate` using `.with_file()`
- Preserve the Terraform module files already mounted at `/module`
- Add logging to confirm state-based destroy is being used

**Validation**:
After fix, running `test_integration` should:
- Successfully destroy all Cloudflare tunnels and DNS records
- Successfully destroy all UniFi DNS records
- Show "✓ Cloudflare state file mounted for state-based destroy" in logs
- Leave no orphaned test resources in either system

---

### 02-fix-unifi-fqdn.md

**Severity**: 🟡 High  
**Impact**: Malformed DNS records  
**Files Modified**: [`terraform/modules/unifi-dns/main.tf`](../terraform/modules/unifi-dns/main.tf)  
**Lines Affected**: Line 132

**Problem**:
The UniFi DNS A-record resource only uses `hostname` (e.g., "test-14fqf") instead of concatenating it with the `domain` field to create a full FQDN (e.g., "test-14fqf.sghd.io"). This creates incomplete DNS records visible in the UniFi controller UI.

**Fix**:
- Change line 132 from: `name = each.value.hostname`
- To: `name = "${each.value.hostname}.${each.value.domain}"`
- Matches the pattern already used for CNAME records on line 178

**Validation**:
After fix, running `test_integration` should:
- Create UniFi DNS records with full FQDN: "test-XXXXX.example.com"
- Show complete domain names in UniFi controller UI
- Log: "✓ Created UniFi DNS record: test-XXXXX.example.com" (not just "test-XXXXX")

---

## Impact Analysis

### Combined Impact When Both Bugs Exist

1. **Resource Accumulation**: Tests create resources but can't clean them up → orphaned infrastructure
2. **Incorrect DNS**: Created records lack domain suffixes → DNS resolution issues or naming conflicts
3. **Cost**: Orphaned Cloudflare tunnels and DNS records accumulate charges
4. **Manual Cleanup**: Operators must manually delete resources from both Cloudflare and UniFi after each test
5. **CI/CD Impact**: Automated testing pipelines leave debris in production accounts

### Post-Fix State

After implementing both fixes:
- ✅ Integration tests fully clean up after themselves
- ✅ DNS records created with correct FQDN format
- ✅ No manual cleanup required
- ✅ Tests can run repeatedly without resource accumulation
- ✅ Production-ready cleanup behavior

---

## Evidence and Diagnosis

### Issue #1 Evidence (State Mounting)

**Code location**: [`src/main/main.py:1368`](../src/main/main.py:1368)

Current broken code:
```python
if cloudflare_state_dir:
    cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", cloudflare_state_dir)
```

**Root cause**: `.with_directory("/module", cloudflare_state_dir)` replaces the entire `/module` directory instead of adding a file to it.

**Observable symptoms**:
- Terraform destroy operations fail or do nothing
- Orphaned resources visible in Cloudflare dashboard and UniFi controller
- No error messages (silent failure due to missing state)

### Issue #2 Evidence (FQDN)

**Code location**: [`terraform/modules/unifi-dns/main.tf:132`](../terraform/modules/unifi-dns/main.tf:132)

Current broken code:
```terraform
name    = each.value.hostname  # Only "test-14fqf"
```

**Root cause**: Resource only uses `hostname` field, ignoring the `domain` field that's available in the same `local.dns_records` map.

**Observable symptoms**:
- Screenshot shows: Domain Name = "test-14fqf" (missing ".sghd.io")
- Should be: "test-14fqf.sghd.io"
- CNAME records work correctly (line 178 uses full FQDN)

---

## Testing Strategy

### Pre-Fix Validation

Confirm both bugs exist:
```bash
# Run integration test
dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

# Observe:
# 1. Cleanup phase shows warnings or errors
# 2. Check Cloudflare dashboard - see orphaned "tunnel-test-XXXXX"
# 3. Check UniFi DNS - see "test-XXXXX" (not "test-XXXXX.example.com")
```

### Post-Fix Validation

After implementing both fixes:
```bash
# Run same test
dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY

# Verify:
# 1. Phase 5 logs: "✓ Cloudflare state file mounted for state-based destroy"
# 2. Phase 5 logs: "✓ UniFi state file mounted for state-based destroy"
# 3. Phase 5 logs: "✓ Destroyed tunnel: tunnel-test-XXXXX"
# 4. Phase 5 logs: "✓ Deleted DNS record: test-XXXXX.example.com"
# 5. Phase 5 logs: "✓ Deleted UniFi DNS record: test-XXXXX.example.com"
# 6. Check Cloudflare dashboard - no orphaned resources
# 7. Check UniFi DNS - no orphaned records
# 8. Run test again - should work identically (idempotent)
```

---

## Related Documentation

- **Existing Proposals**: There are already proposal directories for these issues, but they may contain incomplete or incorrect implementations:
  - [`openspec/changes/preserve-terraform-state/`](../changes/preserve-terraform-state/)
  - [`openspec/changes/fix-test-config-domain/`](../changes/fix-test-config-domain/)
  
- **Root Specifications**:
  - [`openspec/specs/cleanup/spec.md`](../specs/cleanup/spec.md) - Cleanup phase requirements
  - [`openspec/specs/integration-testing/spec.md`](../specs/integration-testing/spec.md) - Integration test spec
  - [`openspec/specs/dagger-module/spec.md`](../specs/dagger-module/spec.md) - Dagger module spec

---

## Handoff Process

### For OpenSpec Workflow Users

If using the standard OpenSpec proposal workflow:

1. Process **01-fix-state-mount-bug.md**:
   ```bash
   # The workflow will automatically detect 01-fix-state-mount-bug.md as NEXT.md
   # Generate proposal
   # Review and approve
   # Implement changes
   ```

2. Process **02-fix-unifi-fqdn.md**:
   ```bash
   # After 01 is complete, workflow moves to 02-fix-unifi-fqdn.md
   # Generate proposal
   # Review and approve
   # Implement changes
   ```

### For Manual Implementation

If implementing directly:

1. Read prompt 01, make changes to [`src/main/main.py`](../src/main/main.py)
2. Read prompt 02, make changes to [`terraform/modules/unifi-dns/main.tf`](../terraform/modules/unifi-dns/main.tf)
3. Run validation tests
4. Commit changes with references to both prompts

---

## Quick Reference

| Prompt | File | Lines | Change Type | Risk |
|--------|------|-------|-------------|------|
| 01 | [`src/main/main.py`](../src/main/main.py) | 1368-1371 | Container mount logic | Low - surgical fix |
| 01 | [`src/main/main.py`](../src/main/main.py) | 1457-1460 | Container mount logic | Low - surgical fix |
| 02 | [`terraform/modules/unifi-dns/main.tf`](../terraform/modules/unifi-dns/main.tf) | 132 | String interpolation | Low - one-line change |

**Total Changes**: 3 locations, ~10 lines of code  
**Estimated Implementation Time**: 15-30 minutes  
**Risk Level**: Low (surgical fixes to well-isolated code)  
**Testing Time**: 5-10 minutes (one integration test run)
