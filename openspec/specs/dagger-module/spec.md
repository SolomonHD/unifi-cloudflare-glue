# Spec: Dagger Module Scaffolding

## Overview

This specification defines the requirements for initializing a Dagger Python module at the repository root of the unifi-cloudflare-glue project.

## ADDED Requirements

### Requirement: Dagger Module Manifest

The Dagger module SHALL have a `dagger.json` manifest file at the repository root with correct configuration.

#### Scenario: dagger.json exists at repository root
Given: The repository root directory exists
When: Dagger module initialization is complete
Then: A `dagger.json` file exists at the repository root with:
  - `name`: "unifi-cloudflare-glue"
  - `engineVersion`: "v0.19.7" or higher
  - `sdk.source`: "python"

### Requirement: Python Project Configuration

The Dagger module SHALL have a `pyproject.toml` with the correct build system and dependencies.

#### Scenario: pyproject.toml with uv_build backend
Given: The Dagger module requires Python tooling
When: The project configuration is created
Then: A `pyproject.toml` file exists with:
  - `[build-system]` using `uv_build>=0.8.4,<0.9.0`
  - `[project].name`: "main" (required by Dagger)
  - `[project].requires-python`: ">=3.11"
  - `[tool.uv.sources]` with dagger-io pointing to local SDK path
  - `[project].dependencies` includes "dagger-io"

### Requirement: Python Module Structure

The Dagger module SHALL have a standard Python package structure under `src/unifi_cloudflare_glue/`.

#### Scenario: src/unifi_cloudflare_glue directory exists
Given: The Dagger module requires Python source files
When: The module structure is created
Then: The directory `src/unifi_cloudflare_glue/` exists with:
  - `__init__.py` (empty or with minimal exports)
  - `main.py` containing the Dagger class definition

### Requirement: Dagger Class Skeleton

The Dagger module SHALL have a properly named class decorated with `@object_type` in `main.py`.

#### Scenario: UnifiCloudflareGlue class in main.py
Given: The Python module structure exists
When: The main.py file is created
Then: The file contains:
  ```python
  """Dagger module for unifi-cloudflare-glue"""
  
  import dagger
  from dagger import function, object_type
  
  @object_type
  class UnifiCloudflareGlue:
      """Dagger module for managing hybrid DNS infrastructure"""
      
      @function
      def hello(self) -> str:
          """Placeholder function for module verification"""
          return "Hello from unifi-cloudflare-glue!"
  ```

### Requirement: Gitignore Updates

The repository `.gitignore` SHALL be updated to exclude Dagger and Python artifacts.

#### Scenario: .gitignore includes Dagger artifacts
Given: The repository has an existing `.gitignore` file
When: The Dagger module scaffolding is complete
Then: The `.gitignore` file contains entries for:
  - `/sdk/` (Dagger auto-generated SDK)
  - `__pycache__/` (Python cache)
  - `*.py[cod]` (Python bytecode)
  - `*.egg-info/` (Python package metadata)
  - `.venv/` (Python virtual environment)
  - `/.env` (Environment files)

### Requirement: Module Verification

The Dagger module SHALL be loadable and display its functions when running `dagger functions`.

#### Scenario: dagger functions shows the module
Given: All scaffolding files are in place
When: The command `dagger functions` is executed from the repository root
Then: The output shows:
  - Class name: `UnifiCloudflareGlue`
  - Function: `hello`
  - No errors or warnings about missing files

## Constraints

1. **Module Location**: Dagger module must be at repository root for git-related functions to work properly
2. **Class Name**: Must match PascalCase conversion of module name: `unifi-cloudflare-glue` → `UnifiCloudflareGlue`
3. **Build System**: Must use `uv_build` (not hatchling/setuptools)
4. **Project Name**: Must be "main" in pyproject.toml (Dagger requirement)
