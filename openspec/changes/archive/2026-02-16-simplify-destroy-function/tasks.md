## 1. Update destroy() Function Signature

- [x] 1.1 Add `unifi_only: bool = False` parameter to `destroy()` function
- [x] 1.2 Add `cloudflare_only: bool = False` parameter to `destroy()` function
- [x] 1.3 Update function docstring to document new parameters

## 2. Implement Flag Validation

- [x] 2.1 Add validation logic to check if both `unifi_only` and `cloudflare_only` are True
- [x] 2.2 Return error message "Cannot use both --unifi-only and --cloudflare-only" when both flags are set
- [x] 2.3 Move credential validation to after flag parsing

## 3. Implement Conditional KCL Config Generation

- [x] 3.1 Create logic to generate only `unifi.json` when `unifi_only=True`
- [x] 3.2 Create logic to generate only `cloudflare.json` when `cloudflare_only=True`
- [x] 3.3 Keep default behavior to generate both files when no flags are set

## 4. Update Terraform Module Usage

- [x] 4.1 Modify `destroy()` to use `terraform/modules/glue/` instead of separate modules
- [x] 4.2 Ensure proper module source path is set for destroy operations
- [x] 4.3 Update Terraform working directory configuration

## 5. Implement Selective Destroy with Terraform Targeting

- [x] 5.1 Add logic to use `-target=module.unifi_dns` when `unifi_only=True`
- [x] 5.2 Add logic to use `-target=module.cloudflare_tunnel` when `cloudflare_only=True`
- [x] 5.3 Ensure default behavior runs destroy without targeting (destroys both)

## 6. Update Credential Validation

- [x] 6.1 Require only UniFi credentials when `unifi_only=True`
- [x] 6.2 Require only Cloudflare credentials when `cloudflare_only=True`
- [x] 6.3 Require both credentials when no selective flags are set

## 7. Implement Status Reporting

- [x] 7.1 Return appropriate message for unifi-only destruction
- [x] 7.2 Return appropriate message for cloudflare-only destruction
- [x] 7.3 Return appropriate message for combined destruction

## 8. Testing

- [ ] 8.1 Test destroy with `--unifi-only` flag
- [ ] 8.2 Test destroy with `--cloudflare-only` flag
- [ ] 8.3 Test destroy with both flags (should error)
- [ ] 8.4 Test default destroy behavior (no flags)
- [ ] 8.5 Verify correct credentials are required for each mode
- [ ] 8.6 Verify proper KCL config generation for each mode

## Implementation Summary

The `destroy()` function has been updated to match the pattern established by `deploy()` and `plan()`:

1. **New Parameters**: Added `unifi_only` and `cloudflare_only` boolean flags (both default to False)
2. **Flag Validation**: Both flags cannot be set simultaneously - returns clear error message
3. **Conditional KCL Generation**: Only generates needed config files based on flags
4. **Combined Module**: Now uses `terraform/modules/glue/` instead of separate modules
5. **Terraform Targeting**: Uses `-target=module.unifi_dns` or `-target=module.cloudflare_tunnel` for selective destruction
6. **Credential Validation**: Only requires credentials for the component(s) being destroyed
7. **Status Reporting**: Returns appropriate messages for each destruction mode

### Usage Examples

```bash
# Destroy only UniFi DNS
dagger call destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only

# Destroy only Cloudflare Tunnels
dagger call destroy \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --cloudflare-only

# Destroy both (default behavior)
dagger call destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --unifi-api-key=env:UNIFI_API_KEY
```

### Testing Checklist

The following testing tasks remain:
- Test each mode with real infrastructure
- Verify error messages for invalid flag combinations
- Confirm proper credential requirements for each mode
- Validate KCL config generation matches selected mode
- Test with different backend configurations (local, remote, persistent state)
