# Proposal: Dagger Module Scaffolding

## Summary

Initialize a Dagger Python module at the repository root to enable containerized, reproducible pipelines for the unifi-cloudflare-glue project. This provides the foundation for future Dagger CLI functions that will automate KCL generation, Terraform deployment, and integration testing.

## Motivation

Currently, users must manually run KCL generators and Terraform commands to manage the hybrid DNS infrastructure. By introducing Dagger, we can:

- Provide containerized, reproducible pipeline execution
- Simplify CI/CD integration
- Ensure consistent environments across development and production
- Enable remote execution without local tool installation

## Scope

### In Scope

- Initialize Dagger module at repository base (`unifi-cloudflare-glue/`)
- Create `dagger.json` with proper module name
- Create `pyproject.toml` with correct build system (uv_build)
- Set up Python module structure in `src/unifi_cloudflare_glue/`
- Create basic `main.py` with class skeleton
- Update `.gitignore` for Dagger artifacts
- Ensure class name matches Dagger's expectation

### Out of Scope

- Implementing actual functions (handled in future prompts: 02, 03, 04)
- KCL or Terraform modifications
- Documentation beyond basic docstrings

## Design Overview

### Module Configuration

- **Module Location**: Dagger module lives at repo root (`unifi-cloudflare-glue/dagger.json`)
- **Module Name**: `unifi-cloudflare-glue` in `dagger.json`
- **Class Name**: `UnifiCloudflareGlue` (PascalCase conversion of module name)
- **Build System**: `uv_build` backend (not hatchling/setuptools)
- **Project Name**: Must be "main" in `pyproject.toml`

### File Structure

```
unifi-cloudflare-glue/
├── dagger.json                      # Dagger module manifest
├── pyproject.toml                   # Python project config
├── src/
│   └── unifi_cloudflare_glue/       # Python module
│       ├── __init__.py              # Module init
│       └── main.py                  # Dagger class skeleton
└── .gitignore                       # Updated for Dagger artifacts
```

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
  - Python artifacts (`__pycache__/`, `*.pyc`, etc.)
  - `.venv/`, `/.env`
- [ ] `dagger functions` runs without errors and shows `UnifiCloudflareGlue`

## Dependencies

- Python 3.11+
- Dagger engine v0.19.0+

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Wrong class name causing `dagger functions` to fail | Use correct PascalCase: `UnifiCloudflareGlue` |
| Incorrect build system causing import errors | Use `uv_build` as specified in Dagger docs |
| Git-related functions not working | Ensure Dagger is initialized at repo base where `.git/` lives |

## References

- Dagger Python SDK documentation
- Rule file: `dagger.md` (module naming conventions)
- Prompt: `openspec/prompts/01-dagger-module-scaffolding.md`
