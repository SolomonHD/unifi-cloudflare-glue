# Tasks: Test Integration Cache Buster and Wait Parameters

## Implementation Tasks

- [x] Update `test_integration` function signature to add `cache_buster` parameter
  - Add parameter with type `str`, default `""`
  - Add proper `Annotated[..., Doc(...)]` annotation
  - Position after existing optional parameters

- [x] Update `test_integration` function signature to add `wait_before_cleanup` parameter
  - Add parameter with type `int`, default `0`
  - Add proper `Annotated[..., Doc(...)]` annotation
  - Position after `cache_buster` parameter

- [x] Implement cache buster environment variable injection
  - Modify container creation to conditionally add `CACHE_BUSTER` env var
  - Use `with_env_variable("CACHE_BUSTER", cache_buster)` when value is non-empty
  - Apply to the base container setup in Phase 1

- [x] Implement wait logic between validation and cleanup phases
  - Add async sleep (`asyncio.sleep()`) after Phase 4 completes
  - Only execute when `wait_before_cleanup > 0`
  - Add import for `asyncio` if not already present

- [x] Update test report to include cache buster information
  - Add cache buster value to initial test information section when non-empty
  - Include message like "Cache Buster: <value>" in report

- [x] Update test report to include wait duration information
  - Add wait duration message before the sleep occurs
  - Add completion message after sleep finishes
  - Only include when `wait_before_cleanup > 0`

- [x] Update function docstring with example usage
  - Add example showing both new parameters
  - Document the purpose of each parameter
  - Include CLI example with `--cache-buster` and `--wait-before-cleanup` flags

## Verification Tasks

- [x] Verify backward compatibility
  - Test function call without new parameters
  - Confirm default behavior unchanged

- [x] Verify cache buster functionality
  - Test with non-empty cache buster value
  - Confirm environment variable is set in container
  - Confirm Dagger re-executes (not cached) when value changes

- [x] Verify wait functionality
  - Test with `wait_before_cleanup=5`
  - Confirm pause occurs between Phase 4 and Phase 5
  - Confirm report includes wait messages

- [x] Verify report format
  - Test without new parameters - report matches original format
  - Test with both parameters - report includes new information

## Documentation Tasks

- [x] Update CHANGELOG.md with new parameters
- [x] Update README.md if test integration examples are shown
