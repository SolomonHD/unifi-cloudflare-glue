## Why

When a consumer's KCL module has a git dependency on `unifi-cloudflare-glue`, running `kcl run` outputs module download messages (e.g., `cloning 'https://github.com/...'`) to stdout. This contaminates the YAML output and causes invalid JSON generation, resulting in Terraform failures with "Can't access attributes on a primitive-typed value (string)" errors.

## What Changes

- Modify `generate_unifi_config()` in `src/main/main.py` to run `kcl mod update` before `kcl run generators/unifi.k`
- Modify `generate_cloudflare_config()` in `src/main/main.py` with the same fix
- Add error handling for `kcl mod update` failures (network issues, invalid kcl.mod)
- Ensure backward compatibility with KCL modules that don't have git dependencies

## Capabilities

### New Capabilities
- `kcl-dependency-preload`: Pre-download KCL git dependencies before running generators to ensure clean YAML/JSON output

### Modified Capabilities
- None (this is a bugfix with no spec-level behavior changes)

## Impact

- **Dagger Module**: `src/main/main.py` - Two functions modified
- **Behavior**: No breaking changes; existing KCL modules without git dependencies continue to work
- **Performance**: Slight increase in initial run time due to dependency download, but cached on subsequent runs
- **Error Handling**: New error messages for network failures or invalid kcl.mod files during `kcl mod update`
