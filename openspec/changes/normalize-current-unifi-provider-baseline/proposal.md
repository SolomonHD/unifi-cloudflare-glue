## Why

The deployed `fix-cloudflare-token` dependency already completes an API-key-authenticated, zero-drift plan with `filipowm/unifi` v1.0.0, contradicting the recorded assumption that the provider requires username/password. Before changing provider families, the working Network 10.x client-registration workaround and current behavior need to be normalized on `main`, updated as routine maintenance, and captured as a reproducible baseline.

## What Changes

- Depend on completion of `harden-dagger-secret-and-state-handling` before any additional live execution.
- Preserve and review the `fix-cloudflare-token` branch changes that register unremembered clients before lookup, resolving the Network 10.x `UnknownUser` behavior.
- Update the existing `filipowm/unifi` constraint and lock selection from v1.0.0 to v1.1.0 as maintenance, without representing it as an authentication fix.
- Establish API-key authentication as the tested primary path while retaining username/password compatibility for callers that still need it.
- Add a disposable `solomonhd.ai` UniFi DNS fixture that exercises representative A/CNAME CRUD without taking ownership of production client MAC addresses.
- Publish the normalized repository state from `main` and coordinate the downstream Dagger/KCL dependency away from `fix-cloudflare-token` to a reviewed release or commit on `main`.
- Correct the downstream credential-rotation note that currently says the provider is too old to use API keys.

## Capabilities

### New Capabilities
- `unifi-provider-baseline`: Defines the verified legacy-provider version, API-key path, Network 10.x workaround, zero-drift gate, and disposable baseline fixture.

### Modified Capabilities
- `provider-upgrade`: Adds the maintenance policy and verification requirements for upgrading the current UniFi provider within the `filipowm/unifi` family.
- `module-consumption`: Requires production Dagger/KCL consumers to pin a reviewed `main` commit or release rather than the historical feature branch.

## Impact

- Affects the UniFi Terraform modules, provider lock selection, tests, changelog/release metadata, and documentation.
- Preserves the current resource types and state schema; this change does not migrate to `ubiquiti-community/unifi`.
- Requires read/write access to create and remove only the explicitly authorized disposable UniFi DNS fixture; production verification remains plan-only and must show zero changes.
- Requires a coordinated follow-up commit in `portainer-docker-compose` to update `dagger.json`, `kcl/kcl.mod`, and the deferred credential-rotation note after the normalized revision is published.
