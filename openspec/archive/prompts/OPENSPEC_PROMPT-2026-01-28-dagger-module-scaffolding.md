# OpenSpec Change Prompt: Dagger Module Scaffolding

## Context

The `unifi-cloudflare-glue` repository manages hybrid DNS infrastructure bridging UniFi local DNS with Cloudflare Tunnel edge DNS. Currently, users must manually run KCL generators and Terraform commands. We want to add Dagger CLI functions to enable containerized, reproducible pipelines.

**Critical requirement**: Dagger must be initialized at the **repository base** (where `.git/` lives) for git-related functions to work properly.

## Goal

Initialize a Dagger Python module at the repository root with proper structure, naming conventions, and tooling setup.

## Scope

**In scope:**
- Initialize Dagger module at repository base (`unifi-cloudflare-glue/`)
- Create `dagger.json` with proper module name
- Create `pyproject.toml` with correct build system (uv_build)
- Set up Python module structure in `src/unifi_cloudflare_glue/`
- Create basic `main.py` with class skeleton
- Update `.gitignore` for Dagger artifacts
- Ensure class name matches Dagger's expectation

**Out of scope:**
- Implementing actual functions (future prompts)
- KCL or Terraform modifications
- Documentation beyond basic docstrings

## Desired Behavior

1. **Module Location**: Dagger module lives at repo root (`unifi-cloudflare-glue/dagger.json`)
2. **Module Name**: `unifi-cloudflare-glue` in `dagger.json`
3. **Class Name**: `UnifiCloudflareGlue` (PascalCase conversion of module name)
4. **Python Structure**: Standard Dagger Python module layout
5. **Build System**: Use `uv_build` backend (not hatchling/setuptools)
6. **Project Name**: Must be "main" in `pyproject.toml`
7. **Verification**: `dagger functions` should show the class without errors

## Constraints & Assumptions

- Repository root contains `.git/` directory
- Python 3.11+ available
- Dagger engine v0.19.0+ required
- Use modern SDK format: `"sdk": {"source": "python"}`
- Follow Dagger module naming conventions (avoid "dagger-" prefix)
- Class name must match what `dagger functions` expects

## Acceptance Criteria

- [ ] `dagger.json` exists at repository root with:
  - `name`: "unifi-cloudflare-glue"
  - `engineVersion`: v0.19.7 or higher
  - `sdk.source`: "python"
- [ ] `pyproject.toml` exists with:
  - `[build-system]`: `uv_build>=0.8.4,<0.9.0`
  - `[project].name`: "main"
  - `[project].requires-python`: ">=3.11"
  - `[tool.uv.sources]`: dagger-io pointing to local sdk
- [ ] `src/unifi_cloudflare_glue/` directory with:
  - `__init__.py`
  - `main.py` with `class UnifiCloudflareGlue` skeleton
- [ ] `.gitignore` updated with:
  - `/sdk/` (Dagger auto-generated SDK)
  - `__pycache__/`, `*.pyc`
  - `.venv/`, `/.env`
- [ ] `dagger functions` runs without errors and shows `UnifiCloudflareGlue`

## Files to Create/Modify

**Create:**
- `dagger.json` (repo root)
- `pyproject.toml` (repo root)
- `src/unifi_cloudflare_glue/__init__.py`
- `src/unifi_cloudflare_glue/main.py`

**Modify:**
- `.gitignore` (append Dagger entries)

## Reference

- Existing project structure at `unifi-cloudflare-glue/`
- Dagger Python SDK documentation
- Rule file: `dagger.md` (module naming conventions)

## Open Questions

None - this is a straightforward scaffolding task.
