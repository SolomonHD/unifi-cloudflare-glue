# OpenSpec Prompt: Create Modular Documentation Structure

## Context

The current [`README.md`](../../README.md) is monolithic at 1355 lines, making it difficult to navigate and maintain. Information is repeated multiple times, and there's no clear separation of concerns between getting started, API reference, security, and troubleshooting content.

## Goal

Transform the documentation into a modular structure with a condensed main README that links to specialized documentation files, improving discoverability and maintainability.

##Scope

### In Scope

1. Create `docs/` directory structure
2. Split README.md into focused documentation files:
   - `docs/getting-started.md` - Installation and first deployment
   - `docs/dagger-reference.md` - Complete Dagger function reference
   - `docs/terraform-modules.md` - Using as standalone Terraform modules
   - `docs/state-management.md` - State management deep dive
   - `docs/security.md` - Security best practices
3. Rewrite README.md to ~300 lines with clear navigation
4. Ensure all links work correctly
5. Preserve all existing content (migrate, don't delete)

### Out of Scope

- New content creation (covered in subsequent prompts)
- KCL documentation expansion (separate prompt)
- vals integration guide (separate prompt)
- Backend configuration updates (separate prompt)
- Architecture diagrams (separate prompt)

## Desired Behavior

### New README.md Structure (~300 lines)

```markdown
# unifi-cloudflare-glue

Brief project overview (2-3 paragraphs)

## Quick Start

Three-command getting started (minimal)

## Documentation

- [Getting Started Guide](docs/getting-started.md) - Installation and first deployment
- [Dagger Function Reference](docs/dagger-reference.md) - Complete API reference
- [Terraform Modules](docs/terraform-modules.md) - Using as standalone modules
- [State Management](docs/state-management.md) - Ephemeral, local, and remote backends
- [Security Best Practices](docs/security.md) - Credential handling and state security
- [Backend Configuration](docs/backend-configuration.md) - S3, Azure, GCS backends
- [Troubleshooting](docs/troubleshooting.md) - Common issues and solutions

## Architecture

High-level architecture description with link to detailed docs

## Key Features

- Unified Configuration
- DNS Loop Prevention  
- MAC Address Management
- One Tunnel Per Device

## Project Structure

```
unifi-cloudflare-glue/
├── terraform/modules/ - Terraform modules
├── kcl/               - KCL schemas and generators
├── src/               - Dagger module source
├── examples/          - Example configurations
└── docs/              - Documentation
```

## Contributing

Link to CONTRIBUTING.md

## License

MIT
```

### docs/ Directory Structure

```
docs/
├── getting-started.md        # Quickstart to first deployment
├── dagger-reference.md       # All Dagger functions with examples
├── terraform-modules.md      # Terraform module usage
├── state-management.md       # State options: ephemeral, local, remote
├── security.md              # Security best practices
├── backend-configuration.md  # Backend config files (placeholder for prompt 03)
├── troubleshooting.md       # Common issues (placeholder for prompt 07)
└── README.md                # docs/ index
```

## Constraints & Assumptions

### Constraints

- Preserve ALL existing content (migrate, don't delete)
- Maintain all existing links and examples
- Keep code examples tested and accurate
- Follow Markdown best practices
- Use relative paths for internal links

### Assumptions

- Users may bookmark specific sections, so provide redirects/anchors
- Some users will read linearly (getting started → reference)
- Other users will jump directly to specific topics (security, troubleshooting)
- CI/CD users need quick reference to remote usage patterns

## Acceptance Criteria

- [ ] `docs/` directory created with structure
- [ ] README.md reduced to ~300 lines with navigation links
- [ ] [`docs/getting-started.md`](../../docs/getting-started.md) created with installation and quickstart
- [ ] [`docs/dagger-reference.md`](../../docs/dagger-reference.md) created with all function examples
- [ ] [`docs/terraform-modules.md`](../../docs/terraform-modules.md) created with module usage
- [ ] [`docs/state-management.md`](../../docs/state-management.md) created with state options
- [ ] [`docs/security.md`](../../docs/security.md) created with security practices
- [ ] All internal links work correctly
- [ ] All code examples preserved and accurate
- [ ] Original README.md backed up as [`README.old.md`](../../README.old.md)

## Expected Files/Areas Touched

- `README.md` - Rewrite to condensed version
- `docs/` (new directory)
  - `getting-started.md` (new)
  - `dagger-reference.md` (new)
  - `terraform-modules.md` (new)
  - `state-management.md` (new)
  - `security.md` (new)
  - `backend-configuration.md` (placeholder, new)
  - `troubleshooting.md` (placeholder, new)
  - `README.md` (docs index, new)
- `.gitignore` - Add any necessary entries

## Dependencies

None (first prompt in sequence)

## Notes

- This lays the foundation for subsequent documentation improvements
- Focus on structure and organization, not new content
- Ensure the transition is smooth for existing users
- Placeholder files for backend-configuration and troubleshooting will be populated by later prompts
