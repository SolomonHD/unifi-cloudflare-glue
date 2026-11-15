# Execution Contracts

This is the supported caller migration for `modernize-dagger-execution-contracts`.
It documents the current interface, not completion of remaining runtime,
consumer or production acceptance. The [runtime receipt](dagger-runtime-qualification.md)
owns exact evidence; [offline verification](offline-verification.md) owns the
credential-free check contract. `README.old.md` is not normative guidance.

## Runtime And Inputs

Use the exact beta27 CLI and immutable engine in the runtime receipt:

```bash
bash scripts/dagger-qualified.sh api call -m . version --source=.
```

The wrapper checks the qualified CLI checksum and supplies the pinned global
`--engine` option before `api call`; `-m .` selects this module. Set `DAGGER_BIN`
only to the separately bootstrapped, checksum-matching Linux/amd64 binary.
Use `--source` for generation/version/verification and `--kcl-source` for
plan/deploy/destroy. Never substitute the module library for the consumer's
configuration directory. Removed `deploy-unifi`/`deploy-cloudflare` APIs are
not restored: use `deploy` with explicit selective scope instead.

For an intentional, non-sensitive configuration export from a consumer directory:

```bash
bash scripts/dagger-qualified.sh api call -m . generate-unifi-config \
  --source=./kcl export --path=./unifi.json
bash scripts/dagger-qualified.sh api call -m . generate-cloudflare-config \
  --source=./kcl export --path=./cloudflare.json
```

These are explicit File exports, not implicit checkout writes or an accepted
Changeset adapter. Validation/verification does not export configuration, raw
state, credentials or plans into the checkout automatically.

Provider credentials and backend configuration enter as Secrets. Beta URI
syntax is `env://NAME`, not `env:NAME`. Despite its historical name,
`backend_config_file` is `Optional[Secret]`, not `File`. A remote selection
requires that Secret plus `backend_config_format="yaml"` or `"hcl"`; a plain
host path is not equivalent. Configuration is parsed/serialized in the
secret-mounted runtime and mounted owner-only, without returning its contents.
YAML has a constrained supported value model; malformed or unsupported data
fails, never falls back to treating YAML as HCL or to another backend.

Terraform 1.13.5 is selected by immutable image digest. KCL 0.12.4 uses the
official linux-amd64 release archive, SHA-256
`01dc1d8914ed8fdfac7e8b34cc155227cf7f155ef8760f741f35b0f8529f08ca`,
on the digest-pinned Python bookworm base with qualified Git 2.39.5.
The executable version is checked, not inferred from a tag. The mislabeled
`kcllang/kcl:v0.12.4` image reporting 0.12.3 was rejected. Version overrides
require reviewed helper pins; `latest` is not a supported default. Preserve
Python, Dagger, KCL and Terraform locks independently.

## Split-DNS Origins

Same-zone apex and subdomain origins are rejected by default as a conservative
loop guard. Public-zone membership is not proof of an actual loop: split-horizon
DNS can resolve the same name internally. An opt-in declaration records operator
intent only, not a lookup, resolution verification or routing change.

`cloudflare.SplitDNSOrigin` is a typed record with `protocol` restricted to
`"http" | "https" | "tcp"`, a concrete DNS `hostname: str`, and `port: int` in
1..65535. `CloudflareConfig.split_dns_origins: [SplitDNSOrigin]` defaults to
`[]`. `generate_cloudflare_from_entities`, `transform_service` and
`transform_tunnel_services` accept that same typed list as an optional trailing
`split_dns_origins` argument defaulting to empty. Pass it to any direct helper
that validates a same-zone origin, not only to a later configuration wrapper.

With the consumer's existing `cloudflare` schema import, the required policy
example for the already-intended `https://traefik-mid.sghd.io:443` origin is:

```kcl
_split_dns_origins: [cloudflare.SplitDNSOrigin] = [
    cloudflare.SplitDNSOrigin {
        protocol = "https"
        hostname = "traefik-mid.sghd.io"
        port = 443
    }
]
```

Assign this list to `split_dns_origins` in the existing `CloudflareConfig` or
pass `split_dns_origins = _split_dns_origins` to the existing entity-generator
or transform-helper call. This is a consumer migration example, not an edit
to the consumer repository or permission to change its origin routing.

- Match the exact lowercase URL scheme, case-insensitive DNS hostname with one
  terminal root dot normalized, and effective port. An omitted HTTP port is 80;
  an omitted HTTPS port is 443. TCP must have an explicit URL port.
