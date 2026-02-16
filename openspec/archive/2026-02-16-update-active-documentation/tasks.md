## 1. Update README.md

- [x] 1.1 Search for all `--no-cache` occurrences in README.md
- [x] 1.2 Replace deployment examples using `--no-cache` with `--cache-buster=$(date +%s)`
- [x] 1.3 Replace quickstart examples using `--no-cache` with `--cache-buster=$(date +%s)`
- [x] 1.4 Verify no `--no-cache` references remain in README.md

## 2. Update docs/dagger-reference.md

- [x] 2.1 Search for all `--no-cache` occurrences in docs/dagger-reference.md
- [x] 2.2 Update parameter tables to remove `--no-cache` row
- [x] 2.3 Update `--cache-buster` parameter description to "Unique value to bypass cache (use `$(date +%s)`)"
- [x] 2.4 Replace all command examples using `--no-cache` with `--cache-buster=$(date +%s)`
- [x] 2.5 Verify no `--no-cache` references remain in docs/dagger-reference.md

## 3. Update docs/deployment-patterns.md

- [x] 3.1 Search for all `--no-cache` occurrences in docs/deployment-patterns.md
- [x] 3.2 Update cache control section to explain Dagger's function-level caching
- [x] 3.3 Add explanation that `$(date +%s)` provides unique epoch timestamp
- [x] 3.4 Replace examples using `--no-cache` with `--cache-buster=$(date +%s)`
- [x] 3.5 Verify no `--no-cache` references remain in docs/deployment-patterns.md

## 4. Validation

- [x] 4.1 Run `grep -r "no.cache" README.md docs/*.md` to ensure no references remain
- [x] 4.2 Verify all updated examples are syntactically correct bash commands
- [x] 4.3 Review changes for consistency across all files
