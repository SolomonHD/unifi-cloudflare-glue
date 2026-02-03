## Why

After successful Cloudflare tunnel deployment, users need to retrieve tunnel tokens to configure `cloudflared` on their devices. Currently, deployment functions ([`deploy_cloudflare()`](../../src/main/main.py:422-571) and [`deploy()`](../../src/main/main.py:574-742)) return success messages without explaining this critical next step, forcing users to figure out token retrieval independently. Adding clear post-deployment guidance will improve user experience by completing the deployment-to-configuration workflow.

## What Changes

- Modify [`deploy_cloudflare()`](../../src/main/main.py:422-571) success message to include credential retrieval guidance
- Modify [`deploy()`](../../src/main/main.py:574-742) final summary to include guidance (only when Cloudflare deployment succeeds)
- Add multi-line formatted section with:
  - Context about configuring `cloudflared`
  - Terraform output command option
  - Dagger [`get_tunnel_secrets()`](../../src/main/main.py:28) command option with actual deployment parameters
  - Link to example documentation
- Preserve existing success indicators and backend information
- Update unit tests to expect new message format

## Capabilities

### New Capabilities
- `deployment-guidance`: Post-deployment success messages include actionable next-step instructions for retrieving tunnel credentials

### Modified Capabilities
<!-- No existing spec-level requirements are changing, only implementation details within deployment functions -->

## Impact

- **Modified functions**: [`deploy_cloudflare()`](../../src/main/main.py:422-571) and [`deploy()`](../../src/main/main.py:574-742)
- **Test updates**: Unit tests that validate success message content
- **Dependencies**: Requires [`get_tunnel_secrets()`](../../src/main/main.py:28) function from previous change (prompt 01)
- **User experience**: Users will know immediately how to retrieve tunnel tokens after successful deployment
- **Documentation**: Example guidance links to existing [`examples/homelab-media-stack/README.md`](../../examples/homelab-media-stack/README.md)