- A declaration for HTTPS port 443 does not authorize HTTP, port 8443, another
  hostname or any descendant of that hostname. No suffix wildcards,
  subdomain inheritance or global bypass exists.
- Declaration hostnames cannot be URLs, wildcards, IP addresses or address
  ranges. Invalid declarations fail closed, including unused entries.
  Userinfo and ambiguous URL authorities cannot qualify for an exception.
- Paths, query strings and fragments do not change origin identity. Generation
  preserves output URLs, service ordering, TLS/path metadata and Terraform
  input shape. The validation policy is not emitted into Terraform JSON.
- Explicit services, entity-derived services, internal hostname overrides,
  resolved fallback hostnames and direct helpers use the same policy. Omitted
  or empty policy retains default rejection; origins outside the public zone
  retain their existing behavior.

Offline schema/generator tests establish exact matching and output preservation,
not DNS safety in a running network. Separately authorized live acceptance must
prove that the connector resolves the declared origin internally and reaches it
without a Cloudflare loop, with TLS and path behavior preserved.

## Root And State Ownership

`state_scope` accepts exactly `full`, `unifi` or `cloudflare` and must match
the flags and existing state. No flags selects `full`/`glue`; `unifi_only`
selects `unifi`/`unifi-dns`; `cloudflare_only` selects
`cloudflare`/`cloudflare-tunnel`. Both selective flags together fail. The
combined root keeps sibling module paths and existing resource addresses.
Standalone roots are only for already independently managed state, never an
implicit migration from combined state.

Public `deploy` and `destroy` reject local backend/state selections at method
entry. Specify a remote backend and preserve its address/bucket, key,
workspace, locking, lineage and provider/root identity. Backend failure stops
execution without falling back to local state. There is no supported default
ephemeral effect path even though the API's backend default remains `local`.

`plan` may use a local protected state Directory as read-only input, mutually
exclusive with a remote backend. Dagger Directory inputs are immutable
snapshots, not host mounts with automatic write-through. A preview returns
neither durable updated state nor permission for local apply/destroy.
DLR-1, durable local-state custody after successful, partial or unknown
effects, was explicitly deferred by the operator on 2026-11-14. It is not
implemented, waived as passed or replaced by cache retention.

## Preview And Disclosure

`plan` returns a Directory with `plan.txt` and `plan-summary.txt` by default.
Raw `plan.tfplan`, `plan.json` and the sensitive-handling manifest are added
only when `sensitive_artifacts=True` (`--sensitive-artifacts`). Raw files are
owner-only, but permissions alone are not encrypted storage or a retention
policy. Do not upload them to ordinary CI artifacts or commit them. Review
text output too; provider sensitivity classification can be incomplete.

Structured action counts distinguish add/change/destroy and validate malformed
input. A replacement contributes both create and delete; no-op/read actions
are not changes. A zero-change preview is no-drift evidence for that observed
scope/time only, not proof of full pipeline execution or production readiness.
Deploy independently replans. No saved-plan approval/execution API is added.

`get-tunnel-secrets` returns a protected credential Directory and defaults to
`output_format="json"`. It always includes `credentials.json`; `human` adds
`credentials.txt`, and `shell` adds `tunnel-secrets.sh`. Every file is sensitive
and owner-only (`0600`); shell output is not automatically executed. It requires the explicit
`protected_disclosure=True` acknowledgement. Credential material stays inside
the runtime until the caller explicitly exports the owner-only artifact.
That gate does not encrypt storage, choose a destination or authorize
disclosure. Use a separately approved protected destination with
`export --path='<protected-output-directory>'`, never ordinary logs, public
CI artifacts or source control. Do not read artifact contents back into a
transcript; owner-only permissions do not make plaintext safe to publish.
Its module detection supports combined or standalone Cloudflare outputs; it
must read the same backend as the deployment. Ephemeral state from a previous
invocation is not recoverable merely by rerunning the method.

## Freshness And Recovery

Live entry points use `@function(cache="never")`; underlying `live_exec`
adds a fresh UUID to each live execution graph. Function policy alone does
not make an otherwise identical exec fresh. Deterministic generation and tool
setup remain reusable independently. `cache_buster`, if supplied, is bounded
non-secret metadata only: 0-80 ASCII letters/digits/dots/underscores/hyphens.
Do not pass shell timestamp commands or credentials.

