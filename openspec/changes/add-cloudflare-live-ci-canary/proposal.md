## Why

Offline tests cannot prove that the current Cloudflare provider schema, zone-scoped token, public authoritative DNS, and cleanup behavior work together. The newly available `solomonhd.ai` zone provides a bounded public sandbox for an unattended DNS-only canary after the Dagger secret and provider work has stabilized.

## What Changes

- Sequence implementation after the three preceding changes, with `harden-dagger-secret-and-state-handling` as the mandatory security prerequisite.
- Add a dedicated Terraform/Dagger DNS canary that creates uniquely named records beneath `ci.solomonhd.ai`, validates them through the Cloudflare API and public DNS, updates one value, destroys them, and verifies authoritative absence.
- Add a GitHub Actions workflow for trusted `main` pushes, scheduled runs, and manual dispatch; do not expose secrets to pull-request or fork-controlled code.
- Use a Cloudflare API token restricted to Zone Read and DNS Edit for only `solomonhd.ai`.
- Keep Cloudflare Tunnel creation/configuration out of hosted CI because Tunnel Edit is account-scoped and could affect production tunnels; retain full Tunnel integration as an explicitly authorized local Dagger test.
- Add strict concurrency, timeout, least-privilege GitHub permissions, guaranteed cleanup, residual-resource failure reporting, and a scheduled stale-record janitor.
- Treat each test object as a random subdomain/record inside the existing zone, not as a newly registered domain or Cloudflare zone.

## Capabilities

### New Capabilities
- `cloudflare-live-ci-canary`: Defines trusted workflow triggers, zone-scoped credentials, ephemeral DNS CRUD validation, cleanup verification, janitor behavior, and the boundary between hosted DNS testing and local Tunnel testing.

### Modified Capabilities

None.

## Impact

- Adds GitHub Actions workflow(s), a DNS-only Terraform/Dagger fixture, test scripts or functions, documentation, and narrowly scoped repository/environment secrets.
- Mutates only run-prefixed DNS records inside `solomonhd.ai`; it does not modify production `sghd.io`, UniFi, Cloudflare Tunnels, or application routes.
- Introduces small recurring Cloudflare API/DNS traffic and requires operational monitoring for failed cleanup.
- Full Tunnel integration remains available locally through the hardened integration path with explicitly supplied account-level credentials.
