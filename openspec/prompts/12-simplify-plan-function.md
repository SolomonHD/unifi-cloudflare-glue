# OpenSpec Prompt: Simplify Plan Function

## Context

The `terraform/modules/glue/` combined module exists (Prompt 10), and `deploy()` has been simplified (Prompt 11). Now `plan()` needs to be updated to use the combined module with the same selective deployment flags.

## Goal

Update `src/main/main.py` to:
1. Modify `plan()` to use the combined Terraform module
2. Add `--unifi-only` and `--cloudflare-only` boolean flags
3. Generate appropriate configs based on flags
4. Return plan artifacts for selected components

## Scope

### In Scope
- Update `plan()` function to use `terraform/modules/glue/`
- Add `unifi_only` and `cloudflare_only` boolean parameters
- Generate only needed config files based on flags
- Return Directory with plan artifacts

### Out of Scope
- Changes to `deploy()` (handled in Prompt 11)
- Changes to `destroy()` (handled separately)

## Desired Behavior

### Default (Both Components)
```bash
dagger call plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    export --path=./plans
```
Generates plan for both UniFi DNS and Cloudflare Tunnels.

### UniFi Only
```bash
dagger call plan \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only \
    export --path=./plans
```

### Cloudflare Only
```bash
dagger call plan \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --cloudflare-only \
    export --path=./plans
```

## Constraints & Assumptions

- The combined module at `terraform/modules/glue/` exists
- When `--unifi-only` is set, Cloudflare credentials are optional
- When `--cloudflare-only` is set, UniFi credentials are optional
- Cannot use both flags simultaneously
- Output Directory contains plan files based on selected components

## Acceptance Criteria

1. `plan()` function uses `terraform/modules/glue/` module
2. Function has `unifi_only: bool = False` parameter
3. Function has `cloudflare_only: bool = False` parameter
4. Validation: error if both flags are True
5. Generates only needed KCL configs based on flags
6. Creates plan artifacts (tfplan, json, txt, summary)
7. Returns `dagger.Directory` with plan files

## Function Signature

```python
@function
async def plan(
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
    unifi_only: Annotated[bool, Doc("Plan only UniFi DNS")] = False,
    cloudflare_only: Annotated[bool, Doc("Plan only Cloudflare")] = False,
) -> dagger.Directory:
```

## Output Files

The returned Directory should contain:
- `plan.tfplan` - Binary plan file
- `plan.json` - JSON format
- `plan.txt` - Human-readable format
- `plan-summary.txt` - Summary with resource counts

## Files to Modify

| File | Changes |
|------|---------|
| `src/main/main.py` | Update `plan()` function |

## Dependencies

- Prompt 10: `terraform/modules/glue/` module must exist
- Reference existing `plan()` function (lines 1116-1522) for patterns
