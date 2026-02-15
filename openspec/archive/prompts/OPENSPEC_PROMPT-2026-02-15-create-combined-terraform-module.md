# OpenSpec Prompt: Create Combined Terraform Wrapper Module

## Context

The project currently has two separate Terraform modules:
- `terraform/modules/unifi-dns/` - Manages UniFi DNS records
- `terraform/modules/cloudflare-tunnel/` - Manages Cloudflare Tunnels and edge DNS

When using the `deploy()` function with persistent local state (`--state-dir`), both deployments share the same state file, causing provider conflicts. The Cloudflare deployment tries to initialize the UniFi provider because it sees UniFi resources in the shared state.

## Goal

Create a new combined Terraform module at `terraform/modules/glue/` that wraps both existing modules and allows a single `terraform apply` to deploy both UniFi DNS and Cloudflare Tunnels atomically.

## Scope

### In Scope
- Create `terraform/modules/glue/` directory
- Create `main.tf` that calls both sub-modules with proper dependency
- Create `variables.tf` that combines inputs from both modules
- Create `outputs.tf` that exposes outputs from both modules
- Create `versions.tf` with both provider requirements
- Create `README.md` with module documentation

### Out of Scope
- Modifying existing `unifi-dns` or `cloudflare-tunnel` modules
- Dagger/Python code changes (handled in separate prompts)

## Desired Behavior

The combined module should:
1. Accept both UniFi and Cloudflare configuration files as inputs
2. Accept all provider credentials (UniFi URL, API key, Cloudflare token, etc.)
3. Call the `unifi-dns` module first
4. Call the `cloudflare-tunnel` module with explicit `depends_on` to ensure UniFi completes first
5. Expose all outputs from both modules

## Constraints & Assumptions

- The existing modules at `../unifi-dns/` and `../cloudflare-tunnel/` should not be modified
- Use relative paths (`../unifi-dns/`, `../cloudflare-tunnel/`) for module sources
- Provider configurations must be defined at the root module level
- The module must support both `config` (object) and `config_file` (path) input patterns

## Acceptance Criteria

1. `terraform/modules/glue/` directory exists with all required files
2. `terraform init` succeeds in the glue module directory
3. `terraform validate` shows no errors
4. Module properly declares both `filipowm/unifi` and `cloudflare/cloudflare` providers
5. Module has explicit dependency: `cloudflare-tunnel` depends on `unifi-dns`
6. All outputs from both sub-modules are exposed

## Files to Create

| File | Purpose |
|------|---------|
| `terraform/modules/glue/main.tf` | Module calls with dependency |
| `terraform/modules/glue/variables.tf` | All input variables |
| `terraform/modules/glue/outputs.tf` | Combined outputs |
| `terraform/modules/glue/versions.tf` | Provider requirements |
| `terraform/modules/glue/README.md` | Module documentation |

## Example Structure

```hcl
# main.tf
provider "unifi" {
  api_url = var.unifi_url
  api_key = var.unifi_api_key
  # ... other provider config
}

provider "cloudflare" {
  api_token = var.cloudflare_token
}

module "unifi_dns" {
  source = "../unifi-dns"
  config_file = var.unifi_config_file
  # ... pass variables
}

module "cloudflare_tunnel" {
  source = "../cloudflare-tunnel"
  config_file = var.cloudflare_config_file
  # ... pass variables
  
  depends_on = [module.unifi_dns]
}
```

## Dependencies

None - this is the first change in the sequence.
