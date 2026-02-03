# Tasks: Add Persistent Local State Directory Support

## Implementation Tasks

- [x] **Add `state_dir` parameter to `deploy_unifi` function**
  - Add parameter: `state_dir: Annotated[Optional[dagger.Directory], Doc("...")]  = None`
  - Add to function signature in `src/main/main.py`
  - Update docstring to reflect new parameter

- [x] **Add `state_dir` parameter to `deploy_cloudflare` function**
  - Add parameter: `state_dir: Annotated[Optional[dagger.Directory], Doc("...")]  = None`
  - Add to function signature in `src/main/main.py`
  - Update docstring to reflect new parameter

- [x] **Add `state_dir` parameter to `deploy` function**
  - Add parameter to orchestration function
  - Pass through to both `deploy_unifi` and `deploy_cloudflare` calls

- [x] **Add `state_dir` parameter to `destroy` function**
  - Add parameter to cleanup function
  - Pass through to both cleanup phases (Cloudflare then UniFi)

- [x] **Implement validation logic for mutual exclusion**
  - Add validation BEFORE backend configuration logic in all four functions
  - Check: if `backend_type != "local"` and `state_dir is not None`, return error
  - Error message must explain mutual exclusion and show all three mode examples

- [x] **Implement state directory mounting logic**
  - Add after Terraform container creation, before terraform init
  - Mount state directory: `ctr = ctr.with_directory("/state", state_dir)`
  - Only execute if `state_dir is not None`

- [x] **Implement module file copying to state directory**
  - Add shell command: `cp -r /module/* /state/ && ls -la /state`
  - Execute in container after mounting state directory
  - Add report line: "✓ Mounted persistent state directory"

- [x] **Implement working directory logic**
  - When `state_dir` is provided: `ctr = ctr.with_workdir("/state")`
  - When `state_dir` is None: `ctr = ctr.with_workdir("/module")` (default)
  - Apply consistently across all four functions

- [x] **Ensure consistent implementation across all four functions**
  - Validation logic identical in `deploy_unifi`, `deploy_cloudflare`, `deploy`, `destroy`
  - State directory handling identical across all functions
  - Working directory logic identical across all functions

## Documentation Tasks

- [x] **Update README.md with state management section**
  - Add "State Management in Dagger Functions" section after "Modules" section
  - Include comparison matrix showing three modes (Ephemeral, Remote Backend, Persistent Local)
  - Provide usage examples for all three modes
  - Document when to use each mode
  - Note about state locking and team collaboration limitations
  - Add warning about backup responsibility for local state directories

- [x] **Add state management examples to README.md**
  - Show ephemeral mode (default, no flags)
  - Show remote backend mode (from prompt 01)
  - Show persistent local mode (NEW)
  - Include `destroy` examples matching each mode

- [x] **Update CHANGELOG.md**
  - Add entry under "### Added" section
  - Document `state_dir` parameter addition to four functions
  - Explain three state management modes
  - Provide usage example
  - Note backward compatibility (default unchanged)

## Validation Tasks

- [x] **Validate with openspec**
  - Run: `openspec validate add-persistent-state-directory --strict`
  - Resolve any validation errors
  - Ensure all requirements have scenarios

- [x] **Test mutual exclusion validation**
  - Verify error when using `--state-dir` with `--backend-type=s3`
  - Verify success when using only `--state-dir`
  - Verify success when using only `--backend-type=s3 --backend-config-file`
  - Verify success when using neither (default ephemeral)

- [x] **Verify error message clarity**
  - Check that error message shows conflicting flags
  - Check that error message provides three example commands
  - Check that examples are complete and actionable

- [x] **Test implementation consistency**
  - Verify `deploy_unifi` handles state directory correctly
  - Verify `deploy_cloudflare` handles state directory correctly
  - Verify `deploy` passes state directory to both phases
  - Verify `destroy` uses state directory for cleanup

## Notes

- Implementation should follow the exact pattern specified in the prompt file
- Consider extracting common logic to helper function: `_configure_state_storage(ctr, backend_type, backend_config_file, state_dir)`
- This depends on prompt 01 (remote backend support) being implemented first
- Default behavior (ephemeral state) must remain unchanged for backwards compatibility
