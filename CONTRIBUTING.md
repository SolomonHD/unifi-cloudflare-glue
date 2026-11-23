# Contributing to unifi-cloudflare-glue

Thank you for your interest in contributing to unifi-cloudflare-glue! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/SolomonHD/unifi-cloudflare-glue.git
   cd unifi-cloudflare-glue
   ```

2. Prepare Python 3.11+, `uv`, and exact KCL 0.12.4 for the local baseline.
   Do not install a moving latest release. Container execution uses the official
   checksum-verified KCL archive and immutable tool identities in
   `src/main/toolchains.py`, including the Git-capable Python base (Git 2.39.5).

3. Use the repository launcher to select the beta.28 CLI and engine recorded in
   [the runtime receipt](docs/dagger-runtime-qualification.md).
   ```bash
   bash scripts/dagger-qualified.sh api call -m . hello
   uv sync --frozen
   ```

Retain the migrated `dagger.toml`, `dagger-module.toml`, `dagger.lock`, generated
`sdk/` and `clients/core/` workspace packages and `uv.lock`. A normal checkout
does not need legacy `dagger develop`. Intentional SDK regeneration uses the
qualified beta `generate --auto-apply` workflow and requires reviewing the
resulting clients/locks, not regenerating them during production calls.

## Project Structure

The project consists of three tightly integrated components:

- **KCL Schemas** (`schemas/`, `generators/`, `main.k`): Library and generators
- **Terraform Modules** (`terraform/modules/`): Infrastructure modules
- **Dagger Module** (`src/main/main.py`): Containerized orchestration

All components share the same version number to ensure compatibility.

## Making Changes

1. Create a new branch for your changes
2. Make your modifications
3. Test your changes locally
4. Update documentation if needed (see [Documentation](#documentation))
5. Submit a pull request

## Documentation

Documentation is organized in the `docs/` directory:

- `docs/getting-started.md` - Installation and first deployment
- `docs/dagger-reference.md` - Complete function reference
- `docs/terraform-modules.md` - Standalone module usage
- `docs/state-management.md` - State backend options
- `docs/security.md` - Security best practices
- `docs/backend-configuration.md` - Backend configuration guide
- `docs/troubleshooting.md` - Troubleshooting guide
- `docs/README.md` - Documentation index
- `docs/execution-contracts.md` - Current supported caller/migration contract
- `docs/dagger-runtime-qualification.md` - Immutable runtime identities and evidence
- `docs/offline-verification.md` - Portable credential-free baseline

The root `README.md` is the current condensed entry point. Older topical guides
and `README.old.md` are background, not normative for migrated API syntax,
Secret transport, freshness, local custody or default artifacts.

When contributing:
- Update relevant docs/ files for feature changes
- Keep the README concise - add detailed content to appropriate docs/ files
- Ensure cross-links between related documentation work correctly
- Update `CHANGELOG.md` with user-facing changes

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.y.z): Breaking changes that require user intervention
- **MINOR** (x.Y.z): New features that are backward compatible
- **PATCH** (x.y.Z): Bug fixes and minor improvements

### Version Guidelines

Since all components (KCL, Terraform, Dagger) are tightly integrated and function as a cohesive system:

- **Breaking change in ANY component** → Major version bump
- **New feature in any component** → Minor version bump
- **Bug fix** → Patch version bump

Examples of breaking changes:
- KCL schema changes that require user configuration updates
- Terraform module variable changes
- Dagger function signature changes
- Changes to generated JSON output format

## Release Process

Follow these steps to create a new release. Use the comprehensive checklist below to ensure all version files are updated.

### Release Checklist

- [ ] 1.1 Prepare the Release
  - [ ] Ensure all changes are merged to the main branch
  - [ ] Update the `CHANGELOG.md` with the new version section
  - [ ] Run tests to ensure everything works:
    ```bash
    # Explicit sandbox mutation authorization is required; not a release smoke test.
    dagger --engine "$DAGGER_ENGINE" api call -m . test-integration \
        --source=. \
        --cloudflare-zone=test.example.com \
        --cloudflare-token=env://CF_TOKEN \
        --cloudflare-account-id=xxx \
        --unifi-url=https://unifi.local:8443 \
        --api-url=https://unifi.local:8443 \
        --unifi-api-key=env://UNIFI_API_KEY
    ```

- [ ] 1.2 Update Version Files

  Update the version in the following files. **Note: Use plain version without `v` prefix (e.g., `0.6.0`)**:

  - [ ] `VERSION` - Root version file (e.g., `0.6.0`)
    ```bash
    echo "0.6.0" > VERSION
    ```

  - [ ] `kcl.mod` - `[package].version` field
    ```bash
    # Update version field in kcl.mod
    ```

  - [ ] `pyproject.toml` - `[project].version` field
    ```bash
    # Update version field in pyproject.toml
    ```

  - [ ] `terraform/modules/unifi-dns/versions.tf` - Module version comment
    ```hcl
    # Version: 0.6.0
    ```

  - [ ] `terraform/modules/cloudflare-tunnel/versions.tf` - Module version comment
    ```hcl
    # Version: 0.6.0
    ```

  - [ ] `dagger.json` - `engineVersion` field (if applicable)
    This checklist label is historical: the migrated checkout uses
    `dagger.toml`, `dagger-module.toml`, `dagger.lock` and generated SDK/core
    clients. Runtime/SDK changes require their own qualification and are not
    a routine application version bump. Do not recreate `dagger.json` or
    substitute an unqualified engine version.

  - [ ] `examples/*/kcl.mod` - Git tag dependencies in examples

    Update git tag references in all example kcl.mod files:
    ```bash
    # Find all examples with git tag dependencies
    grep -r 'tag = "v' examples/

    # Update each to new version (e.g., v0.6.0 -> v0.7.0)
    ```

- [ ] 1.3 Version Format Conventions

  **Important: Version format varies by location:**

  | Location | Format | Example |
  |----------|--------|---------|
  | VERSION file | Plain (no v prefix) | `0.6.0` |
  | kcl.mod `[package].version` | Plain (no v prefix) | `0.6.0` |
  | pyproject.toml `[project].version` | Plain (no v prefix) | `0.6.0` |
  | Git tags | With v prefix | `v0.6.0` |
  | kcl.mod dependencies (git tag) | With v prefix | `tag = "v0.6.0"` |
  | Dagger CLI/engine/SDK | Independently qualified immutable identities | See runtime receipt; not the application version |

- [ ] 1.4 Version Override Capability (Future)

  > **Note:** Version override capability is planned for future automation. When implemented, you will be able to specify different versions for specific components:
  >
  > No public `release` function or arbitrary runtime-version override is
  > supported. Existing tool-version parameters accept reviewed immutable pins
  > only; they do not resolve moving tags or unrelated example versions.
  >
  > Default behavior: All components use the same version.

- [ ] 1.5 Create Git Tag

  Git tags use the `v` prefix (per Dagger conventions):

  ```bash
  # Create an annotated tag
  git tag -a v0.6.0 -m "Release version 0.6.0"

  # Push the tag
  git push origin v0.6.0
  ```

- [ ] 1.6 Verify the Release

  - [ ] Verify the version function works:
    ```bash
    dagger --engine "$DAGGER_ENGINE" api call -m . version --source=.
    ```

  - [ ] Verify the tag exists:
    ```bash
    git tag | grep v0.6.0
    ```

  - [ ] Verify all version references are consistent (see verification commands below)

- [ ] 1.7 Search Verification

  Run these commands to ensure no old version references remain:

  ```bash
  # Replace 0.5.0 with the OLD version number
  OLD_VERSION="0.5.0"

  # Search for old version in all files
  grep -r "$OLD_VERSION" --include="*.tf" --include="*.md" --include="*.toml" --include="*.json" --include="*.k" --include="VERSION" .

  # Check specific files
  grep "version" pyproject.toml
  grep "version" kcl.mod
  cat VERSION

  # Check example kcl.mod files
  grep -r 'tag = "v' examples/
  ```

- [ ] 1.8 Document the Release

  - [ ] Ensure `CHANGELOG.md` has an entry for the new version
  - [ ] Update `README.md` if needed with new version references
  - [ ] Create a GitHub release (if using GitHub) with release notes

## Testing

### Authoritative Offline Baseline

From the repository root, run the complete baseline after bootstrap:

```bash
bash scripts/verify-offline.sh
```

The sequence checks Black and isort across `src` and `tests`, mypy for all
production Python, Python compilation, the **entire** `tests/unit` suite without
marker exclusions, and the root KCL schema/validation and standalone generator
entry points. KCL assertions make failed validation exit nonzero; `kcl test`
alone discovers no tests because these historical files are named `test_*.k`,
not `*_test.k`. The full unit suite includes the hardening sentinel and
failure-injection tests in `test_secret_safety.py` and normalized-provider
regressions in `test_unifi_provider_baseline.py`.

Offline means no infrastructure credentials, live infrastructure calls, or
dependency downloads during this sequence. It does not mean a fresh checkout
can bootstrap air-gapped. Unit transports are mocked; generator tests execute
the local KCL binary against synthetic fixtures. No Terraform apply, Dagger
engine, UniFi controller, Cloudflare API, backend, or 1Password access is used.

Bootstrap separately with Python 3.11+, `uv`, KCL 0.12.4, and the generated
Python SDK/core workspace packages corresponding to the committed beta
manifests and locks. Synchronize these packages before using `--no-sync`;
otherwise a previously prepared environment can still lack the generated core
client. Bootstrap may need network access; the checks below do not authorize
global runtime changes. Acquire/cache Python dependencies once:

```bash
uv sync --frozen
uv run --frozen --no-sync \
  --with pytest==9.2.0 --with pytest-asyncio==1.5.0 \
  --with black==26.10.1 --with isort==9.0.2 \
  --with mypy==2.4.1 --with types-PyYAML==6.0.12.20261113 \
  python -c 'import pytest, pytest_asyncio, black, isort, mypy, yaml, dagger'
```

The wrapper repeats those exact tool pins with `uv --offline --frozen` so a
missing prerequisite fails rather than silently downloading or skipping tests.
The PyYAML stubs are necessary for typed backend parsing. No global package
installation or project dependency change is needed.

### Integration Testing

Integration tests create and delete real resources. Run only under separate
authorization for a disposable target, never as part of offline verification:
```bash
dagger --engine "$DAGGER_ENGINE" api call -m . test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env://CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env://UNIFI_API_KEY \
    --test-mac-address=de:ad:be:ef:12:34
```

### Local KCL Testing

Test KCL schema changes:
```bash
kcl run generators/unifi.k
kcl run generators/cloudflare.k
```

Standalone generators export `result`. Dagger generation instead consumes a
consumer directory whose `main.k` exports `unifi_output` and/or `cf_output`.
The root library `main.k` is not such a consumer. Dedicated test fixtures keep
these contracts separate; do not add consumer outputs to the library to satisfy
a stale test.

Generation validates JSON field types against the existing Terraform input
structures before exporting a file. Malformed-output diagnostics identify field
paths and expected types without echoing values. Cloudflare KCL generation also
rejects resolved origins in the configured public zone, including explicit URLs
and entity-derived hostname overrides or fallbacks.

Deployment requires an explicit remote backend, Secret backend URI and explicit
yaml/hcl format; scope must match existing state ownership. Local previews do
not write back to the host. DLR-1 durable local effects remain deferred by
operator decision. Runtime guidance uses actual non-secret account/zone/backend
selections, but source/output placeholders are not recovered host paths.
Credential retrieval additionally requires protected-disclosure acknowledgement
and a separately authorized protected consumer, never ordinary stdout logs.

Live freshness is automatic at the function and exec boundaries. Optional run
labels are bounded non-secret metadata, not shell timestamps or authorization.
Preview/no-drift, full-pipeline execution, remote feature-consumer loading and
separately approved production-read acceptance are independent evidence gates.
Do not claim the remaining gates passed from an offline result or documentation
change. See [Execution Contracts](docs/execution-contracts.md) for migration.

## Code Style

### Python (Dagger Module)

- Follow PEP 8 guidelines
- Use type hints with `Annotated[..., Doc(...)]` for parameters
- Use typed `File`/`Directory` outputs for non-sensitive generated configuration;
  bounded status strings for successful orchestration; sanitized exceptions for failures
- Use `✓` for success and `✗` for failure in output
- All public functions must be `async`

### KCL

- Use explicit types for schema fields
- Use comprehensions instead of statement for-loops
- Keep check blocks simple (use lambda functions for complex validation)
- Document schemas with docstrings

### Terraform

- Use `terraform fmt` to format code
- Document variables in `variables.tf`
- Include version comments at the top of module files

## Commit Messages

Use conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/process changes

Example:
```
feat: add version function for querying module version

Adds a new Dagger function `version()` that reads the VERSION
file and returns the current module version.
```

## Getting Help

- Open an issue for bugs or feature requests
- Check existing issues and documentation before creating new ones
- Provide minimal reproducible examples for bug reports

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
