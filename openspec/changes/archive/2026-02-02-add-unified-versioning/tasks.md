# Tasks: Add Unified Versioning

## File Creation

- [x] Create `VERSION` file at repository root with content `0.1.0` and LF ending
- [x] Create or update `.gitattributes` with entry `VERSION text eol=lf`
- [x] Create `CONTRIBUTING.md` with release process documentation (if it doesn't exist)

## Version Synchronization

- [x] Update `pyproject.toml` version from `0.0.0` to `0.1.0`
- [x] Verify `kcl/kcl.mod` version is `0.1.0` (already correct per kcl/kcl.mod:4)

## Terraform Module Metadata

- [x] Add version comment header to `terraform/modules/unifi-dns/versions.tf`
- [x] Add version comment header to `terraform/modules/cloudflare-tunnel/versions.tf`
- [x] Verify both version headers reference correct GitHub URL with v0.1.0 tag

## Dagger Function

- [x] Add `version()` function to `src/main/main.py` in `UnifiCloudflareGlue` class
- [x] Function accepts `source: dagger.Directory` parameter (required, per dagger-coding-rules.md)
- [x] Function reads VERSION file from source directory
- [x] Function returns stripped version string
- [x] Add comprehensive docstring with usage examples
- [x] Use `Annotated[dagger.Directory, Doc("Source directory containing VERSION file")]` annotation

## Documentation Updates

- [x] Add "Versioning" section to `README.md` explaining strategy
- [x] Add current version reference in `README.md`
- [x] Add version query example to `README.md`: `dagger call version --source=.`
- [x] Add version pinning examples to `README.md`
- [x] Add "Release Process" section to `CONTRIBUTING.md` with step-by-step workflow
- [x] Add semantic versioning guidance to `CONTRIBUTING.md`
- [x] Verify `CHANGELOG.md` [0.1.0] section exists (already present per CHANGELOG.md:83)

## Validation

- [x] Verify VERSION file reads correctly: `cat VERSION`
- [x] Verify all version references match: grep for `0.0.0` and ensure all are updated
- [x] Test Dagger version function: `dagger call version --source=.`
- [x] Verify dagger functions output includes version function
- [x] Run `terraform fmt` on both modules to ensure version comments preserved
- [x] Verify git tracks VERSION file: `git status` should show it

## Dependencies

- Tasks in "File Creation" should be completed first
- "Version Synchronization" can happen in parallel with "Terraform Module Metadata"
- "Dagger Function" depends on VERSION file existing
- "Documentation Updates" should be done after all implementation tasks
- "Validation" should be last
