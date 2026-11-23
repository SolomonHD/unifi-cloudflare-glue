# unifi-cloudflare-glue

Define hybrid DNS services in KCL and generate UniFi DNS and Cloudflare Tunnel
configuration through a Python Dagger module. Terraform manages infrastructure
using the existing provider constraints and resource addresses.

## Supported Execution Path

This checkout uses the qualified Dagger **1.0.0-beta.28** CLI/engine and pinned
Python authoring SDK, not the old standalone deployment APIs. Read the
[runtime receipt](docs/dagger-runtime-qualification.md) for exact identities,
qualification evidence and outstanding acceptance gates. Installation or a
successful no-op is not full-pipeline or production acceptance.

From this repository root, use the wrapper that verifies the CLI checksum and
selects the immutable engine without changing the globally selected CLI:

```bash
bash scripts/dagger-qualified.sh api call -m . hello
bash scripts/dagger-qualified.sh api call -m . verify-offline --source=.
```

Generated `sdk/`, `clients/core/`, workspace/module manifests, `dagger.lock`
and `uv.lock` belong to this runtime contract. Do not run legacy `dagger
develop` or silently select a stable fallback. See
[CONTRIBUTING.md](CONTRIBUTING.md) for bootstrap and local verification.

## Configuration And Preview

Supply a consumer KCL directory containing `kcl.mod` and `main.k`. Its selected
exports must be `unifi_output` and/or `cf_output`; the root library `main.k`
is not a consumer configuration. Full operations select both outputs from one
validated native JSON snapshot. Dependencies require exact declarations and a
matching committed `kcl.mod.lock`; ordinary generation does not update them.

Cloudflare origins at the public zone apex or its subdomains are rejected by
default. For an intentionally split-horizon origin, declare only its exact typed
protocol/hostname/port tuple, for example with the existing `cloudflare` import:

```kcl
_split_dns_origins: [cloudflare.SplitDNSOrigin] = [
    cloudflare.SplitDNSOrigin {
        protocol = "https"
        hostname = "traefik-mid.sghd.io"
        port = 443
    }
]
```

