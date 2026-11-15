## Why

Offline tests cannot prove that the Cloudflare provider, zone-scoped token, public DNS, and cleanup work together. The existing `solomonhd.ai` sandbox supports a DNS-only Actions pilot after the repaired test baseline and Dagger execution foundation, with durable protected recovery rather than dependence on a dying runner.

## What Changes

- Depend on `modernize-legacy-unit-test-contracts` and accepted `modernize-dagger-execution-contracts` security/execution contracts, retaining existing hardening evidence; do not depend on the UniFi provider migration.
- Add one normal Dagger entry point owning the TXT/unproxied-CNAME create, API/public-DNS validation, update, zero-drift plan, destroy, and exact-name absence verification lifecycle below `ci.solomonhd.ai`.
- Add a thin GitHub Actions adapter for exact selected CLI setup, trusted `main` pushes/schedule/manual refs, least permissions, runtime secret handoff, and sanitized reporting. No Terraform lifecycle logic belongs in workflow YAML.
- Use a Cloudflare API token restricted to Zone Read and DNS Edit for only `solomonhd.ai`.
- Keep Cloudflare Tunnel creation/configuration out of hosted CI because Tunnel Edit is account-scoped and could affect production tunnels; retain full Tunnel integration as an explicitly authorized local Dagger test.
- Attempt cleanup within Dagger for handled failures, report verified/failed/unknown outcomes accurately, and provide an explicitly authorized separate reconciliation entry point and guarded stale-record janitor. Hard cancellation cannot guarantee cleanup.
- Use a dedicated Wasabi sandbox prefix for isolated per-run state and run ledgers, separate from production, with scoped CI credentials supplied only at runtime. Record intent before possible effects and qualify exact backend conditional-write/lock semantics and active-run fencing before live mutation.
- Treat each test object as a random subdomain/record inside the existing zone, not as a newly registered domain or Cloudflare zone.

## Capabilities

### New Capabilities
- `cloudflare-live-ci-canary`: Defines trusted thin-adapter CI, Dagger-owned DNS lifecycle, protected durable recovery, fencing, cleanup/reconciliation, janitor behavior, and the hosted-DNS/local-Tunnel boundary.

### Modified Capabilities

None.

## Impact

- Adds a thin GitHub Actions workflow, DNS-only Terraform/Dagger fixture, recovery interface, documentation, and narrowly scoped runtime Cloudflare/Wasabi secret bindings. Planning approval does not provision or access Wasabi or GitHub environments.
- Mutates only run-prefixed DNS records inside `solomonhd.ai`; it does not modify production `sghd.io`, UniFi, Cloudflare Tunnels, or application routes.
- Introduces small recurring Cloudflare API/DNS traffic and requires operational monitoring for failed cleanup.
- Full Tunnel integration remains available locally through the hardened integration path with explicitly supplied account-level credentials.
- Excludes Dagger Cloud and migrations of other CI templates. The exact CLI/engine/Python SDK tuple is selected by the parent's early beta-first qualification with a recorded 0.21.11 fallback decision, not guessed here.
