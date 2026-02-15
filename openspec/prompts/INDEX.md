# OpenSpec Prompts Index: Documentation Revamp

This directory contains a series of prompts for revamping the project documentation to be more modular, maintainable, and comprehensive.

## Prompt Sequence

The following prompts should be executed in order:

1. **[01-create-docs-structure.md](01-create-docs-structure.md)** - Create modular docs directory structure and split README
2. **[02-vals-integration-guide.md](02-vals-integration-guide.md)** - Write comprehensive vals + 1Password integration documentation
3. **[03-backend-configuration-guide.md](03-backend-configuration-guide.md)** - Document S3 lockfile vs DynamoDB locking options
4. **[04-kcl-configuration-guide.md](04-kcl-configuration-guide.md)** - Expand KCL schema documentation with examples
5. **[05-environment-examples.md](05-environment-examples.md)** - Add environment-specific deployment examples
6. **[06-architecture-diagrams.md](06-architecture-diagrams.md)** - Create Mermaid architecture diagrams
7. **[07-troubleshooting-guide.md](07-troubleshooting-guide.md)** - Write systematic troubleshooting documentation
8. **[08-add-version-update-checklist.md](08-add-version-update-checklist.md)** - Add unified version update checklist
8. **[08-add-version-update-checklist.md](08-add-version-update-checklist.md)** - Add unified version update checklist to CONTRIBUTING.md
9. **[09-improve-kcl-error-handling.md](09-improve-kcl-error-handling.md)** - Improve KCL error messages in Dagger module

## Overview

### Goal

Transform the monolithic 1355-line README into a modular documentation system that:
- Makes information easier to find and maintain
- Provides progressive disclosure of complexity
- Adds missing critical documentation (vals integration, S3 lockfile options)
- Improves user onboarding and debugging experience

### Key Changes

1. **Modular Structure**: Split README into focused documentation files
2. **vals Integration**: Complete workflow guide for 1Password and other secret backends
3. **Backend Clarification**: Document both S3 lockfile and DynamoDB locking options
4. **KCL Documentation**: Expand schema reference and validation guide
5. **Visual Documentation**: Add architecture diagrams using Mermaid
6. **Environment Examples**: Provide dev/staging/prod deployment patterns
7. **Troubleshooting**: Systematic problem-solving guide
8. **KCL Error Handling**: Improved error messages for KCL generator failures

### Dependencies

- **Prompt 01** must complete before others (creates structure)
- **Prompts 02-04** are independent and can run in parallel after 01
- **Prompts 05-07** can run after their respective dependencies

### Handoff Process

Each prompt follows the standard OpenSpec workflow:

1. Run proposal generation: `./openspec-proposal.md` workflow
2. Review proposal and approve
3. Implement changes
4. Move to next prompt in sequence

### Success Criteria

- [ ] README.md reduced to ~300 lines with clear links to docs
- [ ] Complete docs/ directory with 7+ specialized files
- [ ] vals + 1Password workflow fully documented with examples
- [ ] S3 lockfile and DynamoDB options clearly explained
- [ ] KCL schemas comprehensively documented
- [ ] Architecture diagrams created using Mermaid
- [ ] Environment-specific examples in examples/ directory
- [ ] Troubleshooting guide with decision trees
- [ ] Version update checklist for all components
- [ ] KCL error messages show actual output when yq conversion fails
- [ ] KCL execution errors include stdout/stderr details
- [ ] Empty KCL output produces helpful error message with possible causes

## Status

- **Status**: In Progress
- **Created**: 2026-02-05
- **Last Updated**: 2026-02-15
- **Priority**: High
- **Estimated Completion**: 2-3 weeks (9 prompts)
