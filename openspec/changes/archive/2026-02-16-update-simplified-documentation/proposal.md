## Why

The Dagger module API has been simplified to use a unified Terraform module approach, combining UniFi DNS and Cloudflare Tunnel deployments into single functions. The separate `deploy_unifi()` and `deploy_cloudflare()` functions have been removed in favor of selective flags (`--unifi-only`, `--cloudflare-only`). Documentation must be updated to reflect this simplified API and prevent user confusion.

## What Changes

- **Update README.md**: Replace separate deployment examples with unified approach using `deploy`, `plan`, and `destroy` functions
- **Update docs/dagger-reference.md**: 
  - Document new unified function signatures
  - Add `--unifi-only` and `--cloudflare-only` flag documentation
  - Remove references to deleted `deploy_unifi()` and `deploy_cloudflare()` functions
- **Update docs/deployment-patterns.md**: 
  - Update "Full Deployment" pattern to use unified commands
  - Remove provider conflict warnings (now resolved by combined module)
  - Document selective deployment patterns using new flags

## Capabilities

### New Capabilities
- `readme-quick-start-update`: Update README.md Quick Start section with unified deployment examples
- `dagger-reference-update`: Update docs/dagger-reference.md with new function signatures and flags
- `deployment-patterns-update`: Update docs/deployment-patterns.md with simplified workflow documentation

### Modified Capabilities
- None (this is a documentation-only change)

## Impact

- **User-facing documentation**: README.md, docs/dagger-reference.md, docs/deployment-patterns.md
- **User experience**: Clearer, simpler API documentation reduces confusion
- **Breaking changes documented**: Users migrating from separate functions need guidance on new unified approach
