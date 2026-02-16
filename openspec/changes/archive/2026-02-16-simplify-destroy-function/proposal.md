## Why

The `destroy()` function currently uses separate Terraform modules for UniFi DNS and Cloudflare Tunnel management. After the introduction of the combined `terraform/modules/glue/` module (Prompt 10) and the simplification of `deploy()`/`plan()` (Prompts 11-12), the `destroy()` function needs to be updated for consistency. Additionally, users need the ability to selectively destroy only UniFi DNS records or only Cloudflare Tunnel configurations, rather than always destroying both components.

## What Changes

- Update `destroy()` function in `src/main/main.py` to use the combined `terraform/modules/glue/` module
- Add `--unifi-only` boolean flag to destroy only UniFi DNS configurations
- Add `--cloudflare-only` boolean flag to destroy only Cloudflare Tunnel configurations
- Add validation to prevent both flags being set simultaneously
- Generate only the necessary KCL config files based on the selected destroy mode
- Use Terraform `-target` option for selective component destruction
- Return clear status messages indicating what components were destroyed

## Capabilities

### New Capabilities
- `selective-destroy`: Support for destroying only UniFi DNS or only Cloudflare Tunnel components via command-line flags

### Modified Capabilities
- None (this is a pure implementation change to existing destroy functionality)

## Impact

- **File**: `src/main/main.py` - The `destroy()` function implementation
- **CLI Interface**: New `--unifi-only` and `--cloudflare-only` flags for the `destroy` command
- **Terraform Behavior**: Uses `-target` option for selective destruction when flags are provided
- **KCL Generation**: Conditionally generates only needed config files based on flags
- **State Management**: Maintains proper state handling for partial destroys
