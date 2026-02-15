# OpenSpec Prompt: Simplify Deploy Function

## Context

The `terraform/modules/glue/` combined module has been created (Prompt 10). Now the Dagger `deploy()` function needs to be updated to use this combined module, and the separate `deploy_unifi()` and `deploy_cloudflare()` functions should be removed.

## Goal

Update `src/main/main.py` to:
1. Modify `deploy()` to use the combined Terraform module by default
2. Add `--unifi-only` and `--cloudflare-only` boolean flags for selective deployment
3. Remove `deploy_unifi()` function entirely
4. Remove `deploy_cloudflare()` function entirely

## Scope

### In Scope
- Update `deploy()` function to use `terraform/modules/glue/`
- Add `unifi_only` and `cloudflare_only` boolean parameters
- Remove `deploy_unifi()` function (lines ~356-588)
- Remove `deploy_cloudflare()` function (lines ~589-841)
- Update function signature and docstring

### Out of Scope
- Changes to `plan()` or `destroy()` (handled separately)
- Terraform module changes (already completed)

## Desired Behavior

### Default (Both Components)
```bash
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```
Uses combined module, deploys both UniFi DNS and Cloudflare Tunnels.

### UniFi Only
```bash
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only
```
Uses combined module but only applies UniFi resources (no Cloudflare credentials required).

### Cloudflare Only
```bash
dagger call deploy \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --cloudflare-only
```
Uses combined module but only applies Cloudflare resources (no UniFi credentials required).

## Constraints & Assumptions

- The combined module at `terraform/modules/glue/` exists
- When `--unifi-only` is set, Cloudflare credentials should be optional
- When `--cloudflare-only` is set, UniFi credentials should be optional
- When neither flag is set, both sets of credentials are required
- Cannot use both `--unifi-only` and `--cloudflare-only` simultaneously (validation error)

## Acceptance Criteria

1. `deploy()` function uses `terraform/modules/glue/` module
2. Function has `unifi_only: bool = False` parameter
3. Function has `cloudflare_only: bool = False` parameter
4. Validation: error if both `unifi_only` and `cloudflare_only` are True
5. `deploy_unifi()` function is completely removed
6. `deploy_cloudflare()` function is completely removed
7. Single Terraform init/apply in all cases
8. Returns appropriate status message based on deployment scope

## Function Signature

```python
@function
async def deploy(
    self,
    kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
    unifi_url: Annotated[str, Doc("UniFi Controller URL")] = "",
    api_url: Annotated[str, Doc("UniFi API URL (defaults to unifi_url)")] = "",
    unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key")] = None,
    unifi_username: Annotated[Optional[Secret], Doc("UniFi username")] = None,
    unifi_password: Annotated[Optional[Secret], Doc("UniFi password")] = None,
    unifi_insecure: Annotated[bool, Doc("Skip TLS verification for UniFi")] = False,
    cloudflare_token: Annotated[Optional[Secret], Doc("Cloudflare API Token")] = None,
    cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")] = "",
    zone_name: Annotated[str, Doc("DNS zone name")] = "",
    terraform_version: Annotated[str, Doc("Terraform version")] = "latest",
    kcl_version: Annotated[str, Doc("KCL version")] = "latest",
    backend_type: Annotated[str, Doc("Backend type")] = "local",
    backend_config_file: Annotated[Optional[dagger.File], Doc("Backend config")] = None,
    state_dir: Annotated[Optional[dagger.Directory], Doc("State directory")] = None,
    no_cache: Annotated[bool, Doc("Bypass cache")] = False,
    cache_buster: Annotated[str, Doc("Cache key")] = "",
    unifi_only: Annotated[bool, Doc("Deploy only UniFi DNS (skip Cloudflare)")] = False,
    cloudflare_only: Annotated[bool, Doc("Deploy only Cloudflare (skip UniFi)")] = False,
) -> str:
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/main/main.py` | Update `deploy()`, remove `deploy_unifi()`, remove `deploy_cloudflare()` |

## Dependencies

- Prompt 10: `terraform/modules/glue/` module must exist

## Notes

The combined Terraform module handles both deployments in a single apply. The flags control which configuration files are generated and passed:

- `unifi_only=True`: Only generate `unifi.json`, pass empty/null for Cloudflare config
- `cloudflare_only=True`: Only generate `cloudflare.json`, pass empty/null for UniFi config
- Neither flag: Generate both configs, deploy both

The combined module's variables should handle optional configs appropriately.
