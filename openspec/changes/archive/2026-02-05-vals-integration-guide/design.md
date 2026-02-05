## Context

The project currently supports YAML backend configuration files that accept Terraform state settings, but these files must either contain plaintext secrets or reference environment variables. Users face a dilemma: commit credentials to version control (insecure) or manually manage environment variables (operationally complex). This is particularly challenging for multi-environment deployments where different environments use different secret backends (Dev in 1Password, Production in AWS Secrets Manager, etc.).

vals is an industry-standard tool for secret injection that supports multiple backends through a unified `ref+<backend>://` syntax. By documenting vals integration, we enable users to store secrets securely in their preferred secret management system while maintaining version-controlled template files that can be safely shared.

## Goals / Non-Goals

**Goals:**
- Provide comprehensive documentation for vals integration with all major secret backends
- Create working template examples that users can copy and customize
- Document complete workflows from secret storage to deployment
- Establish security best practices around rendered secret file handling
- Demonstrate automation patterns that guarantee secret cleanup

**Non-Goals:**
- Modifying Dagger module code (YAML parsing already works with vals-rendered output)
- Supporting secret backends beyond vals' native capabilities
- Creating custom vals plugins or backends
- CI/CD-specific integration (focus on local development workflows that translate to CI/CD)
- Implementing secret rotation automation (document best practices only)

## Decisions

### Decision: Document vals for secret injection

**Rationale:** vals is the most widely-adopted multi-backend secret injection tool in the infrastructure-as-code community. It supports 15+ backend providers through a unified interface, making it suitable for diverse environments. Alternative tools either lack multi-backend support (e.g., 1Password CLI alone) or require more complex setup (e.g., sealed-secrets for Kubernetes).

**Alternatives considered:**
- envsubst: Only supports environment variables, doesn't integrate with secret managers
- gomplate: More complex, requires learning template syntax
- Individual CLIs (op, aws secretsmanager, etc.): No unified interface across backends

### Decision: Focus on 1Password as primary example

**Rationale:** 1Password is commonly used for personal and small team infrastructure management, making it the most accessible entry point for documentation. Its CLI (`op`) works well with vals and provides good UX for local development.

**Secondary backends documented:** AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, HashiCorp Vault

### Decision: Provide Makefile automation examples

**Rationale:** Makefiles provide platform-independent automation that works in both local development and CI/CD environments. The make pattern allows error handling through target dependencies and `.PHONY` declarations, ensuring cleanup happens even on failures.

**Alternatives considered:**
- Shell scripts: Less familiar to some users, harder to express dependencies
- Task runners (just, mage): Additional tooling dependencies
- CI/CD specific (GitHub Actions, GitLab CI): Too narrow in scope

### Decision: Template files use `.yaml.tmpl` extension

**Rationale:** Clear distinction between template files (committed to version control) and rendered files (ephemeral secrets). The `.tmpl` suffix signals "process before use" and allows gitignore patterns like `*.yaml` (blocking rendered files) while permitting `*.yaml.tmpl` (allowing templates).

### Decision: Automatic cleanup as core pattern

**Rationale:** Rendered backend configuration files contain plaintext secrets that should not persist on disk. Making cleanup automatic (via Makefile dependencies or shell traps) reduces risk of credential exposure through orphaned files.

**Implementation:** Every deploy/destroy target automatically invokes cleanup as a dependency or via `trap` command, ensuring files are removed whether the operation succeeds or fails.

## Documentation Structure

### Main Guide: docs/vals-integration.md

**Sections:**
1. **Overview:** Brief explanation of vals and why it's valuable
2. **Prerequisites:** Installation steps for vals and backend CLIs
3. **1Password Integration:** Complete workflow (most detailed section as primary example)
   - Setup and authentication
   - Creating secret items
   - Template file structure
   - Rendering and deployment
   - Cleanup
4. **Other Backend Integrations:** Parallel structure for AWS, Azure, GCP, HashiCorp
5. **Security Best Practices:** Gitignore, rotation, cleanup, least privilege
6. **Troubleshooting:** Common errors and solutions

### Template Files: examples/backend-configs/

**File Naming Pattern:** `<backend-type>-<secret-source>.yaml.tmpl`

Examples:
- `s3-backend-1password.yaml.tmpl`
- `s3-backend-aws-secrets.yaml.tmpl`
- `azurerm-backend-1password.yaml.tmpl`
- `azurerm-backend-azure-kv.yaml.tmpl`
- `gcs-backend-gcp-secrets.yaml.tmpl`

Each template includes:
- Header comments with usage instructions
- Required secrets documentation
- vals ref syntax examples
- Optional credential fields (commented) for static credential scenarios

### Automation Example: examples/backend-configs/Makefile.example

**Targets:**
- `deploy`: Render secrets → Deploy infrastructure → Clean secrets
- `destroy`: Render secrets → Destroy infrastructure → Clean secrets
- `clean-secrets`: Remove rendered YAML files
- `help` (optional): Document available targets

**Key features:**
- Uses `@` prefix for sensitive commands (suppress echo of secrets)
- Demonstrates mixing file-based backend config with inline secrets (API keys via env vars)
- Shows 1Password CLI integration for inline account IDs
- Automatic cleanup via target dependencies

## Risks / Trade-offs

**[Risk]** Users might commit rendered secret files if they don't configure gitignore properly
→ **Mitigation:** Documentation prominently features gitignore setup. Template example includes `.gitignore` updates as an explicit step.

**[Risk]** vals has a learning curve for users unfamiliar with secret management tools
→ **Mitigation:** 1Password section provides step-by-step tutorial with screenshots/examples. Other backends provide parallel structure for pattern recognition.

**[Risk]** Different backends have different authentication mechanisms, documentation could become overwhelming
→ **Mitigation:** Use consistent structure across backends (Setup → Authentication → Usage). Focus on showing patterns rather than exhaustive configuration options.

**[Risk]** Makefile automation might not work on Windows without WSL/Git Bash
→ **Mitigation:** Document Makefile as one automation approach. Users can translate patterns to PowerShell or Task Scheduler equivalents.

**[Trade-off]** Documentation doesn't cover every vals backend
→ **Acceptance:** The five covered backends (1Password, AWS, Azure, GCP, Vault) represent 90%+ of infrastructure use cases. Documentation patterns enable users to adapt to other backends.

**[Trade-off]** vals rendering creates temporary plaintext files
→ **Acceptance:** This is inherent to vals' design. Mitigation through automatic cleanup and gitignore patterns. Alternative (passing secrets via env vars) is already documented elsewhere.

## Migration Plan

This is additive documentation—no migration required. Existing users can continue using environment variables or static YAML files.

**Rollout:**
1. Create documentation and templates
2. Update main README with link to vals guide
3. Announce in release notes as a new feature/workflow option
4. Optionally demonstrate in tutorial/blog post

**Compatibility:** No breaking changes. YAML backend configuration parsing remains unchanged.

## Open Questions

None—documentation-only change with well-established external tool (vals).
