## Why

When using the `deploy()` function with persistent local state (`--state-dir`), both the UniFi DNS and Cloudflare Tunnel deployments share the same state file, causing provider conflicts. The Cloudflare deployment tries to initialize the UniFi provider because it sees UniFi resources in the shared state, and vice versa. This creates a poor user experience requiring separate state directories or manual provider configuration.

## What Changes

- Create new `terraform/modules/glue/` directory containing a combined Terraform module
- Create `main.tf` that calls both `unifi-dns` and `cloudflare-tunnel` sub-modules with explicit dependency
- Create `variables.tf` that combines all inputs from both modules (config files, provider credentials)
- Create `outputs.tf` that exposes all outputs from both sub-modules
- Create `versions.tf` with both `filipowm/unifi` and `cloudflare/cloudflare` provider requirements
- Create `README.md` with module documentation and usage examples
- The combined module uses relative paths (`../unifi-dns/`, `../cloudflare-tunnel/`) for module sources
- Explicit `depends_on` ensures UniFi DNS is applied before Cloudflare Tunnel

## Capabilities

### New Capabilities
- `combined-terraform-module`: A wrapper module that combines both UniFi DNS and Cloudflare Tunnel modules into a single atomic deployment, eliminating provider conflicts when using shared state.

### Modified Capabilities
- None - existing modules remain unchanged

## Impact

- **New Directory**: `terraform/modules/glue/` will be created
- **No Breaking Changes**: Existing `unifi-dns` and `cloudflare-tunnel` modules are not modified
- **Provider Configuration**: Both UniFi and Cloudflare providers are configured at the root module level
- **State Management**: Single state file contains both UniFi and Cloudflare resources without provider conflicts
- **Dependency Chain**: Cloudflare Tunnel deployment waits for UniFi DNS completion
- **Documentation**: New README explains when to use the combined module vs individual modules
