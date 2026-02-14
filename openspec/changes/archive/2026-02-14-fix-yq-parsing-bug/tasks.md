# Implementation Tasks: Fix yq Parsing Bug

## Phase 1: Code Changes

- [x] Fix `generate_unifi_config` function in `src/main/main.py` (line 142)
  - Change: `"kcl run generators/unifi.k | yq -o=json '.result'"`
  - To: `"kcl run generators/unifi.k | yq eval -o=json '.'"`

- [x] Fix `generate_cloudflare_config` function in `src/main/main.py` (line 1678)
  - Change: `"kcl run generators/cloudflare.k | yq -o=json '.result'"`
  - To: `"kcl run generators/cloudflare.k | yq eval -o=json '.'"`

## Phase 2: Testing

- [x] Test `generate_unifi_config` function locally
  ```bash
  dagger call generate-unifi-config --source=./kcl
  ```

- [x] Test `generate_cloudflare_config` function locally
  ```bash
  dagger call generate-cloudflare-config --source=./kcl
  ```

- [x] Verify generated JSON is valid
  - Check unifi.json structure matches expected Terraform module input
  - Check cloudflare.json structure matches expected Terraform module input

- [ ] Test with portainer-docker-compose KCL configuration
  - Ensure compatibility with existing KCL configs

## Phase 3: Verification

- [x] Run Dagger module tests (if available)
- [x] Verify no YAML parsing errors in output
- [x] Confirm JSON output is properly formatted

## Phase 4: Documentation

- [x] Update CHANGELOG.md with bug fix entry
- [x] Mark change as complete in openspec tracking

## Acceptance Criteria

- [x] `dagger call generate-unifi-config --source=./kcl` succeeds without errors
- [x] `dagger call generate-cloudflare-config --source=./kcl` succeeds without errors
- [x] No "mapping values are not allowed in this context" errors
- [x] Generated JSON files are valid and usable by Terraform modules
