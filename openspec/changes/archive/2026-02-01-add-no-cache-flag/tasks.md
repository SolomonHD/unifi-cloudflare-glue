## 1. Implementation

### 1.1 Add time module import
- [x] Add `import time` to `src/main/main.py` with other imports
- [x] Verify import is at the top of the file

### 1.2 Add no_cache parameter to function signature
- [x] Add `no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution by auto-generating epoch timestamp")] = False` parameter
- [x] Update `cache_buster` parameter documentation to mention `--no-cache` as preferred alternative
- [x] Ensure parameter order maintains backward compatibility

### 1.3 Implement parameter validation logic
- [x] Add validation check at start of function: if `no_cache` and `cache_buster` both provided, return error
- [x] Error message: "✗ Failed: Cannot use both --no-cache and --cache-buster"

### 1.4 Implement auto-generated cache buster
- [x] Add logic: if `no_cache=True`, set `effective_cache_buster = str(int(time.time()))`
- [x] Ensure existing `cache_buster` parameter still works when `no_cache=False`
- [x] Ensure neither flag sets cache_buster to empty string (no cache invalidation)

### 1.5 Update docstring with new examples
- [x] Add `--no-cache` usage example to docstring
- [x] Update existing `--cache-buster` example to clarify advanced use
- [x] Add note about mutual exclusivity of the two flags

### 1.6 Update CHANGELOG.md
- [x] Add entry under [Unreleased] section
- [x] Describe the new `--no-cache` flag feature
- [x] Mention backward compatibility with existing `--cache-buster` parameter

## 2. Verification

### 2.1 Code Review
- [x] Verify `import time` is present
- [x] Verify `no_cache` parameter has correct type annotation and default
- [x] Verify validation logic returns proper error message
- [x] Verify epoch timestamp generation uses `int(time.time())`

### 2.2 Documentation Review
- [x] Verify docstring includes `--no-cache` example
- [x] Verify docstring explains mutual exclusivity
- [x] Verify CHANGELOG.md has entry under [Unreleased]

## 3. Post-Implementation

### 3.1 Archive Change
- [ ] Run `openspec archive add-no-cache-flag --yes` after implementation is merged
