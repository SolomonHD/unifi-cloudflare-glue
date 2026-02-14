# OpenSpec Change Prompt

## Context
The unifi-cloudflare-glue Dagger module v0.7.1 fails when generating UniFi and Cloudflare configurations. The error occurs when executing the KCL generation commands due to incorrect yq parsing.

Error message:
```
Error: bad file '-': yaml: line 2: mapping values are not allowed in this context
Hint: Check your KCL syntax with 'kcl run generators/unifi.k' locally.
```

The local KCL execution works correctly, but the Dagger module's shell command fails.

## Goal
Fix the YAML/JSON parsing issue in the Dagger module's generate_unifi_config and generate_cloudflare_config functions in `src/main/main.py`.

## Scope

**In scope:**
- Fix the yq command in `src/main/main.py` for generate_unifi_config function (line ~142)
- Fix the yq command in `src/main/main.py` for generate_cloudflare_config function (line ~1678)
- Test that the fixes work with the portainer-docker-compose KCL configuration

**Out of scope:**
- Other Dagger functions (deploy, plan, destroy)
- KCL schema changes

## Desired Behavior
- `dagger call -m unifi-cloudflare-glue generate-unifi-config --source=./kcl` should successfully generate the UniFi config JSON
- `dagger call -m unifi-cloudflare-glue generate-cloudflare-config --source=./kcl` should successfully generate the Cloudflare config JSON

## Root Cause
The current command:
```python
"kcl run generators/unifi.k | yq -o=json '.result'"
```

This fails because:
1. KCL outputs YAML by default, not JSON
2. yq expects to parse YAML, but the pipe from kcl may be producing output that yq misinterprets
3. The `.result` filter assumes the KCL output is JSON, but it's actually YAML

## Constraints & Assumptions
- KCL is available in the container at `/src` (the source directory is mounted there)
- yq is installed in the container
- The fix should work with the existing KCL output format

## Suggested Fix
Change the yq command to properly parse YAML output from KCL:
```python
"kcl run generators/unifi.k | yq eval -o=json '.'"
```
or
```python
"kcl run -y generators/unifi.k | yq eval -o=json '.'"
```

The `-y` flag tells KCL to output YAML explicitly, and `yq eval` is the more explicit form of the yq command.

## Acceptance Criteria
- [ ] generate_unifi_config function works without errors
- [ ] generate_cloudflare_config function works without errors
- [ ] No YAML parsing errors in Dagger output
