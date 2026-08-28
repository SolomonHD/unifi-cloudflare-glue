## 1. Prerequisite and Branch Review

- [x] 1.1 Confirm `harden-dagger-secret-and-state-handling` is complete, exposed credentials are addressed, and the hardened plan/integration paths pass sentinel-secret tests
- [x] 1.2 Review every commit and the aggregate diff from `main` through `fix-cloudflare-token`, documenting the behavior retained or dropped
- [x] 1.3 Integrate the reviewed Network 10.x `unifi_user` registration plus dependent lookup behavior onto a new implementation feature branch
- [x] 1.4 Add unit/static tests proving `allow_existing`, `skip_forget_on_destroy`, normalized MAC keys, and the explicit data-source dependency are preserved

## 2. Current Provider Maintenance Update

- [x] 2.1 Run the hardened production Dagger plan with the existing v1.0.0 selection and record a secret-free 0-add/0-change/0-destroy baseline
- [x] 2.2 Update all UniFi module constraints to `~> 1.1.0` and verify Terraform selects the reviewed v1.1.x release
- [x] 2.3 Compare provider schemas and generated plans to identify any v1.1 state, default, or API behavior changes
- [x] 2.4 Update documentation and changelog to describe the update as maintenance and distinguish it from the Network 10.x client-registration workaround

## 3. Isolated solomonhd.ai Baseline Fixture

- [x] 3.1 Add a disposable Terraform fixture that generates a production-scale representative mix of A and CNAME records beneath a unique `unifi-poc-<run>.solomonhd.ai` namespace
- [x] 3.2 Ensure fixture inputs use benign private-address targets and no production-managed MAC address, `sghd.io` name, or Cloudflare Tunnel resource
- [x] 3.3 Run authorized create, API/read validation, second zero-drift plan, one benign update, destroy, and API absence verification through the hardened lifecycle
- [x] 3.4 Confirm cleanup leaves no run-prefixed DNS records or test state and record non-secret evidence

## 4. Production Verification and Publication

- [x] 4.1 Re-run the production API-key-authenticated Dagger plan with v1.1.x and require 0 add, 0 change, and 0 destroy
- [x] 4.2 Run Python tests, Terraform formatting/validation, KCL schema/generator tests, Dagger module checks, and secret-disclosure scans
- [ ] 4.3 Publish the reviewed normalized revision on `main` as a semantic release tag or immutable commit
- [ ] 4.4 In `portainer-docker-compose`, atomically update `dagger.json` and `kcl/kcl.mod` from `fix-cloudflare-token` to the same published revision
- [ ] 4.5 Correct the downstream credential-audit and `rotate-high-risk-credentials` artifacts to state that glue already authenticates by API key and that v1.1 is maintenance
- [ ] 4.6 Run the consumer pre-flight plan from the updated pin and require zero production drift
- [x] 4.7 Run `openspec validate normalize-current-unifi-provider-baseline --strict` and `git diff --check`
