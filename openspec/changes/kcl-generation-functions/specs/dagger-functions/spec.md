# Spec: Dagger KCL Generation Functions

## ADDED Requirements

### Requirement: generate_unifi_config Function

The Dagger module SHALL provide a `generate_unifi_config` function that runs the KCL UniFi generator in a containerized environment and returns the generated JSON as a `dagger.File`.

#### Scenario: Generate UniFi JSON from KCL
Given a valid KCL module directory containing UniFi configuration
When the `generate_unifi_config` function is called with the source directory
Then it returns a `dagger.File` containing the generated UniFi JSON configuration

#### Scenario: Container Environment
Given any source directory input
When the function executes KCL
Then it uses the official `kcllang/kcl` container image with the source mounted at `/src`

#### Scenario: KCL Module Validation
Given a source directory without `kcl.mod`
When the function is called
Then it returns a clear error message indicating the directory is not a valid KCL module

#### Scenario: Generator File Validation
Given a source directory without `generators/unifi.k`
When the function is called
Then it returns a clear error message indicating the generator file is missing

#### Scenario: KCL Execution Error Handling
Given a KCL module with syntax errors
When the function runs the generator
Then it captures stderr and returns an error message with debugging details

---

### Requirement: generate_cloudflare_config Function

The Dagger module SHALL provide a `generate_cloudflare_config` function that runs the KCL Cloudflare generator in a containerized environment and returns the generated JSON as a `dagger.File`.

#### Scenario: Generate Cloudflare JSON from KCL
Given a valid KCL module directory containing Cloudflare configuration
When the `generate_cloudflare_config` function is called with the source directory
Then it returns a `dagger.File` containing the generated Cloudflare JSON configuration

#### Scenario: Container Environment
Given any source directory input
When the function executes KCL
Then it uses the official `kcllang/kcl` container image with the source mounted at `/src`

#### Scenario: KCL Module Validation
Given a source directory without `kcl.mod`
When the function is called
Then it returns a clear error message indicating the directory is not a valid KCL module

#### Scenario: Generator File Validation
Given a source directory without `generators/cloudflare.k`
When the function is called
Then it returns a clear error message indicating the generator file is missing

#### Scenario: KCL Execution Error Handling
Given a KCL module with syntax errors
When the function runs the generator
Then it captures stderr and returns an error message with debugging details

---

### Requirement: Function Documentation

All Dagger functions SHALL include comprehensive documentation following Python best practices and Dagger conventions.

#### Scenario: Docstring Completeness
Given the implemented functions
When viewed via `dagger functions` or help text
Then they display comprehensive docstrings describing purpose, parameters, and return values

#### Scenario: Parameter Documentation
Given any function parameter
When viewed in help or IDE
Then it has a descriptive docstring via `Annotated[type, Doc("...")]` explaining the parameter's purpose

---

### Requirement: Return Value Contract

The generator functions SHALL return `dagger.File` objects containing valid JSON that matches the respective Terraform module input schemas.

#### Scenario: File Object Return
Given successful execution of either generator function
When the function completes
Then it returns a valid `dagger.File` object containing valid JSON

#### Scenario: JSON Output Validity
Given successful execution
When the returned file is read
Then it contains valid parseable JSON matching the Terraform module input schema
