## Why

The `unifi-cloudflare-glue` Dagger module embeds Terraform modules at `terraform/modules/unifi-dns/` and `terraform/modules/cloudflare-tunnel/`. These modules are part of the repository and must be accessible when the Dagger module is called from external projects (e.g., `portainer-docker-compose`).

Currently, multiple functions incorrectly use `dagger.dag.directory().directory("terraform/modules/...")` which resolves to the **calling project's** directory instead of the module's own source. This causes "module not found" failures when the module is used as a dependency from external projects.

## What Changes

- **Bug Fix**: Replace all instances of `dagger.dag.directory().directory("terraform/modules/...")` with `dagger.dag.current_module().source().directory("terraform/modules/...")` in [`src/main/main.py`](src/main/main.py)
- **Affected Functions**: [`deploy_unifi()`](src/main/main.py:406), [`deploy_cloudflare()`](src/main/main.py:565), [`plan()`](src/main/main.py:1094), [`destroy()`](src/main/main.py:1473), [`test_integration()`](src/main/main.py:2204), [`get_tunnel_secrets()`](src/main/main.py:2805)
- **Documentation**: Update CHANGELOG.md with bug fix entry
- **Versioning**: Bump patch version in VERSION file

## Capabilities

### New Capabilities
<!-- This is a bug fix with no new capabilities - existing behavior is corrected, not added -->
- `terraform-module-loading`: Correctly loads embedded Terraform modules from the module's own source directory when called from external projects

### Modified Capabilities
<!-- No existing spec-level requirements are changing - this is purely an implementation fix -->
- None

## Impact

- **Code**: 8+ locations in [`src/main/main.py`](src/main/main.py) requiring the pattern change
- **API**: No changes to function signatures or public APIs (backwards compatible)
- **Dependencies**: No new dependencies required
- **Behavior**: Module now correctly resolves Terraform module paths when called externally

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
