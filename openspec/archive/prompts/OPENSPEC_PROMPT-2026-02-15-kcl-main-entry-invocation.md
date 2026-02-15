# OpenSpec Change Prompt

## Context

KCL v0.12.x has a SIGSEGV bug in its native Rust/CGO execution layer that crashes when running any `.k` file other than the module entry point (`main.k`) from a KCL module that imports schemas via git dependencies. The `unifi-cloudflare-glue` Dagger module currently runs `kcl run generators/unifi.k` and `kcl run generators/cloudflare.k`, which triggers this crash in consumer projects.

Running `kcl run main.k` works correctly because KCL handles the module entry point differently. The consumer's `main.k` already calls both generators and exports `unifi_output` and `cf_output` as public variables.

## Goal

Change the Dagger module's KCL invocation strategy from running separate generator entry-point files (`generators/*.k`) to running `main.k` and extracting the relevant output section with `yq`.

## Scope

**In scope:**
- Modify `generate_unifi_config()` in `src/main/main.py` to run `kcl run main.k` instead of `kcl run generators/unifi.k`
- Modify `generate_cloudflare_config()` in `src/main/main.py` to run `kcl run main.k` instead of `kcl run generators/cloudflare.k`
- Use `yq` to extract `.unifi_output` or `.cf_output` from the full `main.k` YAML output
- Remove the file-existence checks for `generators/unifi.k` and `generators/cloudflare.k`
- Add a file-existence check for `main.k` instead
- Update documentation and examples to reflect the new contract
- Update error messages to reference `main.k` instead of `generators/*.k`

**Out of scope:**
- Fixing the KCL v0.12.x SIGSEGV bug itself (upstream issue)
- Changes to KCL schemas
- Changes to Terraform modules
- Consumer-side KCL changes (consumer's `main.k` already exports the needed variables)

## Desired Behavior

1. `generate_unifi_config()` should:
   - Verify `main.k` exists in the source directory
   - Run `kcl mod update` (already implemented)
   - Run `kcl run main.k` to get full YAML output
   - Use `yq eval '.unifi_output' /tmp/kcl-output.yaml` to extract UniFi config
   - Convert extracted YAML to JSON with `yq eval -o=json`

2. `generate_cloudflare_config()` should:
   - Same flow but extract `.cf_output` instead

3. Consumer's `main.k` must export:
   - `unifi_output` — result of `unifi_gen.generate_unifi_config(config)`
   - `cf_output` — result of `cf_gen.generate_cloudflare_config(config)`

## Constraints & Assumptions

- Assumption: Consumer's `main.k` exports `unifi_output` and `cf_output` as public (non-underscore-prefixed) variables
- Assumption: `yq eval '.unifi_output'` correctly extracts a nested YAML node from multi-document output
- Constraint: Must maintain backward compatibility — existing consumers that already have these variables in `main.k` should work without changes
- Constraint: The `generators/` directory in consumer projects becomes optional/dead code
- Constraint: Error messages must clearly explain the new requirement if `main.k` doesn't export the expected variables

## Acceptance Criteria

- [ ] `generate_unifi_config()` runs `kcl run main.k` instead of `kcl run generators/unifi.k`
- [ ] `generate_cloudflare_config()` runs `kcl run main.k` instead of `kcl run generators/cloudflare.k`
- [ ] UniFi JSON output is extracted from `.unifi_output` in the YAML
- [ ] Cloudflare JSON output is extracted from `.cf_output` in the YAML
- [ ] Generated JSON files are valid and match the previous generator output format
- [ ] Clear error message when `main.k` is missing or doesn't export expected variables
- [ ] No SIGSEGV crash when running with KCL v0.12.x
- [ ] Examples and documentation updated to show `main.k`-based pattern
