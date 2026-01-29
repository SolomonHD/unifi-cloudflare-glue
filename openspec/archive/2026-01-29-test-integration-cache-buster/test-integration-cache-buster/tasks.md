# Tasks: Add cache_buster and wait_before_cleanup to test_integration

## Implementation Tasks

- [x] Add `cache_buster` parameter to `test_integration` function signature
  - Type: `str`
  - Default: `""`
  - Properly annotated with `Annotated[str, Doc("...")]`

- [x] Add `wait_before_cleanup` parameter to `test_integration` function signature
  - Type: `int`
  - Default: `0`
  - Properly annotated with `Annotated[int, Doc("...")]`

- [x] Integrate `cache_buster` into container execution
  - Add as environment variable `CACHE_BUSTER` when non-empty
  - Location: Phase 1, base_container setup

- [x] Implement wait logic for `wait_before_cleanup`
  - Add async sleep between Phase 4 (validation) and Phase 5 (cleanup)
  - Log wait duration in test report

- [x] Update test report output
  - Include cache_buster value in report when non-empty
  - Include wait_before_cleanup duration when > 0

- [x] Update function docstring
  - Document both new parameters
  - Add example usage showing cache_buster
  - Add example usage showing wait_before_cleanup

- [x] Verify backward compatibility
  - Existing calls without new parameters continue to work
  - Defaults maintain existing behavior

## Verification

- [x] Code review confirms all acceptance criteria met
- [x] CHANGELOG.md updated with changes
- [x] README.md updated with usage examples
