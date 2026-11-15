# Dagger Runtime Qualification

Current closeout disposition, 2026-11-15: the downstream completed task 4.3 and
archived its 12/12 change. Archive-readiness testing then found and fixed an
unused literal-IP declaration mismatch. Revised functional candidate
`e8777e968f83fb7b8de82ccbd245b7f918ca20fa` passed 613 local/613 Dagger tests
and renewed exact-SHA remote consumer qualification. The operator explicitly
accepted bounded reuse of the earlier live evidence for unchanged execution
inputs; no new live preview ran against this revision. See
[Closeout Requalification](#closeout-requalification-and-explicit-evidence-reuse-2026-11-15).
Earlier pending gates and SHA-bound live receipts remain historical evidence,
not claims that a new live operation ran. Squash/merge is authorized without a
release; deployment or consumer repinning is not implied.

## Candidate Receipt, 2026-11-14

Qualification ran on SOL-3D-MIDSEASON as solomong, outside the application
checkout, without production credentials or changes to global tool selection.
This receipt accepts the isolated runtime checks, not production adoption.

| Component | Exact identity |
| --- | --- |
| CLI | `/home/solomong/.local/opt/dagger/1.0.0-beta.27/bin/dagger` |
| CLI SHA-256 | `d8a5c186090f92062fe773508f3b4d609ea75658802d5f5b75d6f627f2f2a075` |
| Dagger source | `400b82d6f3c09ef096d2f59b3e920267b5969bf4` |
| Engine version | `v1.0.0-beta.27+400b82d6` |
| Engine index digest | `registry.dagger.io/engine@sha256:ad121f720ed9bfb8e740f99dd783fa8472965a5e262fc64ff3ef2634cea1e6dd` |
| Engine linux/amd64 digest | `sha256:c3e653724654c9c3ce4124abc1f879a2dec55ba5d133fc7fa7528589e6e2f5f9` |
| Python authoring SDK | `github.com/dagger/python-sdk@9394f7454139f1ee2ca35be20e585b1e54f06cc2` (`v1.8.0`) |
| Generated API view | `v1.0.0-beta.24`, the pinned SDK's default, served by beta27 |
| Qualification Python | `3.12.16` |
| Python container | `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b` |

The SDK package's generated version is `dagger-io==0.0.0`; its immutable
source revision, not that package label, establishes SDK identity.

## Manifest And Invocation Checks

The isolated fixture is `/tmp/kilo/dagger-beta27-qualification-20261114`.
Its generated files remain there for inspection, including `dagger.lock`.
The following sequence succeeded using the CLI and engine above:

1. Initialize an empty Git fixture and run `dagger init`.
2. Create a minimal legacy Python module with a `hello` function.
3. Run `dagger module migrate ./module --auto-apply`.
4. Pin the migration-added Python SDK source to the revision above.
5. Run `dagger generate --auto-apply`.
6. Run `dagger api call -m ./module hello`: `python-runtime-ok`.

All behavioral qualification commands supplied `--engine` with the index digest above. CLI help discovery also included commands without an engine override; a workspace-aware help command loaded its default engine, but its result is not behavioral qualification evidence. Global context
flags precede SDK selection. A new workspace does not register `python`
automatically. Installing `dagger/dagger/sdk/python/runtime` alone does not
register the Python authoring SDK; that runtime is not its replacement.
Migration initially writes an unpinned standalone SDK source: pin it before
generation, rather than accepting a moving source.

Qualified paths are workspace `dagger.toml`, module `dagger-module.toml`,
workspace `dagger.lock` (format version 2), generated `sdk/entrypoint/`,
`sdk/src/dagger/`, and `clients/core/`. Generation replaces the builtin
`[runtime] source = "python"` with a generated entrypoint. Its
`sdk/entrypoint/dang.toml` records the beta24 API view. Generated bindings must
be retained for cold execution. Dagger's lock does not replace Python's
`uv.lock` or Terraform/KCL locks. The tiny qualification fixture used pip
resolution; it is not the application's frozen-dependency acceptance.

## Synthetic Behavioral Results

`python3 /tmp/kilo/dagger-beta27-qualification-20261114/check_contracts.py`
exited zero after separate CLI invocations proved:

- Two identical default-function calls reused the same generated UUID.
- Two identical `@function(cache="never")` calls returned different UUIDs.
- Two identical uncached functions constructing a container with a fresh,
  non-secret invocation environment variable executed Python twice and
  returned different execution-generated UUIDs.
- `--value=env://QUALIFICATION_SECRET` passed a synthetic Secret input to
  `with_mounted_secret(..., mode=0o400)`; the container verified permissions
  and readable content, returning only `secret-channel-ok`.
- A function returned a generated `Secret`; its `name` could be selected
  without selecting `plaintext`. Generated secrets need not have a provider
  URI; an empty `uri` is not evidence that output failed.
- The final subprocess stdout/stderr scans contained no synthetic canary.

Initial fixture-only mistakes were corrected before the passing run:
`env:` is not the beta Secret URI syntax (`env://` is); Secret `id` is not a
CLI field; and embedding a canary literal in an asserted command exposes that
literal as command text. The final command contains no canary. These are not
production security-path tests, which remain separate implementation tasks.

## Separate Remote Consumer

`/tmp/kilo/dagger-beta27-consumer-20261114` is a separate empty Git fixture.
It successfully installed this immutable remote dependency:

```text
github.com/dagger/python-sdk/.dagger/modules/e2e/fixtures/runtime/app@9394f7454139f1ee2ca35be20e585b1e54f06cc2
```

`dagger api functions remote-python-fixture` loaded its schema, and
`dagger api call remote-python-fixture greeting` exited zero, returning
`served by the python-sdk runtime`. This checks remote Python runtime loading
on the candidate engine. It does not substitute for task 6.2's remote loading
of the reviewed application feature revision and matching consumer KCL.

The GitHub HTML fixture page could not be fetched because of robots policy;
the immutable Git dependency itself loaded and executed successfully.

## Current-Interface Baseline

Application HEAD `0dbdfb70d4f197ddfd4ed222292ba86ebc8ec1fb` on
`modernize-legacy-unit-test-contracts` passed full collection (263 tests), all
263 unit tests in 14.21 seconds, Black (9 files), isort, mypy (3 source files),
in-memory compilation (9 files), and all seven documented KCL entry points
with KCL 0.12.4. There were no exclusions, skipped tests or expected failures.
The offline environment used `uv run --offline --frozen --no-sync` with
pytest 9.2.0, pytest-asyncio 1.5.0, Black 26.10.1, isort 9.0.2, mypy 2.4.1,
and types-PyYAML 6.0.12.20261113. The entry points were `main.k`,
`test_validation.k`, `test_error_validation.k`, `test_error_format.k`,
`test_cloudflare.k`, `generators/unifi.k`, and `generators/cloudflare.k`.

## Acceptance Boundaries

No stable fallback was selected. Production reads, provider effects, feature
publication, consumer adoption, merge and archive were not performed. Runtime
qualification does not authorize them. Application migration, frozen tooling,
the full error/state/security contracts, and cross-repository acceptance must
still pass before this change is complete.

## Compatibility And Consumer Migration

| Interface | Existing application | Modernized contract |
| --- | --- | --- |
| Runtime | `dagger.json`, engine v0.19.8 | Qualified beta27 engine plus pinned standalone Python SDK and generated entrypoint |
| Invocation | Pre-1.0 `dagger call` examples | Qualified beta CLI uses `dagger api call`; Secret inputs use `env://NAME` or another explicit provider URI |
| Backend | Ordinary `backend_config_file: File`, automatic format detection | Secret-typed configuration, explicitly selected YAML/HCL format; no plaintext File fallback |
| Freshness | Caller cache buster | Uncached live function plus fresh non-secret execution identity; deterministic generation remains reusable |
| Failure | Successful strings containing failure markers | Nonzero status with bounded phase, exit and recovery metadata |
| Local state | Directory input described as host write-through | Public deploy/destroy require remote state and reject local selections before effects; read-only previews promise no write-through; durable local handoff is unfinished DLR-1 |
| Plan | Inconsistent root selection and action parsing | Same selected root/backend as execution; structured string action arrays |
| Sensitive output | Ordinary credential/state/plan reporting | Protected opt-in disclosure, never default checkout output |

The right-hand column is the implementation target, not a statement that the
existing public application functions have already migrated. Downstream callers
must not select this foundation until its application tests and acceptance pass.

Consumer migration order:

1. Retain the previous full module/KCL revisions and tool tuple for recovery.
2. Select the reviewed, published feature module revision and matching KCL
   source in an isolated consumer branch. Do not retarget production defaults.
3. Install the pinned Python authoring SDK, migrate each local Python module
   with `module migrate`, then generate it before migrating a dependent module.
   Commit generated entrypoints/clients and the applicable Dagger/Python locks
   only under separate Git authorization. Never run automatic generation during
   a production invocation as a substitute for those committed files.
4. Update invocation syntax and backend inputs explicitly. Keep the same remote
   backend address, bucket, key, workspace, locking, root and provider identities.
   Do not open backend files in application Python or convert a failed backend
   initialization into local state. Preserve existing Secret credential channels.
5. Run credential-free generation and verification. Compare normalized provider
   outputs, selected roots and resource addresses. Test failure exit status and
   protected state recovery before any effectful adoption.
6. Obtain separately authorized production-read acceptance: a fresh zero-drift
   plan on the unchanged backend. A preview does not authorize deploy, which
   replans independently. Unexpected deltas stop adoption.
7. Promote only after accepted feature evidence and separate Git/deployment
   authorization. Code/tool repinning is not proof of remote state rollback.

The stable v0.21.11 fallback is installed but **not accepted or tested** here.
If a required beta check later fails, retain that evidence and pause for an
explicit fallback decision. Its exact invocation is
`mise exec aqua:dagger/dagger@0.21.11 -- dagger`. Qualify its Python SDK,
`dagger.json` and any supported locks independently; do not carry beta
`dagger.toml`, generated-entrypoint or `dagger api call` assumptions into it.

## Application Migration Recovery

After the isolated checks passed, application `module migrate . --auto-apply`
completed successfully. It replaced `dagger.json` with `dagger-module.toml`,
retaining its legacy `engineVersion = "v0.19.8"` and builtin Python runtime
until generation; `dagger.toml` records the pinned standalone SDK and root
Python scope. `dagger.lock` was created. None of these observations establishes
successful application generation or adoption.

The subsequent `generate --auto-apply` exited 1 after 12.3 seconds:

```text
generate SDK scope ".":
python -m dagger.mod entrypoint --name unifi-cloudflare-glue
  --client-version v1.0.0-beta.24 --output /dagger/entrypoint
ModuleNotFoundError: No module named 'dagger._managers'
```

The failure occurred in `/opt/venv/lib/python3.11/site-packages/dagger/` while
importing the new SDK entrypoint machinery. The existing host SDK contains
`_managers.py`, as does the successful isolated SDK fixture. The application
still declares the legacy editable `sdk` dependency, has `/sdk/` ignored,
and uses `uv_build>=0.8.4,<0.9.0`, whereas the minimal successful fixture used
Hatchling. These differences are investigation leads, not an established root
cause. The existing application SDK and `uv.lock` were not manually replaced,
and the failed generation did not export new clients or package configuration.

The operator approved scoped configuration-level recovery. Changing only the
isolated fixture's root build backend to the application's existing
`uv_build>=0.8.4,<0.9.0` constraint did not break generation. Adding an ignore
rule for its generated SDK did break generation; removing that rule restored
it. Removing the application's `/sdk/` ignore was then sufficient for actual
application `generate --auto-apply` to pass (7.6 seconds), followed by a
successful `dagger api call -m . hello` (6 seconds). This demonstrates the
sufficient visibility correction; it does not prove a selective wheel-file
omission mechanism for the original traceback.

The generator updated Python workspace sources/members and `uv.lock` itself.
`uv sync --frozen` installed the generated SDK/core client successfully. The
initial post-generation test command used `--no-sync` and consequently lacked
the new core client; after synchronization all 263 tests collected. A test
boundary's automatic patching mistook the new lazy SDK Session for an async
builder; explicit `Mock()` restores the synchronous boundary with all 30
deploy-guidance tests passing, without weakening assertions.

Task 2.1's tool identity and frozen bootstrap checks subsequently passed, as
recorded below. The operator additionally approved an exact KCL 0.12.4
release-binary pin after the `kcllang/kcl:v0.12.4` image unexpectedly reported
0.12.3. That image's tag is not proof of its executable version.

No global tool selection, production access, stable fallback, commit, push,
merge or archive was performed during recovery.

## Backend Conversion Evidence

Task 4.2 now requires explicit `yaml` or `hcl` selection through
`process_backend_config_content(content, format)`. Its 108 synthetic tests
exercise real `python-hcl2==8.2.0` parsing, literal escaping and unsupported
type/key/error rejection. A worker additionally checked syntax and exact-value
round trips using Terraform 1.15.8 `fmt`/`console`; this is parser evidence,
not acceptance of that Terraform version as an execution tool. The parent
reran these tests together with 12 immutable-tool identity tests: all 120
passed. Secret-mounted execution integration and provider/backend acceptance
remain separate tasks.

## Native KCL And Tooling Recovery

The operator approved replacing the mislabeled image with the official native
KCL 0.12.4 release and then qualifying a Git-capable base for KCL generation.
`src/main/toolchains.py` records the immutable identities:

- KCL archive:
  `https://github.com/kcl-lang/cli/releases/download/v0.12.4/kcl-v0.12.4-linux-amd64.tar.gz`,
  SHA-256 `01dc1d8914ed8fdfac7e8b34cc155227cf7f155ef8760f741f35b0f8529f08ca`.
  The official release API supplied the digest; Dagger verifies it before
  extraction. The archive contains a bare `kcl` executable. Its runtime version
  is asserted to equal `0.12.4` before generation.
- KCL base: `python:3.12-bookworm@sha256:4209fae09a3e20afd863e528bfddc235da5fd5977983e1996cd54cc9a72e6267`.
  Actual linux/amd64 execution reports Python 3.12.16 and Git 2.39.5; no package
  installer or global Git configuration change provisions Git.
- Terraform: `hashicorp/terraform:1.13.5@sha256:6bbb82d575aa7bd4f0a2c6e3a0838ab9590426c08a71d7a2783643f01004d356`.
  Actual `terraform version -json` reports 1.13.5 on linux_amd64. This tool pin
  does not upgrade provider constraints or establish production state acceptance.
- The slim Python base remains independently pinned for parser/offline work;
  it is not silently substituted for the Git-capable generation base.

The pinned beta engine executed shared `_generate_configs` against a synthetic
source, produced both canonical provider files from one native JSON snapshot,
and returned `native-generation-both-providers-ok`. All 195 focused generator
and DNS-loop tests pass using the real local KCL 0.12.4 boundary. These retain
normalization, site, multi-NIC/distribution, malformed/missing/empty output,
literal VALIDATION content and selected-provider-only assertions.

The actual-container Git probe is retained at
`/tmp/kilo/qualify-kcl-git-20261114.py`. It creates an entirely synthetic local
Git fixture inside the qualification container, fixes its commit dates, pins
the dependency by full commit, resolves native KCL JSON, then supplies the
resulting lock to `_generate_configs`. The second run confirms unchanged lock
bytes and the expected selected provider output: `locked-native-git-resolution-ok`.
Only the synthetic repository history inside that disposable fixture is created;
application Git history is untouched. An initial fixture put its dependency
beside the root import, causing package-name shadowing; moving it under
`.fixtures/` resolved that test-construction error.

KCL 0.12.4's Git resolution needs a Git executable and may write acquisition
diagnostics to stdout. Generation therefore reads the explicit JSON output file,
not stdout, checks exact dependency declarations against committed resolution
metadata, and rejects unexpected lock rewrites. This probe is not the sibling
consumer's feature-revision acceptance or production-read acceptance.

## Final Local Foundation Verification

The final workspace pins application `uv_build==0.8.24` and constrains workspace
build backends to that exact release. Runtime YAML/HCL dependencies and the
complete development tool group, including their transitive versions, are
frozen by `uv.lock`. `uv sync --frozen` bootstraps the environment; ordinary
checks use `uv run --offline --frozen --no-sync`, not fresh `--with` resolution.
The qualified shell wrapper checks the CLI SHA-256 before selecting the pinned
engine and rejects unqualified engine overrides.

Final checks on 2026-11-14:

| Check | Result |
| --- | --- |
| Qualified `generate --auto-apply` | Passed, 6.3 seconds |
| Local `bash scripts/verify-offline.sh` | 474 tests passed, no skips; Black/isort, mypy (8 source files), compilation and all seven KCL entry points passed |
| Qualified public `verify-offline --source=.` | Same 474 tests passed, no skips; same static/format/KCL checks passed |
| Public UniFi and Cloudflare File generation/export | Both passed with canonical synthetic JSON, explicit exports only under `/tmp/kilo/dagger-public-generation-20261114/` |
| Provider constraints, lockfiles and Terraform resource source | `git diff --exit-code -- terraform` passed |
| Whitespace | `git diff --check` passed |
| Active change plus both independent downstream changes | Strict validation passed |
| Affected main specs and non-writing delta preflight | Passed; unrelated repository-wide historical failures remain separately recorded |

An initial offline-container run skipped five native Terraform parser tests;
this was not accepted as equivalence. Copying the already-qualified Terraform
1.13.5 binary into the verification runtime removed those skips. The workstation
parser tests also passed with its existing Terraform 1.15.8, without changing
that global selection. Local Python was 3.12.13; the pinned check container was
3.12.16. The generated application entrypoint additionally loaded and executed
on its supported Python 3.11 runtime. Existing pytest/plugin deprecations were
warnings, not excluded tests.

Final schema loading initially exposed a new-source naming collision:
`*credential*` in the existing secret ignore rules hid a helper named
`tunnel_credentials.py`. It was renamed to `tunnel_artifacts.py`, together with
its tests and runtime script reference. The secret ignore rule was not weakened.
The subsequent generation and actual credential runtime checks passed.

The native backend error probe
`/tmp/kilo/verify-terraform-trace-protection-20261114.py` derives a field from a
multi-field synthetic Secret and makes a fake Terraform command emit it to both
stdout and stderr before exit 17. Native redirection kept it out of captured
stdout/stderr and the complete engine trace; phase and exit-17 information stayed
visible. Source-only exception sanitization was insufficient without redirection.

The native plan probe `/tmp/kilo/verify-plan-boundaries-20261114.py` planned a
builtin `terraform_data` fixture without apply or provider/backend access.
Runtime assertions proved the sensitive marker absent from reviewed text,
present only in protected raw JSON, correct action counts, and raw artifact
permissions `0600`; the complete trace scan passed.

The final credential probe
`/tmp/kilo/verify-protected-tunnel-artifact-20261114.py` exercised JSON, human
and shell outputs through the public Python method and real Dagger objects.
It checked UID 0 / `0600` artifact files, bounded verification metadata, derived
token/secret non-disclosure on success, output-exit-17, malformed data and timeout
paths, and actual immutable Terraform 1.13.5 output against synthetic local
state. No provider/backend was contacted. Both derived-value scans of captured
stdout and complete engine trace passed. Raw credential bytes were never read
back into this receipt.

These are local foundation and synthetic acceptance results. During qualification
no application feature was committed/pushed, no sibling consumer source revision
was accepted, and no production backend/provider read or apply was performed.
Subsequent feature publication is a separate authorization and does not complete
consumer acceptance. Tasks 6.2 and 6.3 require their separately authorized
evidence before merge or promotion; use the independently verified full published
SHA supplied with the consumer handoff, not the package's unchanged version label.

## Remaining Acceptance Gate Discovery

Read-only sibling discovery found `adopt-modernized-dns-dagger-workspace` only
in `/home/solomong/Code/Misc/portainer-docker-compose`, at detached HEAD
`c85bd7af13de5c8176f03ca1b2932b188d4cf030`. At that observation its only dirty
entry was the untracked consumer change directory; the consumer's planning
artifacts were complete but all 12 implementation tasks were unchecked.
All three registered consumer checkouts received separate OpenSpec-list
inspection. Unrelated dirty contents were not inspected or changed.

The consumer still selected engine v0.20.8 and module
`github.com/SolomonHD/unifi-cloudflare-glue@v0.14.0`, resolved to
`d33f4deffd4d2dd7965c49663d4da4093a2f4100`. Its KCL declaration selected the
same repository's v0.14.0 tag; full KCL resolution was not verified. These are
old release selections, not this unpublished modernization candidate. The
authoritative consumer input is `kcl/main.k` with wrappers in `kcl/generators/`.

No feature publication, matching consumer implementation, backend identity
read, credential resolution or production preview was performed by discovery.
Do not treat the matching change's presence, its completed planning artifacts,
or the upstream 474-test result as consumer or production acceptance. Refresh
checkout/head/pin identity under the separately approved acceptance operation;
these observations are point-in-time discovery only. At the end of local
qualification the upstream implementation was uncommitted on
`modernize-legacy-unit-test-contracts`; later publication must be verified
against that branch's remote full SHA rather than inferred from this receipt.
Tasks 6.2 and 6.3 remain unchecked; no merge or archive is requested here.

## Split-DNS Revision Qualification, 2026-11-14

Consumer acceptance rejected published candidate
`38daa8a8131080659acb5e4d59e4a2135eb7d92f` because its same-zone origin
guard rejected existing split-DNS origins. Zone membership alone is not proof
of a tunnel loop. The checks below qualified a working-tree revision based on
that SHA before publication. Later feature publication requires separate
authorization and does not establish consumer acceptance. Use the independently
verified full published SHA supplied with this revision's downstream handoff,
not the old candidate or an assumed branch/tag resolution.

The chosen source contract is `cloudflare.SplitDNSOrigin` with required
`protocol` (`http`, `https` or `tcp`), concrete DNS `hostname`, and integer
`port` (1..65535). `CloudflareConfig.split_dns_origins` and the entity/transform
helpers' optional trailing argument default to an empty typed list. An exception
matches one protocol, case-normalized hostname with one terminal DNS dot
removed, and effective port (HTTP 80 / HTTPS 443; TCP needs an explicit port).
Wildcards, inherited subdomains, global bypass flags, URI/userinfo declarations
and malformed authorities are not accepted as exceptions. URL paths and query
strings do not change origin identity; emitted URLs and ingress ordering remain
unchanged, and policy metadata is not emitted into Terraform input JSON.

Required consumer declaration for the reported origin, using its existing
import alias for this module's Cloudflare schemas:

```kcl
split_dns_origins = [cloudflare.SplitDNSOrigin {
    protocol = "https"
    hostname = "traefik-mid.sghd.io"
    port = 443
}]
```

Set that field on the existing `CloudflareConfig`, or pass the same list as
`split_dns_origins=...` to the existing entity/transform call. This receipt
does not edit the consumer or authorize an origin/routing change. Each additional
origin needs its own exact declaration.

Credential-free revision results:

- Full local `bash scripts/verify-offline.sh`: **593 passed, no skips**.
- Qualified Dagger `verify-offline --source=.`: **593 passed, no skips**.
- Black/isort, mypy across eight application files, compilation and all seven
  KCL entry points passed. Existing plugin deprecations remain warnings.
- Qualified schema generation passed (5.7 seconds); Python runtime, SDK, engine,
  tool identities, locks and provider constraints were not changed.
- Focused DNS suites: 171 passed, including 119 new split-DNS cases and all 52
  existing default-rejection regressions. Cases cover all five entry paths,
  approved/unapproved same-zone origins, case/root-dot and default-port matching,
  label boundaries, raw structural declarations, malformed types/values,
  per-origin isolation, preserved ingress order/TLS/path metadata and non-emission
  of the allowlist.
- `/tmp/kilo/qualify-split-dns-public-20261114.py` exercised the public Cloudflare
  generator with real Dagger Files and the pinned native compiler. The exact
  approved origin succeeded with original URLs/order; a different same-zone
  declaration failed without producing a usable File. No provider or origin-DNS lookup
  was performed.
- Strict validation passed for the active change and canonical main
  `config-generation` / `generator-output-validation` specs. The older
  `kcl-validation-rules`, `kcl-debugging-guide` and `terraform-module` files retain
  their pre-existing structural warnings; unrelated contract/header repair was
  not folded into this revision. The existing `rules.general` warning remains.
- `git diff --check` passed. `git diff --exit-code -- terraform src/main scripts
  dagger-module.toml dagger.toml dagger.lock pyproject.toml uv.lock` confirmed no
  provider-source, execution-contract or tool/lock changes.

The exception records **operator intent, not verified DNS resolution**. Live
acceptance must separately prove the tunnel connector resolves each declared
origin internally and reaches it without routing back through Cloudflare,
including relevant TLS/path behavior. No production access or live DNS/route
check was performed here. No consumer routing change, commit/push, merge or
archive was performed during qualification. Tasks 6.2 and 6.3 remain open and must repeat against the
revised exact published SHA after separate publication/read authorization; the
old candidate's prior qualification is not substituted for that evidence.

## Consumer Technical Acceptance Handoff, 2026-11-15

The operator supplied the final downstream acceptance handoff. Its technical
results satisfy upstream tasks 6.2 and 6.3 for the exact candidate and tested
consumer working-tree snapshot below. They do not establish a committed consumer
feature revision, promotion readiness or permission to merge/deploy/archive.

This reconciliation used the recorded, sanitized consumer receipt and read-only
Git/source inspection. It did not rerun tests, read backend credentials or state,
inspect private plan contents, contact providers/Wasabi/connectors, or repeat the
preview. Live authorizations and results below are attributed to the downstream
handoff, not new authority for this session or independent live verification.

### Source And Evidence Binding

| Input | Recorded or inspected identity |
| --- | --- |
| Accepted upstream Dagger and KCL source | `614c6aea5e2c92417e4e7d08882ccdcb4113eb33` |
| Superseded blocked candidate | `38daa8a8131080659acb5e4d59e4a2135eb7d92f` |
| Upstream feature branch | `modernize-legacy-unit-test-contracts` |
| Upstream remote main and feature merge-base | `6d87ec01164fb338c33ee02cf755a491dc745ef3` |
| Consumer worktree | `/home/solomong/Code/Misc/.worktrees/portainer-docker-compose/adopt-modernized-dns-dagger-workspace` |
| Consumer branch | `change/adopt-modernized-dns-dagger-workspace` |
| Consumer HEAD/base, not an implementation commit | `c85bd7af13de5c8176f03ca1b2932b188d4cf030` |
| Observed remote consumer main | `c8203cf35b2ea4861427c70c4aa3532bb7809c0c` |
| Reported tested execution-source fingerprint | `9bda6c7e86f51e3f66d6abbc96ceee074b2825d6f90c3d8287c91948d74ae68f` |
| Consumer implementation publication | None; tracked changes and new files remain uncommitted/untracked |

Read-only reconciliation confirmed upstream local/remote feature HEAD and remote
main, consumer HEAD/branch and uncommitted status, and the absence of a published
consumer feature branch at the reported remote. It inspected the actual Dagger
registration, generated runtime lock, KCL declaration/acquisition lock and the
three exact origin declarations. The source fingerprint and runtime execution
results are retained from the handoff; this session did not recompute its
fingerprint or independently repeat its remote module acquisition.

Authoritative downstream evidence is the latest superseding section of:
`<consumer-worktree>/openspec/changes/adopt-modernized-dns-dagger-workspace/verification.md`.
Earlier blocked/unconfigured-locking statements in that chronological receipt
are historical, not the final disposition. Consumer task 4.3 is still unchecked.

### Task 6.2: Matched Remote Consumer Acceptance

- Native module update resolved the registered remote module to the full accepted
  SHA; discovery exposed 11 functions, and actual remote generators and the
  production preview ran through that registration.
- The KCL acquisition lock resolves the same full SHA. Package label `0.14.0`
  is not used as source identity. The CLI-generated format-2 Dagger lock retains
  Python 3.11 runtime digest
  `07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535`.
  Full Git SHAs need no symbolic lookup entry; locking is workspace-bound, not
  a claim of universal recursive image locking or a fresh-machine reinstall.
- Consumer checks passed: 10 source/runtime/guidance, 5 generation/parity, and
  6 synthetic Secret checks, 21 total. Both provider outputs matched the old
  baseline and repeated byte-identically: 5 UniFi devices, 3 Cloudflare tunnels,
  13 `both` services and 42 `unifi_only` services. Actual-consumer
  `cloudflare_only` coverage is not claimed.
- Negative/normalization coverage included 16 native rejection fixtures, one
  actual remote rejection and nine hostname/default-port fixtures. Policy
  metadata was absent recursively from exported Terraform JSON.
- Exactly three separately operator-approved HTTPS/443 origins were declared:
  `traefik-mid.sghd.io`, `traefik-lc.sghd.io` and
  `traefik-docker-infra.sghd.io`. Recorded full output parity and source comparison
  preserve URLs, routes, ingress order and TLS/path settings. No global bypass or
  unapproved origin is accepted.
- The existing beta27/SDK v1.8.0 (beta24 API view)/KCL 0.12.4/Terraform 1.13.5
  tuple was used without a provider upgrade. Synthetic checks exercised
  `env://` Secrets, owner-only mounting, protected normal/error output and export
  boundaries, and pre-backend scope/label rejection. No unsupported File Secret
  provider or auto-install fallback is inferred.

### Task 6.3: Separately Authorized Live Evidence

The handoff records separate approval for connector tests and a fresh production
preview, then for a disposable Wasabi lockfile test and enabling
`use_lockfile: true`. The backend configuration was therefore **not byte-for-byte
unchanged**. This sole, explicitly authorized setting change is distinguished
from unchanged endpoint/bucket/key/workspace/state identity, credentials and all
other fields. It was not an implicit conversion, migration or local fallback.
The owning external backend template's edit remains uncommitted per the consumer
receipt; its custody/publication is not performed or authorized by this report.

| Declared origin | Connector-network DNS and actual TLS peer | Recorded result |
| --- | --- | --- |
| `traefik-mid.sghd.io:443` | `192.168.60.114` | Private peer, certificate verification passed |
| `traefik-lc.sghd.io:443` | `192.168.50.155` | Private peer, certificate verification passed |
| `traefik-docker-infra.sghd.io:443` | `192.168.50.192` | Private peer, certificate verification passed |

Pinned temporary probes shared each exact connector's network namespace without
credentials, volumes, published ports or elevated privileges. All 13 service
hostnames received `HEAD /` checks with redirects disabled; peers were private
and responses lacked `CF-Ray`. This supports direct internal origin connectivity
without a Cloudflare hop in those probes. It does not prove full browser,
redirect-chain or application health; observed 404/HEAD-405 responses were not
counted as health passes. Probe containers were removed and absence reconciled.

Disposable lock evidence includes successful conditional acquisition, competing
writer HTTP 412, native Terraform refusal while held, successful native plan
after release and direct verification of an empty disposable prefix. This is
qualified only for the tested Wasabi endpoint/bucket/credential/runtime.

The single fresh full-scope preview used the exact candidate, enabled locking,
real Secret inputs and existing `filipowm/unifi`, `cloudflare/cloudflare` and
`hashicorp/random` sources. Combined root `glue` covered 93 resource instances.
Operation `27fc831c-ed0c-43b8-be96-59970e55551e` reported **add 0, change 0,
destroy 0, replace 0**, with no unexpected deltas. Backend/state identity,
contents, lineage, serial, provider/root identities and resource count matched
before/after; production lock release was directly verified downstream.
Only protected default text artifacts were exported, not raw state or raw plans.

A local parser initially expected a module path rather than the reported root
name `glue`. The original completed outputs and operation/state/lock results were
reconciled after correcting that parser, without replaying the preview. No
unresolved execution outcome remains in the reported operation. No apply,
destroy, state/provider migration or routing change occurred. Lock enablement,
temporary diagnostic containers and disposable test locks are explicit authorized
changes, not mislabeled as an entirely mutation-free acceptance run.

### Remaining Promotion Hold

Upstream technical acceptance is complete for this exact module SHA and reported
tested consumer snapshot only. The consumer remains 11/12 complete with task 4.3
open: final receipt/source/base reconciliation and consumer publication identity
are not yet established. Current consumer HEAD is its base, not accepted changes;
the ignored KCL lock and temporary metadata receipts are not durable published
consumer artifacts. External backend-template custody remains separately owned.

Moved code, pins, runtime, policy, backend or bases require affected checks to be
reconciled or repeated under the appropriate authorization. Do not automatically
replay live checks or restore the old disabled-locking setting. No consumer
promotion, Git commit/push, merge, release, deployment, state operation, spec sync
or archive is authorized or performed by this evidence reconciliation. DLR-1,
community-provider adoption and Actions canary work remain separately scoped.

## Closeout Requalification And Explicit Evidence Reuse, 2026-11-15

The downstream's final archived receipt at
`<consumer-worktree>/openspec/changes/archive/2026-11-15-adopt-modernized-dns-dagger-workspace/verification.md`
records task 4.3 complete, all 12 tasks checked, the same tested source
fingerprint and a scoped comparison of the moved consumer production base.
Its archive-before-publication timing was separately selected by the operator;
the consumer implementation remains uncommitted. This resolves the previous
task-4.3 hold, not its future Git/deployment closeout.

The user then authorized upstream archive and squash/merge with **no release or
tag**, and separately approved preserving tested source
`614c6aea5e2c92417e4e7d08882ccdcb4113eb33` at remote branch
`accepted/dagger-614c6ae`. That ref was created and read back at the exact SHA.
It must survive feature history rewriting because the real consumer still pins
that commit; no consumer source or routing was changed here.

Archive readiness found that a syntactically dotted numeric IP such as
`192.168.100.100` passed the hostname checker when its allowlist entry was
unused, contrary to the existing spec. The user approved fixing and requalifying
before archive. `SplitDNSOrigin` now uses the native `net.is_IP` parser on the
normalized hostname. Twenty new cases reject IPv4, root-dotted IPv4, IPv6 and
IPv4-mapped IPv6 declarations across all five entry points, including otherwise
safe origins that require no exception.

Concurrent, unrelated canary work appeared in the primary checkout during this
check. The user chose an isolated native Git worktree:
`/home/solomong/Code/Misc/.worktrees/unifi-cloudflare-glue/closeout-dagger-execution-contracts`,
branch `change/closeout-dagger-execution-contracts`. Only this operation's seven
owned file changes were transferred. The primary checkout, its dirty canary
work, original branch, ignored files and preserved planning copy were not
reformatted, stashed, reset, moved or selected for deletion.

The isolated full local and pinned-Dagger verification both passed **613 tests
with no skips**, Black/isort, mypy for eight source files, compilation and all
seven KCL entry points. Qualified SDK/schema generation passed. Provider source,
execution code, launchers and dependency locks are byte-unchanged from the
accepted source. The functional guard and tests were committed/pushed separately
as `e8777e968f83fb7b8de82ccbd245b7f918ca20fa` for exact-revision checks.

Credential-free remote consumer requalification used a disposable, allowlisted
public-input-only fixture under
`/tmp/kilo/gh-squash-dagger-RGWFvU/consumer-qualification`, not an edit to the real
consumer. Its KCL source was byte-identical to the real consumer. Only fixture
source refs and their expected-SHA test constants selected the new candidate;
KCL acquisition generated its genuine new resolution lock. Git baseline reads
used a read-only object alternate, never the real index or refs. The fixture
contained no backend files, credentials, raw state or live plan artifacts, and
test subprocesses received only a reviewed non-credential environment allowlist.

Native remote module update reported the full new SHA and discovery succeeded.
All **21 consumer checks passed again**: 10 source/runtime/guidance, 5
generation/parity and 6 synthetic Secret checks. Both remote providers generated
the unchanged consumer outputs twice, byte-identically, with full baseline
equality, 16 native negative cases, nine normalization cases and the existing
remote negative case. An additional actual remote check rejected a fourth,
unused literal-IP policy declaration without producing an output File, proving
that the revised remote guard, not only old cached positive output, executed.
No backend, provider or connector was contacted by these checks.

Requalification metadata/logs are retained under
`/tmp/kilo/gh-squash-dagger-RGWFvU/consumer-requalification.json` and
`consumer-*.log`; they are local evidence, not durable published artifacts.
The test harness is `requalify-public-consumer.py` in the same external state
directory. The real downstream declaration, source refs and routing stayed
unchanged; this is remote qualification of an isolated consumer fixture, not
actual downstream adoption of the new SHA.

The operator was explicitly told that live operation
`27fc831c-ed0c-43b8-be96-59970e55551e` tested `614c6aea...`, **not** the new
candidate. They selected **Accept bounded reuse**: accept those previously
recorded zero-drift and connector results only for the verified unchanged
execution inputs, with complete output parity and unchanged Terraform/provider/
execution/backend code, and finish archive/squash without a new production call.
This operation-specific decision is not an automatic rule for future code,
source, backend, routing or runtime changes. No new zero-drift preview or live
connector test is claimed for `e8777e9...`; future apply still independently
replans, and future consumer adoption must reconcile its own source identity.

Archive synchronization preserves all seven original deltas, including the
secret-safety Markdown delta that the broad `*secret*` ignore rule had left
untracked in the primary checkout. This is reviewed non-secret spec prose; it is
restored and explicitly staged only at its exact archive path, without relaxing
the ignore rule. Six main specs already carry the full semantic delta; only the
new runtime-compatibility capability needs creation, with its authored Purpose
and four requirements preserved. No unrelated main-spec debt or canary change
is included. No release, tag, production effect, consumer repin or unrelated
worktree cleanup is authorized by this closeout.
