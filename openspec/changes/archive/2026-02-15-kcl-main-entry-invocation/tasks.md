## 1. Modify generate_unifi_config()

- [x] 1.1 Replace file-existence check for `generators/unifi.k` with check for `main.k` in `src/main/main.py`
- [x] 1.2 Change KCL invocation from `kcl run generators/unifi.k` to `kcl run main.k`
- [x] 1.3 Write KCL output to temp file, then extract `.unifi_output` using `yq eval '.unifi_output'`
- [x] 1.4 Convert extracted YAML to JSON using `yq eval -o=json`
- [x] 1.5 Add null-check after `yq` extraction: if result is `null`, emit error explaining `main.k` must export `unifi_output`
- [x] 1.6 Update all error messages and hints in `generate_unifi_config()` to reference `main.k` instead of `generators/unifi.k`

## 2. Modify generate_cloudflare_config()

- [x] 2.1 Replace file-existence check for `generators/cloudflare.k` with check for `main.k` in `src/main/main.py`
- [x] 2.2 Change KCL invocation from `kcl run generators/cloudflare.k` to `kcl run main.k`
- [x] 2.3 Write KCL output to temp file, then extract `.cf_output` using `yq eval '.cf_output'`
- [x] 2.4 Convert extracted YAML to JSON using `yq eval -o=json`
- [x] 2.5 Add null-check after `yq` extraction: if result is `null`, emit error explaining `main.k` must export `cf_output`
- [x] 2.6 Update all error messages and hints in `generate_cloudflare_config()` to reference `main.k` instead of `generators/cloudflare.k`

## 3. Container tooling verification

- [x] 3.1 Verify the Dagger container base image (`kcllang/kcl`) includes `yq` (mikefarah/yq v4)
- [x] 3.2 If `yq` is not present, add `yq` installation step to the container setup in `src/main/main.py`

## 4. Test updates

- [x] 4.1 Update `tests/unit/test_generator_output.py` to reflect the new `main.k` invocation path
- [x] 4.2 Verify existing unit tests pass with the new invocation mechanism
- [x] 4.3 Add test case: `main.k` missing → clear error message
- [x] 4.4 Add test case: `main.k` exists but does not export `unifi_output` → clear error about missing key
- [x] 4.5 Add test case: `main.k` exists but does not export `cf_output` → clear error about missing key
- [x] 4.6 Add test case: valid `main.k` → JSON output matches expected schema for both providers

## 5. Documentation updates

- [x] 5.1 Update `README.md` — replace any references to `generators/unifi.k` and `generators/cloudflare.k` with `main.k`
- [x] 5.2 Update `kcl_README.md` — update quick-start and generator usage sections
- [x] 5.3 Update `docs/dagger-reference.md` — update function descriptions and examples
- [x] 5.4 Update `docs/troubleshooting.md` — update error message references and diagnostic hints
- [x] 5.5 Update example READMEs that reference generator file invocation patterns
- [x] 5.6 Document the consumer contract: `main.k` MUST export `unifi_output` and `cf_output` as public variables

## 6. Validation

- [x] 6.1 Run `dagger call generate-unifi-config --source=. export --path=./unifi.json` locally and verify output
- [x] 6.2 Run `dagger call generate-cloudflare-config --source=. export --path=./cloudflare.json` locally and verify output
- [x] 6.3 Compare JSON output with previous generator output to confirm structural equivalence
- [x] 6.4 Verify no SIGSEGV crash with KCL v0.12.x by running against a consumer project with git dependencies
