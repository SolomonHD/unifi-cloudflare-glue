# OpenSpec Change Prompt

## Context

The unifi-cloudflare-glue module contains KCL generators that output multi-document YAML when run. The Dagger module pipes KCL output to `yq eval` to convert YAML to JSON, but this fails because `yq eval` cannot parse multi-document YAML from stdin.

The error occurs in both generators:
- `generators/unifi.k` - outputs both `sample_config` and `result`
- `generators/cloudflare.k` - outputs both `sample_config` and `result`

When KCL runs these files, it produces:
```yaml
sample_config:
  devices: ...
---
result:
  devices: ...
```

The yq command fails with:
```
Error: bad file '-': yaml: line 2: mapping values are not allowed in this context
```

## Goal

Fix the generator files to output only a single YAML document so that `yq eval -o=json '.'` can successfully parse the output.

## Scope

**In scope:**
- Modify `generators/unifi.k` to output only the `result` variable
- Modify `generators/cloudflare.k` to output only the `result` variable
- Preserve `sample_config` for testing purposes (move to separate test file or make conditional)
- Update any related test files that depend on `sample_config` output

**Out of scope:**
- Changes to Dagger Python code
- Changes to schemas
- Changes to the `main.k` module entry point

## Desired Behavior

- `kcl run generators/unifi.k` outputs only the UniFi configuration result
- `kcl run generators/cloudflare.k` outputs only the Cloudflare configuration result
- Dagger `generate-unifi-config` and `generate-cloudflare-config` functions work without yq errors
- Sample configurations remain available for testing (via separate test files)

## Constraints & Assumptions

- The `sample_config` is used for standalone testing of generators
- The fix should not break existing functionality when generators are imported by user configs
- Option 1 preferred: Move `sample_config` to separate test files
- Option 2 acceptable: Wrap `sample_config` in a conditional that only outputs when run directly

## Acceptance Criteria

- [ ] `kcl run generators/unifi.k` outputs valid single-document YAML
- [ ] `kcl run generators/cloudflare.k` outputs valid single-document YAML
- [ ] `kcl run generators/unifi.k | yq eval -o=json '.'` succeeds
- [ ] `kcl run generators/cloudflare.k | yq eval -o=json '.'` succeeds
- [ ] Dagger `generate-unifi-config --source=./kcl` succeeds
- [ ] Dagger `generate-cloudflare-config --source=./kcl` succeeds
- [ ] Sample configurations remain testable (moved to appropriate test files)
