# OpenSpec Change Prompt

## Context

The `unifi-cloudflare-glue` Dagger module generates JSON configurations by running KCL generators. When a consumer's KCL module has a git dependency on `unifi-cloudflare-glue`, running `kcl run` outputs module download messages (e.g., `cloning 'https://github.com/...'`) to stdout, which contaminates the YAML output and causes invalid JSON generation.

The generated `unifi.json` file ends up containing strings like:
```
"cloning 'https://github.com/SolomonHD/unifi-cloudflare-glue' with tag 'v0.9.2' {}"
```

Instead of valid JSON, causing Terraform to fail with:
```
Can't access attributes on a primitive-typed value (string)
```

## Goal

Fix the Dagger module's KCL execution to ensure clean YAML/JSON output by pre-downloading KCL dependencies before running generators.

## Scope

**In scope:**
- Modify `generate_unifi_config()` in `src/main/main.py` to run `kcl mod update` before `kcl run`
- Modify `generate_cloudflare_config()` in `src/main/main.py` with the same fix
- Ensure dependency download messages don't contaminate generator output
- Maintain backward compatibility with existing KCL modules

**Out of scope:**
- Changes to KCL schemas or generators
- Changes to Terraform modules
- Changes to the KCL dependency resolution mechanism itself

## Desired Behavior

1. When `generate_unifi_config()` or `generate_cloudflare_config()` is called:
   - First run `kcl mod update` to pre-download all git dependencies
   - Then run `kcl run generators/*.k` to get clean YAML output
   - The output should contain only valid YAML without download messages

2. The fix should handle:
   - Fresh containers where dependencies haven't been downloaded
   - Cached containers where dependencies already exist
   - Modules with multiple git dependencies
   - Network failures during dependency download

## Constraints & Assumptions

- Assumption: `kcl mod update` outputs download messages to stderr or a separate stream, not interfering with stdout
- Assumption: Running `kcl mod update` before `kcl run` will cache dependencies for the subsequent `kcl run`
- Constraint: Must not break existing functionality for KCL modules without git dependencies
- Constraint: Must handle errors from `kcl mod update` gracefully (e.g., network issues, invalid kcl.mod)

## Acceptance Criteria

- [ ] `generate_unifi_config()` runs `kcl mod update` before `kcl run generators/unifi.k`
- [ ] `generate_cloudflare_config()` runs `kcl mod update` before `kcl run generators/cloudflare.k`
- [ ] Generated JSON files contain valid configuration objects, not git clone messages
- [ ] Error handling for `kcl mod update` failures provides clear messages
- [ ] Both functions work correctly for KCL modules with and without git dependencies
