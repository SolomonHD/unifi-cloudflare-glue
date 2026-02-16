# OpenSpec Prompt: Simplify Destroy Function

## Context

The `terraform/modules/glue/` combined module exists (Prompt 10), and `deploy()`/`plan()` have been simplified (Prompts 11-12). Now `destroy()` needs to be updated to use the combined module with selective flags.

## Goal

Update `src/main/main.py` to:
1. Modify `destroy()` to use the combined Terraform module
2. Add `--unifi-only` and `--cloudflare-only` boolean flags
3. Destroy selected components only

## Scope

### In Scope
- Update `destroy()` function to use `terraform/modules/glue/`
- Add `unifi_only` and `cloudflare_only` boolean parameters
- Generate only needed config files based on flags
- Handle state management correctly for selective destroy

### Out of Scope
- Changes to `deploy()` or `plan()` (handled separately)

## Desired Behavior

### Default (Both Components)
```bash
dagger call destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
```
Destroys both UniFi DNS and Cloudflare Tunnels (Cloudflare first, then UniFi via module dependency).

### UniFi Only
```bash
dagger call destroy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only
```

### Cloudflare Only
```bash
dagger call destroy \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --cloudflare-only
```

## Constraints & Assumptions

- The combined module at `terraform/modules/glue/` exists
- Terraform destroy requires the configuration to know what to destroy
- When destroying both, the module's `depends_on` ensures Cloudflare goes first
- For selective destroy, use Terraform `-target` option or module-level targeting

## Acceptance Criteria

1. `destroy()` function uses `terraform/modules/glue/` module
2. Function has `unifi_only: bool = False` parameter
3. Function has `cloudflare_only: bool = False` parameter
4. Validation: error if both flags are True
5. Generates only needed KCL configs based on flags
6. Returns status message showing what was destroyed

## Function Signature

```python
@function
async def destroy(
    self,
    kcl_source: Annotated[dagger.Directory, Doc("Source directory containing KCL configs")],
    unifi_url: Annotated[str, Doc("UniFi Controller URL")] = "",
    api_url: Annotated[str, Doc("UniFi API URL")] = "",
    unifi_api_key: Annotated[Optional[Secret], Doc("UniFi API key")] = None,
    unifi_username: Annotated[Optional[Secret], Doc("UniFi username")] = None,
    unifi_password: Annotated[Optional[Secret], Doc("UniFi password")] = None,
    unifi_insecure: Annotated[bool, Doc("Skip TLS verification")] = False,
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
    unifi_only: Annotated[bool, Doc("Destroy only UniFi DNS")] = False,
    cloudflare_only: Annotated[bool, Doc("Destroy only Cloudflare")] = False,
) -> str:
```

## Implementation Notes

For selective destroy, use Terraform's `-target` option:
```bash
# Destroy only UniFi
terraform destroy -target=module.unifi_dns -auto-approve

# Destroy only Cloudflare
terraform destroy -target=module.cloudflare_tunnel -auto-approve
```

## Files to Modify

| File | Changes |
|------|---------|
| `src/main/main.py` | Update `destroy()` function |

## Dependencies

- Prompt 10: `terraform/modules/glue/` module must exist
- Reference existing `destroy()` function (lines 1524-1923) for patterns