Failures must retain phase, exit status where available and non-secret
operation/recovery identity without raw provider/backend output. Preserve the
completed post-exec snapshot for dependent phases. Partial failure, cleanup
failure and unknown outcome are not success. Timeout/disconnect/cancellation
does not establish remote termination, rollback or safe retry. Reconcile the
process, remote resources and authoritative remote state before replay.

Disposable integration APIs have their own explicit authorization, resource
isolation, deadlines and cleanup evidence. They do not authorize general
local-state effects or prove cleanup after lost connectivity.

## Consumer Migration

1. Retain the previous full module/KCL revisions and runtime tuple for recovery.
2. Under separate publication authorization, publish the reviewed feature
   revision and select matching module/KCL revisions in the consumer branch.
3. Migrate/generate the Python workspace and retain generated entrypoints,
   clients and locks. Run `uv sync --frozen` before `uv run --no-sync`.
4. Update beta call syntax, Secret URIs, explicit backend format and matching
   state scope. Keep backend/provider/resource identities unchanged.
5. Verify credential-free generation and the entire offline baseline, then
   record repeated live-call, failure/disclosure and full-pipeline acceptance
   separately. A smoke test or no-op alone does not cover these contracts.
6. Obtain separate production-read approval for a fresh same-backend zero-drift
   preview. Unexpected changes stop adoption; no production read evidence is
   established by these instructions and no apply is authorized.
7. Promote only after feature/consumer acceptance and separate Git/deployment
   approval. Repinning code is not state or remote-resource rollback.

The sibling `adopt-modernized-dns-dagger-workspace` change owns consumer
adoption. No global toolchain change, provider upgrade, publication, merge or
production effect is implied by this documentation.

Candidate `38daa8a8131080659acb5e4d59e4a2135eb7d92f` remains superseded and
blocked by its strict same-zone guard. The downstream handoff records technical
acceptance of revised candidate `614c6aea5e2c92417e4e7d08882ccdcb4113eb33`
against its fingerprinted consumer working tree: matched remote source checks,
generation parity, Secret tests, connector-private connectivity and a fresh
zero-drift preview. See the runtime receipt's 2026-11-15 consumer handoff.
The separately approved sole backend setting change, `use_lockfile: true`, is
recorded explicitly; backend/state identity and other fields were preserved.
The downstream subsequently completed task 4.3 and archived its 12/12 change
before consumer publication. The current upstream closeout also fixes literal-IP
declaration rejection at `e8777e968f83fb7b8de82ccbd245b7f918ca20fa`, with
613/613 upstream tests and 21 renewed remote consumer checks in a disposable
public-input fixture. The user explicitly accepted bounded reuse of the previous
live evidence for unchanged execution inputs; no new live preview ran for this
SHA. See the runtime receipt's closeout requalification section. The real
consumer remains pinned to `614c6aea...`, durably retained at remote branch
`accepted/dagger-614c6ae`. Upstream archive/squash is authorized without a release,
not a consumer repin, production apply or unrelated cleanup.

## Independent Downstream Dependencies

`migrate-to-ubiquiti-community-unifi` and `add-cloudflare-live-ci-canary` both
consume this foundation; neither requires the other branch to finish. Their
prerequisite tasks now point to this document and the immutable runtime receipt
instead of choosing a moving beta release. Both still have unchecked
prerequisites: local runtime qualification alone is not consumer/live acceptance.
The later recorded handoff supplies technical acceptance for the exact candidate
and tested consumer snapshot, but does not promote an uncommitted consumer or
complete either downstream branch's independent acceptance/publication gates.

The shared selected contract is beta27 CLI checksum
`d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075`, engine
digest `ad121f720ed9bfb8e740f99dd783fa8472965a5e262fc64ff3ef2634cea1e6dd`,
Python SDK revision `9394f7454139f1ee2ca35be20e585b1e54f06cc2`, KCL 0.12.4
archive checksum `01dc1d8914ed8fdfac7e8b34cc155227cf7f155ef8760f741f35b0f8529f08ca`,
and Terraform 1.13.5 image digest
`6bbb82d575aa7bd4f0a2c6e3a0838ab9590426c08a71d7a2783643f01004d356`.
The generated Python API view is beta24, deliberately distinguished from the
beta27 engine. The stable 0.21.11 fallback remains unaccepted.

The provider branch retains its own guarded ownership migration, provider-read
side-effect qualification and production handoff. The thin-Actions branch
retains its own trusted-ref, scoped secret, sandbox-backend, all-writer fencing
and killed-run recovery acceptance. This foundation provisions neither branch's
services or credentials, activates no schedule and upgrades no provider.
