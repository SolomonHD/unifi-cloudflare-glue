## Why

KCL v0.12.x has a SIGSEGV bug in its native Rust/CGO execution layer that crashes when running any `.k` file other than the module entry point (`main.k`) from a KCL module with git dependencies. The Dagger module currently invokes `kcl run generators/unifi.k` and `kcl run generators/cloudflare.k`, which triggers this crash in consumer projects. Switching to `kcl run main.k` with `yq` extraction avoids the bug without waiting for an upstream fix.

## What Changes

- **Replace KCL generator invocation**: Both `generate_unifi_config()` and `generate_cloudflare_config()` switch from running individual generator files (`generators/unifi.k`, `generators/cloudflare.k`) to running `main.k` and extracting output sections with `yq`.
- **New extraction pipeline**: `kcl run main.k` produces full YAML → write to temp file → `yq eval '.unifi_output'` or `yq eval '.cf_output'` → convert to JSON with `yq eval -o=json`.
- **Update file-existence checks**: Replace checks for `generators/unifi.k` and `generators/cloudflare.k` with a single check for `main.k`.
- **Update error messages**: All error hints and diagnostic messages reference `main.k` instead of `generators/*.k`.
- **Consumer contract**: Consumer's `main.k` must export `unifi_output` and `cf_output` as public variables (most already do).
- **Documentation updates**: Examples and docs reflect the `main.k`-based invocation pattern.
- The `generators/` directory in consumer projects becomes optional/dead code. **Not a breaking change** — existing consumers whose `main.k` already exports the expected variables continue to work without modification.

## Capabilities

### New Capabilities
- `kcl-main-entry-invocation`: Dagger module runs `kcl run main.k` and extracts per-provider output via `yq`, replacing direct generator file execution to avoid KCL v0.12.x SIGSEGV crashes.

### Modified Capabilities
- `config-generation`: The underlying invocation mechanism changes from running separate generator files to running `main.k` with `yq` extraction. The output contract (JSON format fed to Terraform) remains identical.

## Impact

- **`src/main/main.py`**: `generate_unifi_config()` and `generate_cloudflare_config()` — core invocation logic, file-existence checks, error messages, and output parsing all change.
- **Container tooling**: The Dagger container must include `yq` (likely already present; verify).
- **Consumer projects**: No changes required if `main.k` exports `unifi_output` and `cf_output`. Projects relying solely on `generators/*.k` without a `main.k` entry point will need to add one.
- **Tests**: Unit tests for generator output (`tests/unit/test_generator_output.py`) may need updated fixture paths.
- **Documentation**: `README.md`, `kcl_README.md`, `docs/dagger-reference.md`, example READMEs, and troubleshooting guide need error-message and invocation-pattern updates.
