# OpenSpec Prompt: Update Documentation for Simplified API

## Context

The Dagger module API has been simplified:
- `deploy()`, `plan()`, `destroy()` now use the combined Terraform module
- `deploy_unifi()` and `deploy_cloudflare()` have been removed
- New `--unifi-only` and `--cloudflare-only` flags added for selective operations

## Goal

Update all documentation to reflect the simplified API.

## Scope

### In Scope
- Update `README.md` Quick Start and examples
- Update `docs/dagger-reference.md` with new function signatures
- Update `docs/deployment-patterns.md` with simplified workflow
- Remove references to `deploy_unifi` and `deploy_cloudflare`

### Out of Scope
- Changes to example projects (may be updated separately)
- Terraform module documentation (handled in Prompt 10)

## Documentation Changes

### README.md Updates

**Quick Start Section:**
Replace separate deployment examples with unified approach:

```markdown
## Quick Start

Deploy both UniFi DNS and Cloudflare Tunnels:

\`\`\`bash
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
\`\`\`

### Deploy Only One Component

UniFi DNS only:
\`\`\`bash
dagger call deploy \
    --kcl-source=./kcl \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-only
\`\`\`

Cloudflare only:
\`\`\`bash
dagger call deploy \
    --kcl-source=./kcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com \
    --cloudflare-only
\`\`\`
```

### docs/dagger-reference.md Updates

Update the Functions section to show:

| Function | Description |
|----------|-------------|
| `deploy` | Deploy UniFi DNS and/or Cloudflare Tunnels |
| `plan` | Generate execution plan |
| `destroy` | Destroy resources |

**Remove sections for:**
- `deploy_unifi`
- `deploy_cloudflare`

**Add to each function:**
- `--unifi-only` flag description
- `--cloudflare-only` flag description
- Mutual exclusion note (cannot use both)

### docs/deployment-patterns.md Updates

Update "Full Deployment" pattern:
- Remove note about provider conflicts (now resolved)
- Update example commands to use unified `deploy`
- Explain the `--unifi-only` and `--cloudflare-only` flags

## Acceptance Criteria

1. `README.md` shows unified deployment as primary example
2. No references to removed functions (`deploy_unifi`, `deploy_cloudflare`)
3. All examples use `--unifi-only` and `--cloudflare-only` flags correctly
4. `docs/dagger-reference.md` has updated function signatures
5. Documentation explains that combined module solves provider conflicts

## Files to Modify

| File | Changes |
|------|---------|
| `README.md` | Update Quick Start, remove old function refs |
| `docs/dagger-reference.md` | Update function docs, remove deleted functions |
| `docs/deployment-patterns.md` | Update patterns for simplified API |

## Dependencies

- Prompt 11: `deploy()` simplification must be complete
- Prompt 12: `plan()` simplification must be complete
- Prompt 13: `destroy()` simplification must be complete