Set `split_dns_origins = _split_dns_origins` inside `CloudflareConfig`, or pass
`split_dns_origins = _split_dns_origins` as the optional trailing argument to
`generate_cloudflare_from_entities`, `transform_service` or
`transform_tunnel_services`. Omitted policy defaults to `[]`. Matching uses a
lowercase URL scheme, case-insensitive DNS hostname with one terminal root dot
normalized, and effective port (HTTP 80, HTTPS 443; TCP needs an explicit port).
There are no suffix wildcards, inherited subdomains or global bypasses.
Invalid declarations fail closed; userinfo or ambiguous authorities cannot
qualify. URLs, ordering, TLS/path metadata and Terraform JSON are unchanged,
and the policy is not emitted into that JSON. See the
[split-DNS contract](docs/execution-contracts.md#split-dns-origins) for boundaries.

Public-zone membership alone is not proof of a loop. The declaration expresses
operator intent, not DNS verification. Separately authorized live acceptance
must prove connector-internal origin resolution without a Cloudflare loop.

For an explicitly authorized remote-state read, the full-scope preview is:

```bash
bash scripts/dagger-qualified.sh api call -m . plan \
  --kcl-source=./kcl \
  --unifi-url=https://unifi.local:8443 \
  --unifi-api-key=env://UNIFI_API_KEY \
  --cloudflare-token=env://CF_TOKEN \
  --cloudflare-account-id=your-account-id \
  --zone-name=example.com \
  --state-scope=full \
  --backend-type=s3 \
  --backend-config-file=env://TF_BACKEND_CONFIG \
  --backend-config-format=hcl \
  export --path=./plans
```

`TF_BACKEND_CONFIG` must be supplied by the caller's approved secret workflow;
it contains the backend configuration, not a host filename. The parameter is a
Dagger **Secret URI**, not an ordinary File path. Select `yaml` for YAML or
`hcl` for HCL explicitly. Preserve the existing backend bucket/address, key,
workspace, state lineage and locking. Failed parsing/authentication never
authorizes fallback to local state.

Default preview exports contain `plan.txt` and `plan-summary.txt`, not raw
JSON/binary plans. Review and protect text output too: Terraform's sensitive
markers are not a guarantee that every application value is classified.
`--sensitive-artifacts` is a separate, explicit opt-in for credential-bearing
raw plans and requires protected storage. A preview never authorizes effects;
`deploy` replans rather than executing this saved preview.

## Scope And Effects

| Selection | Flags | Terraform root |
| --- | --- | --- |
| Both providers | `--state-scope=full` | `terraform/modules/glue` |
| Independently managed UniFi state | `--unifi-only --state-scope=unifi` | `terraform/modules/unifi-dns` |
| Independently managed Cloudflare state | `--cloudflare-only --state-scope=cloudflare` | `terraform/modules/cloudflare-tunnel` |

The flags are mutually exclusive and must match the existing state's root.
Selective flags are not a way to split or migrate combined state. Full scope
retains the glue root and its sibling modules; plan, deploy and destroy must
use the same backend/root/address identity.

After separate authorization for the named target, use `deploy` or `destroy`
in place of `plan` with the same selected scope, credentials and remote-backend
arguments, and omit `export`. These commands can create or delete real
resources. They require an **explicit remote backend** and reject local-state
selections at entry before generation, initialization or effects. The default
`backend_type="local"` in the signature is not a working deployment default.

Local `plan` previews may consume `--state-dir` as a protected input snapshot.
They do not write back to the host, persist updates or enable local effects.
Durable local-state custody/recovery **DLR-1 is deferred by explicit operator
decision**, not implemented or accepted. Disposable live integration lifecycles
are separate, explicitly authorized tests, not a general ephemeral deployment
path.

## Freshness And Failures

Live functions use `cache="never"` and each live exec receives a fresh UUID.
Deterministic generation/tool setup remain reusable. No shell timestamp or
caller cache buster is required for correctness. The optional `cache_buster`
is only a non-secret run label: at most 80 letters, digits, dots, underscores
or hyphens. Never place a credential or shell expression in it.

Unsuccessful operations raise sanitized failures with phase/exit/recovery
metadata rather than returning a successful failure string. After a timeout,
cancellation, disconnect or partial effect, retain the operation identity and
reconcile process termination, remote resources and authoritative backend state
before retrying. Restoring source or state is not remote rollback.

## Credentials And Tool Pins

- Provider inputs use Dagger Secrets, such as `env://UNIFI_API_KEY` and
  `env://CF_TOKEN`. UniFi accepts an API key or a complete username/password
  pair, never both methods or a partial pair.
- `get-tunnel-secrets` requires `--protected-disclosure` before returning
  a protected credential Directory for explicit export. Its `json` default
  and optional `human`/`shell` artifacts contain secrets and retain owner-only
  file permissions. Use a separately authorized protected destination, never
  ordinary logs, CI artifacts, chat or a source-controlled file.
- Terraform defaults to **1.13.5** through the digest-pinned helper. KCL is the
  exact official **0.12.4** release archive with SHA-256 verification on the
  pinned Python/Git base (qualified Git **2.39.5**). Unsupported version
  overrides fail rather than resolve `latest`. See `src/main/toolchains.py`
  and the runtime receipt for immutable identities.

## Documentation

| Document | Scope |
| --- | --- |
| [Execution Contracts](docs/execution-contracts.md) | Current API migration, state custody, output handling and acceptance boundaries |
| [Runtime Qualification](docs/dagger-runtime-qualification.md) | Exact runtime identities and recorded evidence |
| [Offline Verification](docs/offline-verification.md) | Credential-free bootstrap/check separation and evidence |
| [KCL Guide](docs/kcl-guide.md) | Configuration/schema background |
| [Contributing](CONTRIBUTING.md) | Frozen development setup and verification |

Older topical guides and `README.old.md` may describe pre-migration commands.
They are historical/background material, not authority for runtime syntax,
Secret transport, cache correctness, local persistence or artifact defaults.
Use the current execution contracts and generated API for those interfaces.

## Acceptance Boundaries

Credential-free checks, runtime probes and a zero-change preview are distinct
evidence. Full pipeline acceptance, published feature-revision consumer loading
with matching KCL, and separately approved production-read zero-drift acceptance
must each be recorded. This README establishes none of those gates and records
no production read, apply or destroy. Provider migration, global tool selection,
consumer promotion, publication and release remain separately scoped work.

Candidate `38daa8a8131080659acb5e4d59e4a2135eb7d92f` remains blocked, not
accepted retroactively by the split-DNS revision. Tasks 6.2/6.3 remain open:
consumer and live acceptance must be repeated against the revised exact SHA
after separately authorized commit/push. No new SHA or consumer routing change
is established here.

## License

MIT
