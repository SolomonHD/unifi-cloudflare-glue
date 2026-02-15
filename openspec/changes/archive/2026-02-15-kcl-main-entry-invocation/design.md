## Context

The Dagger module (`src/main/main.py`) currently invokes KCL generators by running individual `.k` files:

- `generate_unifi_config()` → `kcl run generators/unifi.k`
- `generate_cloudflare_config()` → `kcl run generators/cloudflare.k`

KCL v0.12.x introduced a SIGSEGV crash when running any `.k` file other than the module entry point from a project that imports schemas via git dependencies. Running `kcl run main.k` is unaffected because KCL treats the module entry point differently in its Rust/CGO layer.

Consumer projects already define a `main.k` that imports both generators and exports `unifi_output` and `cf_output` as public variables. The full YAML output from `kcl run main.k` therefore already contains both provider sections.

## Goals / Non-Goals

**Goals:**
- Eliminate SIGSEGV crashes by switching all KCL invocations to `kcl run main.k`
- Extract per-provider JSON using `yq` from the unified YAML output
- Maintain identical JSON output format so downstream Terraform consumption is unaffected
- Provide clear error messages when `main.k` is missing or doesn't export expected variables

**Non-Goals:**
- Fixing the upstream KCL v0.12.x SIGSEGV bug
- Changing KCL schemas, generators, or Terraform modules
- Requiring consumer-side changes (consumers already export the needed variables)
- Optimizing KCL execution performance (running `main.k` once per function is acceptable for now)

## Decisions

### 1. Run `main.k` per-function (not shared)

**Choice:** Each of `generate_unifi_config()` and `generate_cloudflare_config()` runs `kcl run main.k` independently and extracts its own section.

**Alternative considered:** Run `main.k` once, cache the output, and extract both sections. Rejected because: (a) both functions may be called independently in different workflows (`deploy-unifi` vs `deploy-cloudflare`); (b) the Dagger container is ephemeral so there's no persistent cache across function calls; (c) the performance cost of running KCL twice is negligible compared to Terraform apply.

### 2. Use `yq` for YAML-to-JSON extraction

**Choice:** Pipe `kcl run main.k` output to a temp file, then use `yq eval '.unifi_output' file | yq eval -o=json` to extract and convert.

**Alternative considered:** Parse the YAML in Python using `pyyaml`. Rejected because: (a) the container already has `yq` available; (b) keeping extraction in shell commands matches the existing pattern of shelling out to `kcl`; (c) avoids adding a Python dependency on `pyyaml`.

### 3. Check for `main.k` instead of generator files

**Choice:** Replace file-existence checks for `generators/unifi.k` and `generators/cloudflare.k` with a single check for `main.k`.

**Rationale:** The generators directory becomes dead code. Checking for `main.k` is the correct pre-flight validation since that's the only file we execute.

### 4. Validate extracted output is non-null

**Choice:** After `yq` extraction, check that the result is not `null` (which `yq` outputs when a key doesn't exist). If the output key is missing, emit a descriptive error explaining the consumer's `main.k` must export `unifi_output` / `cf_output`.

**Rationale:** This catches the case where a consumer has a `main.k` but hasn't updated it to export the expected variables.

## Risks / Trade-offs

- **[Risk] Consumer `main.k` doesn't export expected variables** → Mitigated by the null-check after `yq` extraction, which produces a clear error message explaining what's needed.
- **[Risk] `yq` version differences** → Mitigated by using the `mikefarah/yq` v4 syntax which is standard in the KCL container image. Document the expected `yq` version.
- **[Risk] Multi-document YAML output** → KCL `main.k` may produce multi-document YAML if multiple top-level configs exist. Mitigated by testing with `yq eval` which handles the first document by default. If multi-document is a concern, use `yq eval-all`.
- **[Trade-off] Double execution** → Running `main.k` twice (once per provider) in the `deploy` workflow is slightly less efficient than running once. Acceptable given deployment time is dominated by Terraform apply, not KCL evaluation.
- **[Trade-off] `generators/` directory becomes dead code** → Consumer projects retain the directory but it's no longer invoked by the Dagger module. Not a breaking change but should be documented.

## Open Questions

- Should the `generators/` directory invocation be kept as a fallback if `main.k` doesn't exist? (Recommendation: No — clean break avoids complexity, and the SIGSEGV bug makes the old path unreliable.)
- Should `yq` be explicitly installed in the Dagger container or rely on the KCL image including it? (Need to verify the base image contents.)
