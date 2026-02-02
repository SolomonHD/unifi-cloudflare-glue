# Change: Fix State File Mounting in Cleanup Phase

## Why

The cleanup phase incorrectly mounts state directories using `.with_directory("/module", state_dir)`, which overwrites the entire `/module` directory (containing Terraform module files like `main.tf`, `variables.tf`) with just the state directory. This causes `terraform destroy` to fail because Terraform has the state file but no module files.

## What Changes

- Fix Cloudflare state mounting logic (around line 1368) to use `.with_file()` instead of `.with_directory()`
- Fix UniFi state mounting logic (around line 1457) to use `.with_file()` instead of `.with_directory()`
- Extract the `terraform.tfstate` file from the state directory before mounting
- Add success/failure logging for state file mounting operations
- Wrap state mounting in try/except blocks for graceful error handling

## Impact

- Affected specs: `cleanup`, `integration-testing`
- Affected code: `src/main/main.py` (lines ~1368-1371 and ~1457-1460)
- **BREAKING:** None - this is a bug fix that restores intended behavior
