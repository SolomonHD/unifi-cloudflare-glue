# Contributing to unifi-cloudflare-glue

Thank you for your interest in contributing to unifi-cloudflare-glue! This document provides guidelines for contributing to the project.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/unifi-cloudflare-glue.git
   cd unifi-cloudflare-glue
   ```

2. Install KCL (if working with KCL schemas):
   ```bash
   curl -sSL https://kcl-lang.io/script/install-cli.sh | bash
   ```

3. Install Dagger (for testing Dagger functions):
   ```bash
   curl -L https://dl.dagger.io/dagger/install.sh | sh
   ```

## Project Structure

The project consists of three tightly integrated components:

- **KCL Schemas** (`kcl/`): Configuration schemas and generators
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

The root `README.md` is a condensed entry point (~200 lines) that links to detailed documentation.

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
    dagger call test-integration \
        --source=. \
        --cloudflare-zone=test.example.com \
        --cloudflare-token=env:CF_TOKEN \
        --cloudflare-account-id=xxx \
        --unifi-url=https://unifi.local:8443 \
        --api-url=https://unifi.local:8443 \
        --unifi-api-key=env:UNIFI_API_KEY
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
    ```json
    {
      "engineVersion": "v0.19.7"
    }
    ```

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
  | dagger.json engineVersion | With v prefix | `v0.19.7` |

- [ ] 1.4 Version Override Capability (Future)

  > **Note:** Version override capability is planned for future automation. When implemented, you will be able to specify different versions for specific components:
  >
  > ```bash
  > # Example (not yet implemented)
  > dagger call release --version=0.6.0 --kcl-version=0.5.0 --terraform-version=0.6.0
  > ```
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
    dagger call version --source=.
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

### Unit Testing

Run unit tests for Dagger functions:
```bash
cd src/main
python -m pytest tests/
```

### Integration Testing

Run the integration test against real APIs:
```bash
dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --test-mac-address=de:ad:be:ef:12:34
```

### Local KCL Testing

Test KCL schema changes:
```bash
cd kcl
kcl run generators/unifi.k
kcl run generators/cloudflare.k
```

## Code Style

### Python (Dagger Module)

- Follow PEP 8 guidelines
- Use type hints with `Annotated[..., Doc(...)]` for parameters
- All functions should return `str` for CLI compatibility
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
