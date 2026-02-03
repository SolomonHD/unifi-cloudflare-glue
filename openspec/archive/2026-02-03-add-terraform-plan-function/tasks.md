# Tasks: Add Terraform Plan Function

## Implementation Tasks

### Phase 1: Core Function Structure

- [x] Add `plan()` function to [`src/main/main.py`](../../src/main/main.py)
- [x] Define function signature with all parameters:
  - [x] KCL source directory
  - [x] UniFi authentication (API key OR username/password)
  - [x] Cloudflare authentication (API token, account ID, zone name)
  - [x] State management (state_dir OR backend configuration)
  - [x] Version control (Terraform version, KCL version)
  - [x] Cache control (no_cache OR cache_buster)
- [x] Add comprehensive docstring with example usage
- [x] Use `Annotated[..., Doc(...)]` for all parameter descriptions

### Phase 2: Validation Logic

- [x] Implement UniFi authentication validation:
  - [x] Check mutual exclusivity: API key XOR username/password
  - [x] For username/password: ensure both are provided
- [x] Implement state management validation:
  - [x] Check mutual exclusivity: state_dir XOR remote backend
  - [x] For remote backend (non-"local"): ensure backend_config_file provided
- [x] Implement cache control validation:
  - [x] Check mutual exclusivity: no_cache XOR cache_buster
  - [x] If no_cache: generate epoch timestamp as cache_buster

### Phase 3: KCL Configuration Generation

- [x] Call `_generate_unifi_config()` with KCL source and version
- [x] Call `_generate_cloudflare_config()` with KCL source and version
- [x] Handle errors from KCL generation

### Phase 4: UniFi Plan Generation

- [x] Prepare Terraform container for UniFi DNS module
  - [x] Use existing `_prepare_terraform_container()` helper
  - [x] Mount UniFi JSON configuration
  - [x] Apply state management configuration
  - [x] Inject cache buster if provided
- [x] Run `terraform init` for UniFi module
- [x] Run `terraform plan -out=unifi-plan.tfplan`
- [x] **CRITICAL**: Preserve container reference: `container = container.with_exec([...])`
- [x] Generate JSON output: `terraform show -json unifi-plan.tfplan > unifi-plan.json`
- [x] Generate text output: `terraform show unifi-plan.tfplan > unifi-plan.txt`
- [x] Extract plan files from POST-execution container

### Phase 5: Cloudflare Plan Generation

- [x] Prepare Terraform container for Cloudflare Tunnel module
  - [x] Use existing `_prepare_terraform_container()` helper
  - [x] Mount Cloudflare JSON configuration
  - [x] Apply state management configuration
  - [x] Inject cache buster if provided
- [x] Run `terraform init` for Cloudflare module
- [x] Run `terraform plan -out=cloudflare-plan.tfplan`
- [x] **CRITICAL**: Preserve container reference: `container = container.with_exec([...])`
- [x] Generate JSON output: `terraform show -json cloudflare-plan.tfplan > cloudflare-plan.json`
- [x] Generate text output: `terraform show cloudflare-plan.tfplan > cloudflare-plan.txt`
- [x] Extract plan files from POST-execution container

### Phase 6: Plan Summary Generation

- [x] Parse UniFi plan for resource counts:
  - [x] Attempt JSON parsing first
  - [x] Fallback to text parsing if JSON fails
  - [x] Extract: resources to add, change, destroy
- [x] Parse Cloudflare plan for resource counts:
  - [x] Attempt JSON parsing first
  - [x] Fallback to text parsing if JSON fails
  - [x] Extract: resources to add, change, destroy
- [x] Create `plan-summary.txt` with:
  - [x] Section for UniFi DNS module with counts
  - [x] Section for Cloudflare Tunnel module with counts
  - [x] Overall totals (sum of both modules)
  - [x] Metadata: ISO 8601 timestamp, Terraform version, KCL version, backend type

### Phase 7: Output Directory Assembly

- [x] Create output directory structure in container
- [x] Copy plan files to output directory:
  - [x] `unifi-plan.tfplan`
  - [x] `unifi-plan.json`
  - [x] `unifi-plan.txt`
  - [x] `cloudflare-plan.tfplan`
  - [x] `cloudflare-plan.json`
  - [x] `cloudflare-plan.txt`
  - [x] `plan-summary.txt`
- [x] Return `dagger.Directory` containing all artifacts

### Phase 8: Error Handling

- [x] Add try-except blocks for:
  - [x] KCL generation failures
  - [x] Terraform init failures
  - [x] Terraform plan failures
  - [x] File parsing failures (summary generation)
- [x] Return clear error messages with `"✗ Failed: "` prefix
- [x] Include relevant error details (stderr, exception messages)

## Documentation Tasks

- [x] Update [`README.md`](../../README.md):
  - [x] Add `plan` function to "Dagger Functions" section
  - [x] Example with persistent local state
  - [x] Example with remote backend
  - [x] Explain output directory structure
  - [x] Explain plan summary format
  - [x] Security note about plan file contents
- [x] Update [`CHANGELOG.md`](../../CHANGELOG.md):
  - [x] Add entry under "Unreleased" → "Added"
  - [x] Describe the plan function capability
  - [x] Include usage example
  - [x] Note about plan → review → apply workflow support

## Testing Tasks (Optional - can be deferred)

- [ ] Manual testing with persistent local state:
  - [ ] Deploy infrastructure with `--state-dir`
  - [ ] Run plan with same `--state-dir`
  - [ ] Verify plan shows "no changes"
  - [ ] Modify KCL configuration
  - [ ] Run plan again, verify changes detected
- [ ] Manual testing with remote backend:
  - [ ] Configure S3 backend
  - [ ] Deploy infrastructure with S3 backend
  - [ ] Run plan with same S3 backend
  - [ ] Verify plan accuracy
- [ ] Test output formats:
  - [ ] Verify binary plan files are valid Terraform plans
  - [ ] Verify JSON files are valid JSON
  - [ ] Verify text files are human-readable
  - [ ] Verify plan summary accuracy

## Dependencies

This change depends on:
- [ ] No code changes required to existing functions (uses existing helpers)
- [ ] Existing `_generate_unifi_config()` method
- [ ] Existing `_generate_cloudflare_config()` method
- [ ] Existing `_prepare_terraform_container()` helper
- [ ] Existing state management patterns from `deploy()` and `destroy()`

## Notes

- **Container Reference Preservation**: This is CRITICAL. Without preserving container references after `with_exec()`, file export will fail because you'll be accessing the pre-execution container instead of the post-execution container.
- **Plan Execution Order**: Plans must be generated in the same order as deployment (UniFi first, then Cloudflare) for consistency.
- **State Consistency**: Document that users must use the same state backend for plan and apply operations.
- **Security**: Plan files may contain sensitive values. Document `.gitignore` recommendations.
