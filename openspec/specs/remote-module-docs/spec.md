# Spec: Remote Module Documentation

## ADDED Requirements

### Requirement: Remote Module Usage Section

The README.md MUST include a dedicated section explaining how to use unifi-cloudflare-glue as a remote Dagger module without cloning the repository.

#### Scenario: Section placement in documentation
**Given:** A user reads the README.md from top to bottom  
**When:** They complete the "Quickstart" section  
**Then:** They encounter the "Using as a Dagger Module" section before reaching "Modules"  
**And:** The section explains remote module consumption patterns

#### Scenario: Section parallels existing structure
**Given:** README.md has a "Using as Terraform Modules" section  
**When:** A user compares the two sections  
**Then:** Both sections follow similar structure (installation → usage → patterns → examples)

### Requirement: Module Installation Documentation

The documentation MUST explain how to install the Dagger module for persistent use across commands.

#### Scenario: Installation command provided
**Given:** A user wants to use the module across multiple terminal sessions  
**When:** They read the "Using as a Dagger Module" section  
**Then:** They see the installation command:
```bash
dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0
```
**And:** The command includes version pinning with `@v0.2.0`

#### Scenario: Installation location explained
**Given:** A user installs the module  
**When:** They complete the installation  
**Then:** The documentation explains:
- Module is registered in the current project's dagger.json
- Module functions become available with `-m unifi-cloudflare-glue` flag
- Installation persists across terminal sessions

#### Scenario: Version selection guidance
**Given:** A user decides which version to install  
**When:** They read the installation section  
**Then:** The documentation recommends:
- Use `@vX.Y.Z` for production (specific version)
- Use `@main` for latest development version (not recommended for production)
- Check releases page for available versions

### Requirement: Parameter Distinction Documentation

The documentation MUST clearly explain the critical difference between `--source` and `--kcl-source` parameters to prevent user confusion.

#### Scenario: Source parameter purpose explained
**Given:** A user sees `--source=.` in local development examples  
**When:** They attempt to use it from their own repository  
**Then:** The documentation explains:
- `--source=.` reads the **module's** KCL files
- Only works when running from within the unifi-cloudflare-glue repository
- Used by module developers, not module users

#### Scenario: KCL source parameter purpose explained
**Given:** A user wants to provide their own configuration  
**When:** They read the remote usage documentation  
**Then:** The documentation explains:
- `--kcl-source=./your-config` reads the **user's** KCL files
- Points to the caller's configuration directory
- Required when using the module from external repositories

#### Scenario: Warning about parameter confusion
**Given:** A user might mistakenly use `--source=.` remotely  
**When:** They read the parameter distinction section  
**Then:** The documentation includes:
- Clear warning or important callout box
- Explanation that `--source=.` will fail in remote context
- Example showing correct `--kcl-source` usage

### Requirement: Function Usage Examples

The documentation MUST provide usage examples for all major Dagger functions with realistic parameters.

