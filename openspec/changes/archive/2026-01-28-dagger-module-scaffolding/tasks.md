# Tasks: Dagger Module Scaffolding

## Implementation Tasks

- [x] Create `dagger.json` at repository root
  - Set `name` to "unifi-cloudflare-glue"
  - Set `engineVersion` to "v0.19.7"
  - Set `sdk.source` to "python"

- [x] Create `pyproject.toml` at repository root
  - Configure `[build-system]` with `uv_build>=0.8.4,<0.9.0`
  - Set `[project].name` to "main"
  - Set `[project].requires-python` to ">=3.11"
  - Add `dagger-io` to `[project].dependencies`
  - Configure `[tool.uv.sources]` with local SDK path

- [x] Create `src/main/__init__.py`
  - Export `UnifiCloudflareGlue` class from main module

- [x] Create `src/main/main.py`
  - Add module docstring
  - Import `dagger` and decorators
  - Define `@object_type` class `UnifiCloudflareGlue`
  - Add `hello` function for verification
  - Add `test_integration` function for integration testing

- [x] Update `.gitignore` with Dagger artifacts
  - Add `/sdk/` (Dagger auto-generated SDK)
  - Add Python artifacts (`__pycache__/`, `*.pyc`, etc.)
  - Add virtual environment entries (`.venv/`, `/.env`)

## Verification Tasks

- [x] Run `dagger functions` and verify:
  - No errors about missing files
  - Class `UnifiCloudflareGlue` is displayed
  - Placeholder function is listed

- [x] Run `dagger call hello` and verify:
  - Command executes successfully
  - Returns expected greeting message

## Dependencies

- Python 3.11+
- Dagger engine v0.19.0+

## Notes

- Class name must be `UnifiCloudflareGlue` (PascalCase of module name)
- Build system must be `uv_build` (not hatchling/setuptools)
- Project name must be "main" in pyproject.toml
- Module must be at repository root for git functions to work
- The `src/main/__init__.py` must export the class for Dagger to find it
