# Tasks: Fix Test Config Generation

## Overview

Implementation tasks for replacing KCL-based test config generation with direct JSON generation that matches Terraform module variable structures.

## Task List

### Phase 1: Method Signature Update

- [x] **Task 1.1**: Rename method from `_generate_test_kcl_config()` to `_generate_test_configs()`
  - Update method name in `src/main/main.py` line 710
  - Update the call site in `test_integration()` (line 888)

- [x] **Task 1.2**: Update method signature to accept `cloudflare_account_id` parameter
  - Add `cloudflare_account_id: str` parameter
  - This is needed for the Cloudflare config JSON

- [x] **Task 1.3**: Update return type annotation to `dict`
  - Change return type from `str` to `dict`
  - Dict should contain "cloudflare" and "unifi" keys

### Phase 2: Cloudflare JSON Generation

- [x] **Task 2.1**: Create Cloudflare config structure matching `variables.tf`
  - `zone_name`: Use `cloudflare_zone` parameter
  - `account_id`: Use `cloudflare_account_id` parameter
  - `tunnels`: Map keyed by MAC address

- [x] **Task 2.2**: Create tunnel entry structure
  - `tunnel_name`: Format as `f"tunnel-{test_id}"`
  - `mac_address`: Use fake MAC address (e.g., `aa:bb:cc:dd:ee:ff`)
  - `services`: List with single service entry

- [x] **Task 2.3**: Create service entry structure
  - `public_hostname`: Format as `f"{test_id}.{cloudflare_zone}"`
  - `local_service_url`: Use fake internal URL (e.g., `http://192.168.1.100:8080`)
  - `no_tls_verify`: Set to `false`

- [x] **Task 2.4**: Generate Cloudflare JSON string
  - Use `json.dumps()` with proper indentation
  - Store in result dict under "cloudflare" key

### Phase 3: UniFi JSON Generation

- [x] **Task 3.1**: Create UniFi config structure matching `variables.tf`
  - `devices`: List with single device entry
  - `default_domain`: Set to `"local"`
  - `site`: Set to `"default"`

- [x] **Task 3.2**: Create device entry structure
  - `friendly_hostname`: Use `test_id` value
  - `domain`: Set to `"local"`
  - `nics`: List with single NIC entry

- [x] **Task 3.3**: Create NIC entry structure
  - `mac_address`: Use same fake MAC as Cloudflare config
  - `nic_name`: Set to `"eth0"`

- [x] **Task 3.4**: Generate UniFi JSON string
  - Use `json.dumps()` with proper indentation
  - Store in result dict under "unifi" key

### Phase 4: Documentation and Validation

- [x] **Task 4.1**: Update method docstring
  - Describe new return format (dict with "cloudflare" and "unifi" keys)
  - Document parameter purposes
  - Include example return value

- [x] **Task 4.2**: Verify JSON structure against Terraform variables
  - Compare Cloudflare JSON to `terraform/modules/cloudflare-tunnel/variables.tf`
  - Compare UniFi JSON to `terraform/modules/unifi-dns/variables.tf`
  - Ensure all required fields are present

- [x] **Task 4.3**: Validate MAC address format
  - Ensure format matches regex: `^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$|^[0-9a-fA-F]{12}$`
  - Use lowercase colon format (`aa:bb:cc:dd:ee:ff`)

### Phase 5: Integration

- [x] **Task 5.1**: Update `test_integration` call site
  - Update call at line 888 to pass `cloudflare_account_id`
  - Update to handle dict return value
  - Store results for later use (will be used by future prompts)

- [x] **Task 5.2**: Test method returns valid JSON
  - Verify `json.loads()` works on both config strings
  - Verify structure matches expected Terraform variables

## Dependencies Between Tasks

```
Task 1.1 ─┬─> Task 2.1 ──> Task 2.2 ──> Task 2.3 ──> Task 2.4 ─┐
          │                                                    ├─> Task 4.2 ──> Task 5.1
          ├─> Task 3.1 ──> Task 3.2 ──> Task 3.3 ──> Task 3.4 ─┘
          │
          └─> Task 1.2 ──> Task 1.3 ──> Task 4.1 ──> Task 4.3
```

## Definition of Done

- [x] All tasks completed
- [x] Method renamed and signature updated
- [x] Both Cloudflare and UniFi JSON configs generated correctly
- [x] JSON structures validated against Terraform variables
- [x] Docstring updated with clear return format documentation
- [ ] `openspec validate 01-fix-test-config-generation` passes

## Future Work (Out of Scope)

The following will be addressed in subsequent prompts:

- Using the generated configs to actually create resources (Prompt 02, 03)
- Validating created resources via API calls (Prompt 04)
- Implementing real cleanup via terraform destroy (Prompt 05)
