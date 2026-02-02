# Tasks: Add Unified Versioning

## File Creation

- [ ] Create `VERSION` file at repository root with content `0.1.0` and LF ending
- [ ] Create or update `.gitattributes` with entry `VERSION text eol=lf`
- [ ] Create `CONTRIBUTING.md` with release process documentation (if it doesn't exist)

## Version Synchronization

- [ ] Update `pyproject.toml` version from `0.0.0` to `0.1.0`
- [ ] Verify `kcl/kcl.mod` version is `0.1.0` (already correct per kcl/kcl.mod:4)

## Terraform Module Metadata

- [ ] Add version comment header to `terraform/modules/unifi-dns/versions.tf`
- [ ] Add version comment header to `terraform/modules/cloudflare-tunnel/versions.tf`
- [ ] Verify both version headers reference correct GitHub URL with v0.1.0 tag

## Dagger Function

- [ ] Add `version()` function to `src/main/main.py` in `UnifiCloudflareGlue` class
- [ ] Function accepts `source: dagger.Directory` parameter (required, per dagger-coding-rules.md)
- [ ] Function reads VERSION file from source directory
- [ ] Function returns stripped version string
- [ ] Add comprehensive docstring with usage examples
- [ ] Use `Annotated[dagger.Directory, Doc("Source directory containing VERSION file")]` annotation

## Documentation Updates

- [ ] Add "Versioning" section to `README.md` explaining strategy
- [ ] Add current version reference in `README.md`
- [ ] Add version query example to `README.md`: `dagger call version --source=.`
- [ ] Add version pinning examples to `README.md`
- [ ] Add "Release Process" section to `CONTRIBUTING.md` with step-by-step workflow
- [ ] Add semantic versioning guidance to `CONTRIBUTING.md`
- [ ] Verify `CHANGELOG.md` [0.1.0] section exists (already present per CHANGELOG.md:83)

## Validation

- [ ] Verify VERSION file reads correctly: `cat VERSION`
- [ ] Verify all version references match: grep for `0.0.0` and ensure all are updated
- [ ] Test Dagger version function: `dagger call version --source=.`
- [ ] Verify dagger functions output includes version function
- [ ] Run `terraform fmt` on both modules to ensure version comments preserved
- [ ] Verify git tracks VERSION file: `git status` should show it

## Dependencies

- Tasks in "File Creation" should be completed first
- "Version Synchronization" can happen in parallel with "Terraform Module Metadata"
- "Dagger Function" depends on VERSION file existing
- "Documentation Updates" should be done after all implementation tasks
- "Validation" should be last
