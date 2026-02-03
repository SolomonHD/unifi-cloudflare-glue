# OpenSpec Prompt: Add Tunnel Token Retrieval Guidance to Deployment Functions

## Context

After implementing the [`get_tunnel_secrets()`](../../src/main/main.py:28) function (from prompt 01), users need to know how to retrieve their tunnel credentials after deployment. Currently, the success messages from [`deploy_cloudflare()`](../../src/main/main.py:422-571) and [`deploy()`](../../src/main/main.py:574-742) don't inform users about this critical next step.

Users follow this workflow:
1. Deploy Cloudflare tunnels: `dagger call deploy-cloudflare ...`
2. See success message but no instructions
3. Must figure out independently how to get tunnel tokens
4. Eventually discover `terraform output` or ask for help

The disconnect creates poor user experience - users complete a successful deployment but don't know what to do next to actually configure [`cloudflared`](../../examples/homelab-media-stack/README.md:325) on their devices.

Similar Dagger tools (e.g., GitHub deployment actions) include next-step guidance in their success messages to help users complete their workflows.

## Goal

Update deployment function success messages to include clear, actionable guidance for retrieving tunnel credentials using both Terraform and the new Dagger function.

## Scope

### In Scope

- Modify [`deploy_cloudflare()`](../../src/main/main.py:422-571) success message (around line 563)
- Modify [`deploy()`](../../src/main/main.py:574-742) success message (Phase 3 summary, around lines 725-741)
- Add multi-line formatted guidance including:
  - Brief context ("Next step: configure cloudflared")
  - Terraform command option
  - Dagger command option  
  - Link to example documentation
- Preserve existing success indicators and backend type info
- Update success message tests to expect new guidance

### Out of Scope

- Creating the `get_tunnel_secrets()` function (covered in prompt 01)
- Modifying `plan()`, `destroy()`, or other functions (no secrets in those)
- Adding secrets directly to success messages (security issue)
- Changing error messages
- Modifying `test_integration()` success messages (different context)

## Desired Behavior

### Modified deploy_cloudflare() Success Message

Current behavior (around line 563-569):
```python
result_msg = "✓ Success: Cloudflare Tunnel deployment completed"
if backend_type != "local":
    result_msg += f"\n  Backend: {backend_type}"
elif using_persistent_state:
    result_msg += "\n  State: Persistent local (mounted state directory)"
result_msg += f"\n\n{apply_result}"
return result_msg
```

New behavior:
```python
result_msg = "✓ Success: Cloudflare Tunnel deployment completed"
if backend_type != "local":
    result_msg += f"\n  Backend: {backend_type}"
elif using_persistent_state:
    result_msg += "\n  State: Persistent local (mounted state directory)"

# Add tunnel credential retrieval guidance
result_msg += "\n\n" + "-" * 60
result_msg += "\nNext Step: Retrieve Tunnel Credentials"
result_msg += "\n" + "-" * 60
result_msg += "\n\nTo configure cloudflared on your devices, retrieve the tunnel tokens:"
result_msg += "\n\n1. Using Terraform (if you have terraform installed):"
result_msg += "\n   terraform output -json cloudflare_tunnel_tokens"

# Build Dagger command based on deployment parameters
dagger_cmd = f"   dagger call get-tunnel-secrets \\\n"
dagger_cmd += f"       --source=. \\\n"
dagger_cmd += f"       --cloudflare-token=env:CF_TOKEN \\\n"
dagger_cmd += f"       --cloudflare-account-id={cloudflare_account_id} \\\n"
dagger_cmd += f"       --zone-name={zone_name}"

if backend_type != "local":
    dagger_cmd += f" \\\n       --backend-type={backend_type}"
    if backend_config_file is not None:
        dagger_cmd += f" \\\n       --backend-config-file=./backend.hcl"
elif using_persistent_state:
    dagger_cmd += f" \\\n       --state-dir=./terraform-state"

result_msg += "\n\n2. Using Dagger (recommended):\n"
result_msg += dagger_cmd

result_msg += "\n\n3. Then install cloudflared with the token:"
result_msg += "\n   sudo cloudflared service install <token>"

result_msg += "\n\nSee: examples/homelab-media-stack/README.md for detailed setup\n"
result_msg += "-" * 60

result_msg += f"\n\n{apply_result}"
return result_msg
```

