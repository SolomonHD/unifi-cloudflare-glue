# Offline Verification

The credential-free Dagger entry point runs `scripts/verify-offline.sh`, the
same authoritative baseline used directly on a prepared workstation. It does
not call integration/live canary functions or initialize Terraform or a backend.
The complete unit suite includes real KCL fixture generation, schema contracts,
synthetic transport failures and secret sentinels. No markers are excluded.

## Qualified Invocation

Use the exact CLI, engine and generated Python clients recorded in
[Dagger runtime qualification](dagger-runtime-qualification.md). From the
repository root, the public adapter is invoked as follows:

```bash
bash scripts/dagger-qualified.sh api call -m . verify-offline --source=.
```

The wrapper verifies the Linux/amd64 CLI checksum and selects the pinned engine
without changing global selection. On another runner, bootstrap that exact
verified CLI separately and set `DAGGER_BIN` to its executable path.
This is beta `api call` syntax, not the stable CLI's `call` syntax. Generated
`sdk/`, `clients/core/`, the Dagger lock and `uv.lock` must already be present;
verification does not migrate manifests or regenerate the SDK.

## Bootstrap Versus Checks

The helper `offline_verification_container(source)` constructs two sequential
stages. Bootstrap pulls immutable image identities and runs `uv sync --frozen`,
including the exactly pinned development group and transitive `uv.lock` entries.
It does not independently resolve `--with` tools. Bootstrap can access
image registries and Python package indexes. It must complete before checks.
There is no caller credential, service binding or privileged nested Dagger.

The verification stage sets `UV_OFFLINE=true` and disables automatic Python
downloads. The wrapper passes `--offline --frozen --no-sync`. Missing cached Python
requirements therefore fail rather than trigger a download. Root KCL imports
are repository-local; `kcl.mod` currently has no external dependencies. No
`kcl mod update` runs. Adding external KCL dependencies requires a separately
qualified, frozen bootstrap policy before calling them offline.

Bootstrap uses Python 3.12 from the reviewed digest, copies `/usr/local/bin/uv`
from the pinned UV image, and copies the verified `kcl_binary()` from the shared
toolchain helper. That helper downloads the official KCL 0.12.4 linux-amd64
release archive, verifies SHA-256
`01dc1d8914ed8fdfac7e8b34cc155227cf7f155ef8760f741f35b0f8529f08ca`,
and extracts the compiler on the pinned Python/glibc runtime.
It also copies the reviewed Terraform 1.13.5 executable so native HCL
round-trip tests cannot silently skip for a missing parser/evaluator.
Verification explicitly selects `linux/amd64`, matching that qualified binary;
other architectures require their own compiler identity and acceptance.
It records each executable's version before installing requirements. The UV
image's `python3.14-alpine` label does not select the verification interpreter:
only its standalone UV executable is copied.

**Rejected KCL image:** the originally requested `kcllang/kcl:v0.12.4` image at
`sha256:fdf0833512f277a2de3cfeef6c1b333744c9834aceca032581826de30a770216`
reports `0.12.3` from `kcl version`. Its tag is not proof of executable 0.12.4.
The shared toolchain uses the exact official 0.12.4 binary instead. The native
compiler version test must still pass; the misleading tag is not accepted as
local/CI version agreement.

Offline describes the supported verification commands, not a network-isolation
sandbox. Dagger still needs an engine connection and may need bootstrap cache
material on a cold runner. Its exec API here does not disable all networking.
Do not supply untrusted tests or production configuration to this entry point.

## Scope And Outputs

The container receives an allowlisted copy of Python/SDK files, unit tests and
synthetic fixtures, KCL schemas/entry points, Terraform source fixtures and the
baseline wrapper. It excludes `.env` files, backend configuration, Terraform
state and saved plan paths. No host environment or secret input is forwarded.
The caller is responsible for keeping credentials out of source code and test
fixtures; filename filtering cannot identify arbitrary secrets embedded there.

Checks cover Black and isort for `src`/`tests`, mypy for production Python,
compilation, every `tests/unit` test, then all seven baseline KCL entry points:
`main.k`, `test_validation.k`, `test_error_validation.k`, `test_error_format.k`,
`test_cloudflare.k`, `generators/unifi.k`, and `generators/cloudflare.k`.
An unsuccessful command fails the Dagger call with nonzero status. The helper
does not catch errors and turn them into successful report strings.

Only check output is returned. Container-local virtual environments, bytecode,
temporary synthetic fixtures and caches are not checkout writes. No Directory,
Changeset, raw state or raw plan is exported. Non-sensitive configuration
generation and explicit checkout-export adapters are separate entry points;
their acceptance is not established by this verification helper.

Direct workstation usage remains:

```bash
bash scripts/verify-offline.sh
```

Prepare the same frozen project requirements and exact test tooling first as
described in `CONTRIBUTING.md`. Local execution uses the local KCL binary and
does not need a Dagger engine. Both routes intentionally retain real failures,
including SDK/mypy compatibility failures, instead of dropping checks to pass.

## Verification Evidence

On 2026-11-14, a direct helper probe through the qualified beta CLI's
`api with-session` loaded the real generated `core()` API. Its initial run
failed before checks because the supplied UV image has no `/uv`; the pinned
image was inspected and the copy path corrected to `/usr/local/bin/uv`.
A bootstrap-only probe then passed with the pinned Python/UV images, frozen
project resolution, every exact test-tool pin and the real source projection.
It imported the test tools plus `dagger_clients.core` successfully. After the
shared toolchain correction, a full-helper smoke downloaded checksum-verified
release bytes, checked the actual KCL version as 0.12.4 and completed bootstrap.
Its offline baseline correctly failed with exit 1 at Black on in-progress
source files; the failed check propagated through a real Dagger `ExecError`.
This is bootstrap/failure-path acceptance, not a full-suite pass.

A separate actual-engine projection probe retained a synthetic source file
while excluding `.env`, `.env.production`, state and state-backup files,
saved plans, backend input and a live integration-test path, including files
deliberately placed under otherwise included source directories.

The owned unit tests exercise immutable graph construction and execute the
actual final bash argv with synthetic success and exit-7 failures. Final local
and public Dagger runs both passed all 474 tests without skips, Black/isort,
mypy for eight source files, compilation and all seven KCL entry points.
The first container pass had five missing-Terraform skips; it was rejected,
then rerun successfully after adding the already-pinned executable.
Public generation/File-export adapters also passed against synthetic UniFi
and Cloudflare outputs, exporting only the explicitly selected non-secret
files under `/tmp/kilo`. No checks were dropped or marked expected-failure.
Remote sibling-consumer and production-read acceptance remain separate gates.
