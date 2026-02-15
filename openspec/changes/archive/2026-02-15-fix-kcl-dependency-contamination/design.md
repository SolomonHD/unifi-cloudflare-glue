## Context

The `unifi-cloudflare-glue` Dagger module generates JSON configurations by running KCL generators in containerized environments. When a consumer's KCL module declares git dependencies in `kcl.mod`, the first execution of `kcl run` triggers KCL to download those dependencies. KCL outputs git clone messages to stdout (e.g., `cloning 'https://github.com/SolomonHD/unifi-cloudflare-glue' with tag 'v0.9.2' {}`), which contaminate the YAML output stream.

This contamination causes the YAML-to-JSON conversion (via `yq`) to produce invalid JSON that includes the clone messages as string values. When Terraform attempts to use this JSON, it fails with errors like "Can't access attributes on a primitive-typed value (string)" because the expected object structure is corrupted.

The current implementation directly runs `kcl run generators/unifi.k` or `kcl run generators/cloudflare.k` without first ensuring dependencies are cached.

## Goals / Non-Goals

**Goals:**
- Ensure clean YAML/JSON output from KCL generators regardless of git dependencies
- Run `kcl mod update` before `kcl run` to pre-download dependencies
- Provide clear error messages when dependency download fails
- Maintain backward compatibility with KCL modules that don't have git dependencies

**Non-Goals:**
- Changes to KCL schemas or generator logic
- Changes to Terraform modules
- Changes to the KCL dependency resolution mechanism itself
- Modification of how KCL outputs download messages (this is upstream behavior)

## Decisions

### Decision: Run `kcl mod update` before `kcl run`

**Rationale:** KCL's `kcl mod update` command downloads all declared dependencies without executing the module. Running this before `kcl run` ensures dependencies are cached in the container before output generation begins.

**Implementation approach:**
1. After mounting the source directory, execute `kcl mod update`
2. Check exit code - if non-zero, raise `KCLGenerationError` with stderr content
3. Only proceed to `kcl run` if `kcl mod update` succeeds

**Alternatives considered:**
- **Parse and filter KCL output**: Rejected as fragile - would require maintaining a filter for all possible KCL log messages
- **Use KCL's `--quiet` flag**: Rejected - doesn't suppress dependency download messages
- **Cache dependencies at container build time**: Rejected - source directory is mounted at runtime, dependencies are project-specific

### Decision: Error handling for `kcl mod update` failures

**Rationale:** Network failures or invalid `kcl.mod` files should provide actionable error messages to help users diagnose issues.

**Implementation approach:**
- Wrap `kcl mod update` execution in try/catch
- On `dagger.ExecError`, extract exit code, stdout, and stderr
- Raise `KCLGenerationError` with formatted message including:
  - Clear indication that dependency download failed
  - Original stderr from KCL
  - Suggested remediation steps

### Decision: Apply fix to both generator functions

**Rationale:** Both `generate_unifi_config()` and `generate_cloudflare_config()` have identical patterns and are both susceptible to the same contamination issue.

**Implementation approach:**
- Modify `generate_unifi_config()` at line ~140
- Modify `generate_cloudflare_config()` at line ~1725
- Use consistent error handling patterns in both functions

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Increased execution time on first run | Acceptable trade-off - dependency download happens once per container, cached on subsequent runs |
| `kcl mod update` failing on modules without dependencies | Tested - `kcl mod update` succeeds quickly on modules with no external dependencies |
| Network timeouts during dependency download | Error handling will catch and report with clear message suggesting retry |
| Additional container state from dependency cache | Negligible - KCL dependencies are stored in module's `.kcl` directory which is ephemeral with the container |

## Migration Plan

No migration steps required. This is a backward-compatible bugfix:
- Existing KCL modules without git dependencies continue to work
- Existing KCL modules with git dependencies will now produce valid JSON
- No changes to user-facing APIs or function signatures
- No changes to generated output format (only fixes corruption)

## Open Questions

None. The fix is straightforward and well-understood.