### Modified deploy() Success Message

Current behavior (Phase 3, around lines 725-741):
```python
# Final summary
results.append("")
results.append("=" * 60)
results.append("DEPLOYMENT SUMMARY")
results.append("=" * 60)

if "✓ Success" in unifi_result and "✓ Success" in cloudflare_result:
    results.append("✓ Both deployments completed successfully")
elif "✓ Success" in unifi_result:
    results.append("○ UniFi: Success")
    results.append("✗ Cloudflare: Failed")
else:
    results.append("✗ UniFi: Failed")
    results.append("○ Cloudflare: Not attempted")

return "\n".join(results)
```

New behavior:
```python
# Final summary
results.append("")
results.append("=" * 60)
results.append("DEPLOYMENT SUMMARY")
results.append("=" * 60)

cf_success = "✓ Success" in cloudflare_result
unifi_success = "✓ Success" in unifi_result

if unifi_success and cf_success:
    results.append("✓ Both deployments completed successfully")
    
    # Add tunnel credential guidance only if Cloudflare deployment succeeded
    results.append("")
    results.append("-" * 60)
    results.append("Next Step: Retrieve Tunnel Credentials")
    results.append("-" * 60)
    results.append("")
    results.append("To configure cloudflared on your devices:")
    results.append("")
    
    # Build Dagger command
    dagger_cmd = f"  dagger call get-tunnel-secrets \\\n"
    dagger_cmd += f"      --source=./kcl \\\n"  # Note: kcl source for deploy()
    dagger_cmd += f"      --cloudflare-token=env:CF_TOKEN \\\n"
    dagger_cmd += f"      --cloudflare-account-id={cloudflare_account_id} \\\n"
    dagger_cmd += f"      --zone-name={zone_name}"
    
    if backend_type != "local":
        dagger_cmd += f" \\\n      --backend-type={backend_type}"
        if backend_config_file is not None:
            dagger_cmd += f" \\\n      --backend-config-file=./backend.hcl"
    elif state_dir is not None:
        dagger_cmd += f" \\\n      --state-dir=./terraform-state"
    
    results.append(dagger_cmd)
    results.append("")
    results.append("Then install: sudo cloudflared service install <token>")
    results.append("")
    results.append("See: examples/homelab-media-stack/README.md")
    results.append("-" * 60)
    
elif unifi_success:
    results.append("○ UniFi: Success")
    results.append("✗ Cloudflare: Failed")
else:
    results.append("✗ UniFi: Failed")
    results.append("○ Cloudflare: Not attempted")

return "\n".join(results)
```

## Constraints & Assumptions

### Constraints

1. **No secrets in output**: Never include actual tunnel tokens in success messages
2. **Parameterized commands**: Dagger commands must reflect actual deployment parameters
3. **Maintain existing format**: Keep existing success indicators and structure
4. **Length limit**: Keep guidance concise (under 20 lines)
5. **Backend awareness**: Command examples must match the backend used during deployment
6. **Character limit**: String concatenation must not exceed Python line length guidelines

### Assumptions

1. User has access to same credentials used for deployment
2. User is in the project root directory when running commands
3. `get_tunnel_secrets()` function exists and works (implemented in prompt 01)
4. Backend configuration files are named consistently (e.g., `backend.hcl`)
5. User wants to retrieve credentials immediately after deployment

### Design Decisions

1. **Show both Terraform and Dagger options**: Users may prefer one over the other
2. **Recommend Dagger option**: Consistent with project approach
3. **Include cloudflared install command**: Common next step
4. **Link to example docs**: For users wanting more context
5. **Use visual separators**: Improve readability of multi-step guidance

## Acceptance Criteria

### Functional Requirements

