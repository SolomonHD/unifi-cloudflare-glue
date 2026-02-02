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
4. Update documentation if needed
5. Submit a pull request

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

Follow these steps to create a new release:

### 1. Prepare the Release

1. Ensure all changes are merged to the main branch
2. Update the `CHANGELOG.md` with the new version section
3. Run tests to ensure everything works:
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

### 2. Update Version Files

Update the version in the following files:

1. **`VERSION`** - Root version file (e.g., `0.1.0`)
2. **`pyproject.toml`** - Python package version
3. **`kcl/kcl.mod`** - KCL module version
4. **`terraform/modules/unifi-dns/versions.tf`** - Module version comment
5. **`terraform/modules/cloudflare-tunnel/versions.tf`** - Module version comment

### 3. Create a Git Tag

Git tags use the `v` prefix (per Dagger conventions):

```bash
# Create an annotated tag
git tag -a v0.1.0 -m "Release version 0.1.0"

# Push the tag
git push origin v0.1.0
```

### 4. Verify the Release

1. Verify the version function works:
   ```bash
   dagger call version --source=.
   ```

2. Verify the tag exists:
   ```bash
   git tag | grep v0.1.0
   ```

3. Check that all version references are consistent:
   ```bash
   cat VERSION
   grep "version" pyproject.toml
   grep "version" kcl/kcl.mod
   ```

### 5. Document the Release

1. Ensure `CHANGELOG.md` has an entry for the new version
2. Update `README.md` if needed with new version references
3. Create a GitHub release (if using GitHub) with release notes

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
