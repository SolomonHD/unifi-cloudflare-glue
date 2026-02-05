## Why

The current README.md is 1355 lines and monolithic, making it difficult to navigate and maintain. Information is repeated across sections, and there's no clear separation between getting started, API reference, security, and troubleshooting content. Users struggle to find specific information, and contributors face challenges keeping documentation synchronized.

## What Changes

- Create a `docs/` directory with specialized documentation files organized by topic
- Split README.md content into focused documents: getting-started, dagger-reference, terraform-modules, state-management, and security
- Rewrite README.md to ~300 lines with clear navigation links to detailed docs
- Preserve all existing content (migrate, don't delete) with proper cross-linking
- Create placeholder files for backend-configuration and troubleshooting (to be populated by subsequent prompts)
- Back up original README.md as README.old.md before transformation

## Capabilities

### New Capabilities
- `modular-documentation-structure`: Organized docs/ directory with topic-based files replacing monolithic README
- `condensed-readme`: Streamlined README.md entry point (~300 lines) with navigation to specialized docs
- `documentation-link-integrity`: All internal links work correctly across restructured documentation

### Modified Capabilities
- `documentation`: Update existing documentation capability requirements to support modular structure with cross-references

## Impact

**Files Created:**
- `docs/getting-started.md` - Installation and first deployment
- `docs/dagger-reference.md` - Complete Dagger function reference with examples
- `docs/terraform-modules.md` - Standalone Terraform module usage
- `docs/state-management.md` - State options: ephemeral, local, and remote backends
- `docs/security.md` - Security best practices and credential handling
- `docs/backend-configuration.md` - Placeholder for backend config guide (prompt 03)
- `docs/troubleshooting.md` - Placeholder for troubleshooting guide (prompt 07)
- `docs/README.md` - Documentation index

**Files Modified:**
- `README.md` - Condensed to ~300 lines with navigation structure
- `.gitignore` - Add any necessary entries for docs artifacts

**Files Backed Up:**
- `README.old.md` - Original README before transformation

**Users Affected:**
- Contributors: Need to update documentation in multiple files instead of one
- New Users: Improved onboarding with focused getting-started guide
- Advanced Users: Easier access to detailed references and troubleshooting
- CI/CD Integrators: Quick reference to remote usage patterns