- [ ] [`deploy_cloudflare()`](../../src/main/main.py:422-571) includes credential retrieval guidance after line 563
- [ ] [`deploy()`](../../src/main/main.py:574-742) includes guidance in final summary (only if both succeed)
- [ ] Guidance includes both Terraform and Dagger command options
- [ ] Dagger command reflects actual deployment parameters:
  - [ ] Cloudflare account ID
  - [ ] Zone name
  - [ ] Backend type (if not local)
  - [ ] Backend config file flag (if applicable)
  - [ ] State dir flag (if provided)
- [ ] Guidance only shown on successful Cloudflare deployment
- [ ] Existing success indicators preserved (`✓ Success`, backend type, etc.)
- [ ] Visual separators used for readability (dashes, spacing)

### Message Format

- [ ] Uses consistent line length (< 80 characters where possible)
- [ ] Properly indented for readability
- [ ] Commands formatted with line continuations (`\`)
- [ ] Clear section headers ("Next Step:", numbered steps)
- [ ] Link to example documentation included

### Edge Cases

- [ ] Guidance not shown if `deploy_cloudflare()` fails
- [ ] Guidance not shown if `deploy()` Cloudflare phase fails  
- [ ] Command examples handle missing optional parameters gracefully
- [ ] Backend config file path shown correctly regardless of actual filename

### Testing

- [ ] Existing `deploy_cloudflare()` tests updated to expect new message format
- [ ] Existing `deploy()` tests updated to expect guidance
- [ ] Test verifies guidance includes correct parameters from function call
- [ ] Test verifies no guidance shown on failure
- [ ] Manual testing verifies commands work as documented

### Documentation

- [ ] No changes to external docs needed (guidance is self-contained)
- [ ] Code comments explain why guidance is conditional (Cloudflare success only)
- [ ] Inline example shows correct command syntax

## Implementation Notes

### String Building Pattern

Use multi-line string concatenation for readability:

```python
result_msg += "\n\n" + "-" * 60
result_msg += "\nSection Header"
result_msg += "\n" + "-" * 60
result_msg += "\n\nParagraph text here."
result_msg += "\n\nNext section..."
```

Avoid f-strings with embedded newlines (harder to maintain).

### Conditional Logic Location

- **In `deploy_cloudflare()`**: Add guidance after success determination (line 563+)
- **In `deploy()`**: Add guidance inside the `if unifi_success and cf_success:` block

### Parameter Access

Both functions have access to all needed parameters:
- `cloudflare_account_id`: passed as argument
- `zone_name`: passed as argument  
- `backend_type`: passed as argument
- `backend_config_file`: passed as argument
- `state_dir`: passed as argument
- `using_persistent_state`: computed boolean

### Testing Strategy

Update existing unit tests that check success messages:
```python
def test_deploy_cloudflare_success():
    result = await deploy_cloudflare(...)
    assert "✓ Success" in result
    assert "Next Step: Retrieve Tunnel Credentials" in result  # New assertion
    assert "dagger call get-tunnel-secrets" in result
    assert cloudflare_account_id in result
```

## File Locations

- **Target file**: [`src/main/main.py`](../../src/main/main.py)
  - Function 1: `deploy_cloudflare()` (lines 422-571)
  - Function 2: `deploy()` (lines 574-742)
- **Test file**: `tests/unit/test_deployment_functions.py` (existing)
- **Reference**: [`examples/homelab-media-stack/README.md`](../../examples/homelab-media-stack/README.md:309-329) (shows existing workflow)

## Dependencies

- **Required**: Prompt 01 must be implemented first (creates `get_tunnel_secrets()` function)
- **Soft dependency**: If prompt 01 not yet implemented, can add placeholder text pointing to `terraform output` only

## Reference

- **Target file**: [`src/main/main.py`](../../src/main/main.py)
  - `deploy_cloudflare()` success message: [line 563-569](../../src/main/main.py:563-569)
  - `deploy()` summary: [lines 728-741](../../src/main/main.py:728-741)
- **Example workflow**: [`examples/homelab-media-stack/README.md`](../../examples/homelab-media-stack/README.md:309-329)
- **Terraform outputs**: [`terraform/modules/cloudflare-tunnel/outputs.tf`](../../terraform/modules/cloudflare-tunnel/outputs.tf:11-22)
