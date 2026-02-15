## Context

The `plan()` function currently operates on a "all-or-nothing" model, requiring both UniFi and Cloudflare credentials and generating separate plans using individual Terraform modules (`terraform/modules/unifi-dns/` and `terraform/modules/cloudflare-tunnel/`). This approach:

1. Forces users to provide credentials for both systems even when only planning changes to one
2. Generates two separate plan files that must be reviewed independently
3. Is inconsistent with the simplified `deploy()` function that uses the combined module

The `deploy()` function was recently updated (in `simplify-deploy-function`) to use the combined Terraform module at `terraform/modules/glue/` with `--unifi-only` and `--cloudflare-only` flags. The `plan()` function needs the same treatment to maintain API consistency.

## Goals / Non-Goals

**Goals:**
- Update `plan()` to use the combined Terraform module at `terraform/modules/glue/`
- Add `--unifi-only` and `--cloudflare-only` boolean flags to `plan()`
- Implement conditional credential requirements based on selected components
- Generate appropriate plan artifacts for selected components only
- Maintain backward compatibility in behavior (both components by default)

**Non-Goals:**
- Changes to the combined Terraform module itself (already exists)
- Changes to `destroy()` function (handled in separate prompt)
- Changes to KCL generators or schema validation
- Adding new plan output formats beyond existing tfplan/json/txt

## Decisions

### Use Combined Module with Conditional Config Mounting

**Decision:** The `plan()` function will use the combined `terraform/modules/glue/` module, mounting only the configuration files needed for the selected components.

**Rationale:** 
- Consistent with the updated `deploy()` function
- Reduces code duplication between plan and deploy
- Single Terraform state for both components when using persistent state

**Implementation:**
```python
# Mount combined module
ctr = ctr.with_directory("/module", tf_module)

# Mount configs conditionally
if not cloudflare_only:
    ctr = ctr.with_directory("/workspace/unifi", unifi_dir)
if not unifi_only:
    ctr = ctr.with_directory("/workspace/cloudflare", cloudflare_dir)
```

### Parameter Defaults for Optional Credentials

**Decision:** Make previously required parameters optional with empty defaults, then validate based on deployment scope.

**Rationale:**
- Dagger doesn't support "conditional required" parameters at the CLI level
- Runtime validation provides clear error messages
- Matches pattern established in `deploy()` function

**Implementation:**
```python
cloudflare_token: Annotated[Optional[Secret], Doc("...")] = None,
cloudflare_account_id: Annotated[str, Doc("...")] = "",
zone_name: Annotated[str, Doc("...")] = "",
```

### Unified Plan Output Structure

**Decision:** Generate a single set of plan files (`plan.tfplan`, `plan.json`, `plan.txt`) regardless of component selection, with the summary indicating which components were included.

**Rationale:**
- Simpler output structure than separate files per component
- Combined module naturally produces unified plan
- Summary provides clear indication of what was planned

**Alternative considered:** Separate plan files per component (`unifi-plan.tfplan`, `cloudflare-plan.tfplan`). Rejected because the combined module produces a single plan; splitting would require post-processing.

### Error Handling Pattern

**Decision:** Use `ValueError` exceptions for validation failures (consistent with current `plan()` implementation) rather than returning error strings (used by `deploy()`).

**Rationale:**
- Maintains consistency within the `plan()` function's existing error handling
- `plan()` returns a `dagger.Directory`, not a string, so exceptions are appropriate

## Risks / Trade-offs

**[Risk]** Breaking change to function signature may affect existing automation
→ **Mitigation:** Parameters that become optional have sensible defaults; existing calls will continue to work

**[Risk]** Users may be confused about which credentials are required when
→ **Mitigation:** Clear validation error messages indicating exactly which credentials are needed for each mode

**[Risk]** Combined plan may be harder to review than separate component plans
→ **Mitigation:** Plan summary clearly indicates which resources belong to which component; JSON output can be programmatically filtered

## Migration Plan

No migration needed - this is a functional enhancement. Existing calls to `plan()` will continue to work:

```bash
# Existing usage still works (full deployment)
dagger call plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --unifi-api-key=env:UNIFI_API_KEY \
    export --path=./plans
```

New selective options available:
```bash
# UniFi-only
dagger call plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only \
    export --path=./plans

# Cloudflare-only
dagger call plan \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --cloudflare-only \
    export --path=./plans
```

## Open Questions

None - design is ready for implementation.
