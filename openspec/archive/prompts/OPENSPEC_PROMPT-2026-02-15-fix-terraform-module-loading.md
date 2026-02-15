# OpenSpec Prompt: Fix Embedded Terraform Module Loading

## Context

The `unifi-cloudflare-glue` Dagger module embeds Terraform modules at:
- `terraform/modules/unifi-dns/`
- `terraform/modules/cloudflare-tunnel/`

These modules are part of the repository and should be accessible when the Dagger module is called from external projects (e.g., `portainer-docker-compose`).

## Current Bug

Multiple functions incorrectly use `dagger.dag.directory().directory("terraform/modules/...")` which resolves to the **calling project's** directory, not the module's own source. This causes failures when the module is used as a dependency.

### Affected Functions

| Function | File | Line(s) | Module Path |
|----------|------|---------|-------------|
| `deploy_unifi()` | src/main/main.py | 406 | `terraform/modules/unifi-dns` |
| `deploy_cloudflare()` | src/main/main.py | 565 | `terraform/modules/cloudflare-tunnel` |
| `plan()` (UniFi) | src/main/main.py | 1094 | `terraform/modules/unifi-dns` |
| `plan()` (Cloudflare) | src/main/main.py | 1189 | `terraform/modules/cloudflare-tunnel` |
| `destroy()` (Cloudflare) | src/main/main.py | 1473 | `terraform/modules/cloudflare-tunnel` |
| `destroy()` (UniFi) | src/main/main.py | 1567 | `terraform/modules/unifi-dns` |
| `test_integration()` (fallback) | src/main/main.py | 2204 | `terraform/modules/unifi-dns` |
| `get_tunnel_secrets()` (fallback) | src/main/main.py | 2805 | `terraform/modules/cloudflare-tunnel` |

## Goal

Fix all instances where embedded Terraform modules are loaded to use `dagger.dag.current_module().source().directory()` instead of `dagger.dag.directory().directory()`.

## Scope

### In Scope

1. **src/main/main.py** - Update all affected functions:
   - Replace `dagger.dag.directory().directory("terraform/modules/unifi-dns")` with `dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")`
   - Replace `dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")` with `dagger.dag.current_module().source().directory("terraform/modules/cloudflare-tunnel")`

2. **Error handling** - Keep existing try/except blocks but ensure they catch the correct exceptions

3. **Consistency** - Ensure all functions use the same pattern for module loading

### Out of Scope

- Changes to the Terraform module contents themselves
- Changes to function signatures or APIs
- Changes to how the `source` parameter is used for KCL/config files
- Adding new features or functionality

## Desired Behavior

When the module is called from an external project (e.g., `portainer-docker-compose`), the embedded Terraform modules should be correctly loaded from the `unifi-cloudflare-glue` module's own source directory, not from the calling project.

### Before (Broken)

```python
# In portainer-docker-compose, calling deploy_unifi():
tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
# Looks for: portainer-docker-compose/terraform/modules/unifi-dns (DOESN'T EXIST)
```

### After (Fixed)

```python
# In portainer-docker-compose, calling deploy_unifi():
tf_module = dagger.dag.current_module().source().directory("terraform/modules/unifi-dns")
# Looks for: unifi-cloudflare-glue/terraform/modules/unifi-dns (EXISTS ✓)
```

## Constraints & Assumptions

1. **Dagger API**: `dagger.dag.current_module().source()` returns the module's source directory
2. **Path structure**: Terraform modules are at `terraform/modules/{unifi-dns,cloudflare-tunnel}` relative to module root
3. **Backwards compatibility**: The fix should not change function signatures or behavior from caller's perspective
4. **Test coverage**: Manual verification required - install module in a test project and verify functions work

## Acceptance Criteria

- [ ] All instances of `dagger.dag.directory().directory("terraform/modules/...")` are replaced with `dagger.dag.current_module().source().directory("terraform/modules/...")`
- [ ] Functions affected: `deploy_unifi()`, `deploy_cloudflare()`, `plan()`, `destroy()`, `test_integration()`, `get_tunnel_secrets()`
- [ ] No changes to function signatures or public APIs
- [ ] Error handling preserved (try/except blocks remain functional)
- [ ] CHANGELOG.md updated with bug fix entry
- [ ] Version bumped in VERSION file (patch increment)

## Files To Modify

| File | Changes |
|------|---------|
| `src/main/main.py` | Update 8+ locations where Terraform modules are loaded |
| `CHANGELOG.md` | Add bug fix entry |
| `VERSION` | Bump patch version |

## Dependencies

None - this is a standalone bug fix with no dependencies on other changes.

## Testing Notes

To verify the fix:

```bash
# From an external project that uses the module
cd /path/to/portainer-docker-compose

# Try to call a function that uses Terraform modules
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@<fixed-version> deploy-unifi \
    --source=. \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY
```

The command should succeed (or fail for other reasons like missing unifi.json), but NOT fail with "module not found" errors.