#### Scenario: Deploy function example
**Given:** A user wants to deploy both UniFi and Cloudflare infrastructure  
**When:** They read the function examples  
**Then:** They see a complete `deploy` command with:
- `--kcl-source=./kcl` (user's configuration)
- UniFi authentication (API key or username/password)
- Cloudflare authentication (token, account ID, zone name)
- Optional state management parameters

#### Scenario: Deploy-unifi function example
**Given:** A user wants to deploy only UniFi DNS  
**When:** They read the function examples  
**Then:** They see a `deploy-unifi` command with:
- `--kcl-source=./kcl`
- UniFi authentication parameters
- Optional state management

#### Scenario: Deploy-cloudflare function example
**Given:** A user wants to deploy only Cloudflare Tunnel  
**When:** They read the function examples  
**Then:** They see a `deploy-cloudflare` command with:
- `--kcl-source=./kcl`
- Cloudflare authentication parameters
- Optional state management

#### Scenario: Destroy function example
**Given:** A user wants to tear down deployed infrastructure  
**When:** They read the function examples  
**Then:** They see a `destroy` command with:
- Same authentication parameters as deploy
- Same state management parameters as used for deployment
- Warning about destructive operation

#### Scenario: Plan function example
**Given:** A user wants to preview changes before apply  
**When:** They read the function examples  
**Then:** They see a `plan` command with:
- `--kcl-source=./kcl`
- Authentication parameters
- Export pattern: `export --path=./plans`

#### Scenario: Test-integration function example
**Given:** A user (or CI system) wants to run integration tests  
**When:** They read the function examples  
**Then:** They see a `test-integration` command with:
- `--kcl-source=./kcl`
- All required credentials
- Optional `--no-cache` flag for fresh test execution

### Requirement: Module Calling Patterns

The documentation MUST explain the three different patterns for calling Dagger module functions.

#### Scenario: Installed module pattern explained
**Given:** A user has run `dagger install`  
**When:** They want to call a function  
**Then:** The documentation shows:
```bash
dagger call -m unifi-cloudflare-glue deploy \
  --kcl-source=./kcl \
  --unifi-api-key=env:UNIFI_API_KEY \
  --cloudflare-token=env:CF_TOKEN \
  ...
```
**And:** Explains this is the most common pattern for local development

#### Scenario: Direct remote pattern explained
**Given:** A user wants to use the module without installing  
**When:** They read the calling patterns  
**Then:** The documentation shows:
```bash
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0 \
  unifi-cloudflare-glue deploy \
  --kcl-source=./kcl \
  ...
```
**And:** Explains:
- No installation required
- Full URL with version included
- Module name repeated after URL
- Useful for CI/CD pipelines

#### Scenario: Pattern comparison provided
**Given:** A user is choosing between patterns  
**When:** They read the documentation  
**Then:** A comparison table or list shows:
- **Installed**: Shorter commands, reusable, requires initial setup
- **Direct remote**: No installation, explicit versioning, longer commands
- **When to use each**: Local dev vs CI/CD vs one-off operations

### Requirement: Version Pinning Best Practices

The documentation MUST recommend version pinning for production usage and explain the benefits.

#### Scenario: Version pinning recommendation stated
**Given:** A user is setting up production infrastructure  
**When:** They read the best practices section  
**Then:** The documentation states:
- **Always** use specific version tags (`@v0.2.0`) in production
- Avoid `@main` or branch names in production
- Prevents unexpected breaking changes

#### Scenario: Finding available versions explained
**Given:** A user wants to know which version to use  
**When:** They read the version pinning section  
**Then:** The documentation explains:
- Check GitHub releases page for available versions
- Review CHANGELOG.md for version changes
- Link to releases: `https://github.com/SolomonHD/unifi-cloudflare-glue/releases`

#### Scenario: Version update strategy suggested
**Given:** A user's production uses a pinned version  
**When:** They want to upgrade  
**Then:** The documentation suggests:
- Test new version in non-production first
- Review changelog for breaking changes
- Update version pin only after validation

### Requirement: CI/CD Integration Example

The documentation MUST provide a realistic CI/CD workflow example showing remote module usage.

#### Scenario: GitHub Actions workflow provided
**Given:** A user wants to integrate with GitHub Actions  
**When:** They read the CI/CD section  
**Then:** They see a complete workflow file showing:
- Dagger installation step
- Direct remote module call with version pin
- Environment variable secrets usage
- State management for CI environment

#### Scenario: CI/CD pattern explained
**Given:** A user reviews the CI/CD example  
**When:** They understand the pattern  
**Then:** The documentation highlights:
- Direct remote pattern preferred for CI/CD (no install step)
- Version pinning critical for reproducibility
- Secret management via environment variables
- Ephemeral state or remote backend for state

#### Scenario: Adaptable to other CI systems
**Given:** A user uses GitLab CI or other CI systems  
**When:** They read the GitHub Actions example  
**Then:** The documentation notes:
- Pattern applies to any CI system
- Key elements: install Dagger, set environment variables, call module
- Link to Dagger CI documentation for other platforms

### Requirement: Documentation Consistency

The documentation MUST maintain consistency with existing README.md style, tone, and formatting.

#### Scenario: Markdown formatting matches existing
**Given:** A user reads the new section  
**When:** They compare with existing sections  
**Then:** The formatting matches:
- Code blocks use ```bash syntax highlighting
- Headers follow existing hierarchy (#, ##, ###)
- Lists use consistent bullet/numbering style
- Links use reference-style where appropriate

#### Scenario: Code examples follow conventions
**Given:** A developer reviews command examples  
**When:** They validate syntax  
**Then:** All examples:
- Use `\` for line continuation
- Quote environment variable patterns (`env:VAR_NAME`)
- Show realistic placeholder values
- Include helpful comments where needed

#### Scenario: Tone and voice consistency
**Given:** A user reads the entire README  
**When:** They transition between sections  
**Then:** The new section:
- Uses same instructional voice as existing content
- Maintains technical but approachable tone
- Avoids overly casual or overly formal language
- Matches existing section's detail level

### Requirement: Cross-Referencing

The documentation MUST link to related sections and external resources where appropriate.

#### Scenario: Links to function documentation
**Given:** A user wants detailed parameter information  
**When:** They read a function example  
**Then:** The documentation notes:
- Run `dagger functions` to see all available functions
- Use `dagger call <function> --help` for detailed parameter info
- Function docstrings provide comprehensive usage guidance

#### Scenario: Links to example configurations
**Given:** A user needs a complete KCL configuration example  
**When:** They read the remote module section  
**Then:** The documentation links to:
- `examples/homelab-media-stack/` directory
- KCL schema documentation
- External KCL language guide

#### Scenario: Links to related documentation
**Given:** A user wants to understand Terraform module usage  
**When:** They finish the Dagger module section  
**Then:** The documentation references:
- "Using as Terraform Modules" section for Terraform-only usage
- Relationship between Dagger functions and Terraform modules
- When to use Dagger vs direct Terraform

## Success Testing

### Manual Verification Checklist

After implementation, verify:

- [ ] Section exists after "Quickstart" and before "Modules" in README.md
- [ ] Installation command is syntactically correct
- [ ] All six function examples (deploy, deploy-unifi, deploy-cloudflare, destroy, plan, test-integration) are present
- [ ] Parameter distinction (`--source` vs `--kcl-source`) is clearly explained
- [ ] All three calling patterns (installed, direct remote, CI/CD) are documented
- [ ] Version pinning recommendation is stated
- [ ] CI/CD example (GitHub Actions) is complete and realistic
- [ ] Markdown formatting is consistent with existing sections
- [ ] All code blocks use appropriate syntax highlighting
- [ ] Links to related sections function correctly
- [ ] Warning/important callouts are used for critical information
- [ ] No spelling or grammatical errors

### Command Validation

Test that all documented commands are syntactically valid:

```bash
# Verify module name in dagger.json
cat dagger.json | grep '"name"'  # Should show "unifi-cloudflare-glue"

# Verify current version
cat VERSION  # Should match version in examples

# Test function listing (requires Dagger)
dagger functions  # Should list all documented functions
```
