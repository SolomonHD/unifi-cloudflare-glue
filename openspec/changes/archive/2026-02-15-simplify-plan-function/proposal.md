## Why

The `plan()` function currently requires both UniFi and Cloudflare credentials and always generates plans for both components separately. This is inconsistent with the simplified `deploy()` function that uses the combined Terraform module and supports selective deployment via `--unifi-only` and `--cloudflare-only` flags. Users need the same flexibility in the plan workflow to preview changes for only the components they intend to modify.

## What Changes

- Update `plan()` function to use the combined Terraform module at `terraform/modules/glue/`
- Add `unifi_only: bool = False` parameter for UniFi-only plan generation
- Add `cloudflare_only: bool = False` parameter for Cloudflare-only plan generation
- Add validation to prevent both flags being used simultaneously
- Make Cloudflare credentials optional when `--unifi-only` is set
- Make UniFi credentials optional when `--cloudflare-only` is set
- Generate only needed KCL configurations based on selected components
- Return plan artifacts (tfplan, json, txt, summary) for selected components
- Update plan summary to reflect which components were planned

## Capabilities

### New Capabilities
- `selective-plan-generation`: Support for planning individual components (UniFi-only or Cloudflare-only) using the combined Terraform module with conditional credential requirements and flag validation.

### Modified Capabilities
- None (this is a functional enhancement that doesn't change existing spec requirements)

## Impact

- **Source File**: `src/main/main.py` - `plan()` function (lines 781-1187)
- **Terraform Module**: Uses existing `terraform/modules/glue/` (already created for `deploy()`)
- **CLI Interface**: New `--unifi-only` and `--cloudflare-only` flags for `plan` command
- **Output Directory**: Plan artifacts will be named based on selected components
- **Backward Compatibility**: **BREAKING** - The `plan()` function signature changes; previously required parameters become optional based on flags
