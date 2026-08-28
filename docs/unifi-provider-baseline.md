# UniFi Provider Baseline

This document records the reviewed `filipowm/unifi` baseline and the evidence
required before the later `ubiquiti-community/unifi` ownership migration.

## Security prerequisite

`harden-dagger-secret-and-state-handling` was archived on 2026-08-28 after the
backend credentials were rotated, affected local plan artifacts were removed,
and a controlled production plan showed zero drift without disclosing provider
or backend credentials. Its sentinel and failure-injection regression tests
remain mandatory for this baseline.

## `fix-cloudflare-token` commit review

The historical branch is five commits ahead of its merge base. Sparse commit
messages are supplemented here with the actual behavior reviewed.

| Commit | Behavior | Disposition |
|--------|----------|-------------|
| `bb75675` | Read a tunnel token directly from the Cloudflare tunnel resource | Dropped. It was superseded by the next branch commit and is unrelated to the UniFi baseline. |
| `8584466` | Added a Cloudflare tunnel-token data source | Dropped. The normalized change does not alter the released Cloudflare token-output contract without a separate review. |
| `4ec4ff9` | Registered/adopted each configured UniFi client with `allow_existing` and `skip_forget_on_destroy` | Retained as the Network 10.x unremembered-client workaround. |
| `9fbf5b0` | Kept DNS resource keys static and stopped filtering configured A/CNAME records before client registration completed | Retained so first apply can resolve client IP values after registration. |
| `44cb3a2` | Restored the client data lookup with an explicit dependency on registration | Retained as the final proven sequence: register/adopt, then read the current IP. |

The aggregate branch diff therefore is not merged wholesale. Only the final
UniFi client-registration and dependent-lookup behavior is normalized; the two
Cloudflare experiments remain outside this change.

## Authentication and provider maintenance

Production planning has already demonstrated that `filipowm/unifi` v1.0.0
authenticates with `UNIFI_API_KEY`. Updating the reviewed constraint to v1.1.x
is routine same-family maintenance and is not described as an authentication
fix. Username/password remains a compatibility path for callers that require
it.

## Verification evidence

The change records only non-secret evidence here:

- v1.0.0 production plan: 2026-08-28, API-key authenticated through the hardened
  S3-backed Dagger path; 0 add, 0 change, 0 destroy; safe artifacts and trace
  scan contained no provider, backend, or sentinel credential values
- selected provider: v1.1.0 under `~> 1.1.0`; the provider schema adds the
  optional `http_max_retries` setting and five resource types, with no removed
  provider settings, resources, or data sources used by this repository
- isolated lifecycle: 2026-08-28, run namespace
  `unifi-poc-20260828-1436.solomonhd.ai`; created 64 A and 64 CNAME records,
  provider reads found both representative record types, the second plan had
  zero drift, one A target changed from `10.255.0.10` to `10.255.255.254`, and
  Terraform destroyed all 128 resources; the controller static-DNS API then
  reported zero names matching the complete run prefix
- v1.1.0 production plan: 2026-08-28, API-key authenticated through the same
  hardened S3-backed Dagger path and identical production KCL/state; 0 add,
  0 change, 0 destroy; exported only `plan.txt` and `plan-summary.txt`, both of
  which passed credential-value scans before their temporary directory was
  removed

The v1.0.0 and v1.1.0 generated plans have identical resource-action counts.
The v1.1.0 refresh reported only sensitive output-value updates, not real
infrastructure changes. Schema fingerprints changed from
`381e6f223e872ff0466c3d1c794771c4af5bf0476ee81b148c913f68bd249544`
to `25e219e2eb8722c3d170c0faba579d6077070582994be76ab09142a6a6051840`.
The additive v1.1.0 surface consists of provider setting `http_max_retries` and
resources `unifi_ap_group`, `unifi_firewall_zone_policy_order`,
`unifi_setting_connectivity`, `unifi_setting_ether_lighting`, and
`unifi_setting_global_switch`; no data source was added or removed.

## Disposable fixture

`terraform/fixtures/unifi-provider-baseline` creates 64 A and 64 CNAME records
by default. Every name and CNAME target is confined below a caller-supplied
`unifi-poc-<run>.solomonhd.ai` namespace, and every A target is in
`10.255.0.0/16`. The fixture contains no MAC address, `sghd.io` name, or
Cloudflare resource. `update_first_record=true` changes only the first A-record
target to `10.255.255.254` for the required benign update step.

Run the fixture only through the Dagger baseline lifecycle after the operator
authorizes live UniFi DNS mutation. The lifecycle keeps state inside Dagger,
passes the API key as a secret, enforces create/read/zero-drift/update/destroy,
and verifies through the controller API that no name matching the full run
prefix remains after cleanup.

## Validation status

The provider-baseline and secret-safety suites pass (29 tests), Terraform
formatting and validation pass for both modules and the fixture, the KCL check
files pass, the Dagger function schema loads, and strict OpenSpec validation
passes. The complete legacy Python suite was also run: 74 passed, while 16
failures and 29 setup errors reproduced the removed standalone deploy-method
and stale KCL-output contracts already deferred to
`modernize-legacy-unit-test-contracts`.
