# Tasks: Add Remote Dagger Module Documentation

## Implementation Tasks

### Phase 1: Documentation Structure

- [x] Identify insertion point in [`README.md`](../../README.md)
  - [x] Locate end of "Quickstart" section (approximately line 39)
  - [x] Locate start of "Modules" section (approximately line 95)
  - [x] Verify no content will be disrupted by insertion
- [x] Create new "Using as a Dagger Module" section heading
- [x] Add introductory paragraph explaining remote module consumption

### Phase 2: Installation Documentation

- [x] Write "Installation" subsection
  - [x] Document `dagger install` command with current version (v0.2.0)
  - [x] Explain what installation does (registers in dagger.json)
  - [x] Explain module persistence across sessions
  - [x] Note module becomes available with `-m unifi-cloudflare-glue` flag
- [x] Write "Version Selection" subsection
  - [x] Recommend `@vX.Y.Z` for production
  - [x] Warn against `@main` in production
  - [x] Link to GitHub releases page
  - [x] Show how to check available versions

### Phase 3: Parameter Distinction Documentation

- [x] Write "Critical: Parameter Differences" subsection
  - [x] Use WARNING or IMPORTANT callout box
  - [x] Explain `--source=.` behavior (reads module's files)
  - [x] Explain `--kcl-source=./path` behavior (reads user's files)
  - [x] Provide side-by-side comparison table
  - [x] Show example of each pattern
- [x] Add emphasis that remote users MUST use `--kcl-source`

### Phase 4: Function Examples Documentation

- [x] Write "Function Usage Examples" subsection
- [x] Document `deploy` function:
  - [x] Complete command with all authentication parameters
  - [x] Use `--kcl-source=./kcl`
  - [x] Show UniFi authentication (API key recommended)
  - [x] Show Cloudflare authentication
  - [x] Include state management option example
- [x] Document `deploy-unifi` function:
  - [x] Command for UniFi-only deployment
  - [x] UniFi authentication parameters
  - [x] State management options
- [x] Document `deploy-cloudflare` function:
  - [x] Command for Cloudflare-only deployment
  - [x] Cloudflare authentication parameters
  - [x] State management options
- [x] Document `destroy` function:
  - [x] Command for infrastructure teardown
  - [x] Same authentication as deploy
  - [x] Add warning about destructive operation
- [x] Document `plan` function:
  - [x] Command for plan generation
  - [x] Show export pattern: `export --path=./plans`
  - [x] Explain output directory structure
- [x] Document `test-integration` function:
  - [x] Command for integration testing
  - [x] Show `--no-cache` flag usage
  - [x] Explain when to use (CI/CD, development)

### Phase 5: Calling Patterns Documentation

- [x] Write "Module Calling Patterns" subsection
- [x] Document installed module pattern:
  - [x] Show syntax: `dagger call -m unifi-cloudflare-glue function-name`
  - [x] Explain prerequisites (must run `dagger install` first)
  - [x] Note this is most common for local development
- [x] Document direct remote pattern:
  - [x] Show syntax: `dagger call -m github.com/OWNER/REPO@VERSION MODULE-NAME function-name`
  - [x] Explain no installation required
  - [x] Note longer command but explicit versioning
  - [x] Recommend for CI/CD pipelines
- [x] Create comparison table/list:
  - [x] **Installed**: Pros (shorter commands, persistent), Cons (requires setup)
  - [x] **Direct Remote**: Pros (no install, explicit version), Cons (longer commands)
  - [x] **When to use**: Local dev vs CI/CD vs one-off

### Phase 6: Version Pinning Best Practices

- [x] Write "Version Pinning Best Practices" subsection
  - [x] State recommendation: **ALWAYS** use `@vX.Y.Z` in production
  - [x] Explain benefits: reproducibility, predictability, safety
  - [x] Warn against unpinned versions or branch names
  - [x] Link to releases page for version discovery
  - [x] Suggest version update strategy (test in non-prod first)

### Phase 7: CI/CD Integration Example

- [x] Write "CI/CD Integration" subsection
  - [x] Provide introduction to CI/CD usage patterns
  - [x] Show complete GitHub Actions workflow example:
    - [x] Dagger installation step
    - [x] Direct remote module call with version pin
    - [x] Environment variable secrets usage
    - [x] Appropriate state management (ephemeral or remote)
    - [x] Example deploy or plan operation
  - [x] Explain pattern applicability to other CI systems
  - [x] Note key elements: install Dagger, set secrets, call module
  - [x] Link to Dagger CI documentation for other platforms

### Phase 8: Cross-References and Links

- [x] Add link to `examples/homelab-media-stack/` for KCL config examples
- [x] Add link to "Using as Terraform Modules" section
- [x] Add link to GitHub releases page
- [x] Add reference to `dagger functions` command
- [x] Add reference to `dagger call <function> --help` pattern
- [x] Add link to KCL documentation (if external)

### Phase 9: Formatting and Consistency

- [x] Verify all code blocks use ```bash syntax
- [x] Ensure consistent header hierarchy (##, ###)
- [x] Check list formatting (bullets vs numbers)
- [x] Verify line continuations use `\`
- [x] Check environment variable format (`env:VAR_NAME`)
- [x] Ensure placeholders are realistic
- [x] Add comments to code blocks where helpful

### Phase 10: Review and Validation

- [x] Proofread entire section for typos and grammar
- [x] Verify all commands are syntactically correct
- [x] Check version numbers match VERSION file (0.2.0)
- [x] Verify module name matches dagger.json (unifi-cloudflare-glue)
- [x] Confirm all six functions documented
- [x] Verify section placement in README.md
- [x] Check section length is proportionate to related sections
- [x] Ensure tone matches existing documentation

## Documentation Validation Tasks

- [x] Test installation command (if possible):
  ```bash
  dagger install github.com/SolomonHD/unifi-cloudflare-glue@v0.2.0
  ```
- [x] Verify function list:
  ```bash
  dagger functions
  ```
- [x] Validate module name:
  ```bash
  cat dagger.json | grep name
  ```
- [x] Check current version:
  ```bash
  cat VERSION
  ```
- [x] Test function help (example):
  ```bash
  dagger call deploy --help
  ```

## Dependencies

This change depends on:
- [x] Current VERSION file content (v0.2.0)
- [x] Module name in dagger.json (unifi-cloudflare-glue)
- [x] Existing README.md sections for style/tone reference
- [x] GitHub repository URL (github.com/SolomonHD/unifi-cloudflare-glue)
- [x] Existing function implementations (deploy, deploy-unifi, deploy-cloudflare, destroy, plan, test-integration)

## Notes

- **Section Placement**: Critical to insert between "Quickstart" and "Modules" for logical flow
- **Parameter Distinction**: This is the most important concept to convey clearly - use visual aids (tables, callouts)
- **Version Accuracy**: All version references must match current VERSION file
- **Command Testing**: While not required for proposal, testing commands after implementation prevents documentation bugs
- **CI/CD Pattern**: Direct remote pattern preferred for CI/CD due to explicit versioning and no install step
- **Style Consistency**: Mirror the structure and detail level of "Using as Terraform Modules" section for consistency
- **Future-Proofing**: Consider adding a note about checking latest version since 0.2.0 will become outdated
