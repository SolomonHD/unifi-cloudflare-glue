# Spec Delta: Dagger Version Function

## ADDED Requirements

### Requirement: Version Query Function

The Dagger module SHALL provide a function to query the module version from the VERSION file.

#### Scenario: version() function exists
Given: The Dagger module main.py contains the UnifiCloudflareGlue class
When: The module is loaded via `dagger functions`
Then: A function named `version` is listed in the output
And: The function accepts a `source` parameter of type Directory
And: The function returns a string containing the version number

#### Scenario: version() returns VERSION file content
Given: The VERSION file at repository root contains `0.1.0`
And: The source directory is provided via `--source=.`
When: The command `dagger call version --source=.` is executed
Then: The function reads the VERSION file from the source directory
And: The function returns the string `0.1.0`
And: Leading and trailing whitespace is stripped from the result

#### Scenario: version() handles missing VERSION file
Given: The source directory does not contain a VERSION file
When: The command `dagger call version --source=.` is executed
Then: The function raises a clear error
And: The error message indicates VERSION file is missing

### Requirement: Function Implementation

The version function SHALL follow Dagger module best practices for implementation.

#### Scenario: Function signature follows conventions
Given: The version function is implemented in main.py
When: The function declaration is inspected
Then: The function is decorated with `@function`
And: The function is an async function
And: The `source` parameter is annotated with `Annotated[dagger.Directory, Doc("...")]`
And: The return type is `str`
And: The function has a comprehensive docstring

#### Scenario: Function docstring is informative
Given: The version function exists
When: Users view help via `dagger call version --help`
Then: The help text shows clear description: "Get the module version from VERSION file"
And: The `source` parameter description explains: "Source directory containing VERSION file"
And: The help indicates expected usage: `--source=.`

### Requirement: Function Behavior

The version function SHALL provide reliable version information in all contexts.

#### Scenario: Local development context
Given: A developer is working inside the repository
When: They run `dagger call version --source=.`
Then: The function reads VERSION from the local repository
And: Returns the current development version

#### Scenario: Installed module context
Given: The module is installed via `dagger install`
When: A user runs `dagger call -m unifi-cloudflare-glue version --source=.`
Then: The function reads VERSION from the user's project directory
And: Returns the user's project version (if they have one)
Or: Returns an error if VERSION file is not found in user's project

#### Scenario: Remote module context
Given: The module is called directly from GitHub
When: A user runs `dagger call -m github.com/user/repo@v0.1.0 unifi-cloudflare-glue version --source=.`
Then: The function reads VERSION from the specified source directory
And: Returns the version found there

### Requirement: Documentation Integration

The version function SHALL be documented in user-facing materials.

#### Scenario: README shows version query
Given: The README.md file documents module usage
When: Users read the README
Then: An example shows how to query version: `dagger call version --source=.`
And: The example explains the expected output

#### Scenario: Version function appears in function list
Given: Users want to discover available functions
When: They run `dagger functions`
Then: The output includes the `version` function
And: The description clearly indicates it returns the module version
