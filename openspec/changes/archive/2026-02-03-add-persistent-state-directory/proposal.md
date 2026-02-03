# Proposal: Add Persistent Local State Directory Support

## Change ID
`add-persistent-state-directory`

## Overview

This proposal adds optional persistent local state directory support to deployment functions, providing a middle-ground option between ephemeral container state (default) and remote backends (production). This enables developers to maintain Terraform state across deployments during solo development without setting up remote backend infrastructure.

## Background

Currently, the Dagger module supports two state management modes:
1. **Ephemeral state** (default): State stored in container at `/module/terraform.tfstate`, lost when container exits
2. **Remote backend** (from prompts/01): State stored in remote backends (S3, Azure, GCS, Terraform Cloud) with proper credentials

However, there's a gap for solo developers who want:
- State persistence between runs (unlike ephemeral)
- Simple local development workflow (unlike remote backend)
- No cloud credentials or backend setup required

## Problem Statement

Solo developers must choose between:
- **Ephemeral state**: Fast and simple but requires redeployment from scratch each run, losing track of existing infrastructure
- **Remote backend**: Persistent and team-friendly but requires backend setup, cloud access, credentials management, and additional complexity

**Missing**: A simple persistent local state option for solo development workflows.

## Proposed Solution

Add a `state_dir` parameter (Optional[Directory]) to deployment functions that:
1. Mounts a user-provided directory for state storage
2. Copies Terraform module files to the state directory (co-location with state)
3. Sets working directory to state directory during terraform operations
4. Ensures mutual exclusion with remote backend configuration

### Three State Management Modes

| Mode | Configuration | State Location | Best For |
|------|--------------|----------------|----------|
| **Ephemeral** | (default, no flags) | Container `/module/terraform.tfstate` | Testing, CI/CD, one-off operations |
| **Remote Backend** | `--backend-type=s3 --backend-config-file=...` | S3/Azure/GCS/TFC | Production, teams, compliance |
| **Persistent Local** | `--state-dir=./terraform-state` | Host `./terraform-state/terraform.tfstate` | Solo development, iteration |

## Affected Components

### Dagger Module Functions
- `deploy_unifi()` - Add `state_dir` parameter and handling
- `deploy_cloudflare()` - Add `state_dir` parameter and handling  
- `deploy()` - Add `state_dir` parameter, pass through to both phases
- `destroy()` - Add `state_dir` parameter, pass through to both cleanup phases

### Documentation
- `README.md` - Add "State Management in Dagger Functions" section with comparison matrix
- `CHANGELOG.md` - Document new feature

## Design Decisions

### Mutual Exclusion with Remote Backend
**Decision**: `state_dir` and `backend_type != "local"` are mutually exclusive.

**Rationale**: 
- Mixing local and remote state is confusing and error-prone
- Users should explicitly choose one state strategy
- Clear error messages guide users to correct usage

### Module File Co-location
**Decision**: Copy module files to state directory before terraform operations.

**Rationale**:
- Keeps `.tf` files and `.tfstate` file together
- Matches typical Terraform project structure
- Allows users to inspect both code and state in one location

### Working Directory Change
**Decision**: When using `state_dir`, change working directory from `/module` to `/state`.

**Rationale**:
- Terraform expects to run where state file lives
- Allows `.terraform/` cache to persist alongside state
- Simplifies terraform commands (no `-chdir` needed)

### Default Behavior Unchanged
**Decision**: Ephemeral state remains the default (backwards compatible).

**Rationale**:
- Existing users experience no breaking changes
- Opt-in feature for those who need it
- Testing/CI workflows continue to work unchanged

## Dependencies

- **Prerequisite**: Prompt 01 (remote backend support) must be implemented
- **Reason**: Validation logic checks for conflicts with `backend_type` parameter

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Users forget to backup state directory | Document backup responsibility, suggest version control (with caution), or remote backend for critical infra |
| State directory not created | Provide clear error message, document `mkdir` requirement in examples |
| State corruption from concurrent access | Document that local backend has no locking, recommend remote backend for teams |
| Confusion between three modes | Provide comparison matrix, clear examples, validation with helpful error messages |

## Success Criteria

1. Users can persist Terraform state locally without remote backend setup
2. Clear validation prevents conflicting state storage options
3. Error messages guide users to correct configuration
4. Documentation clearly explains all three modes and when to use each
5. Backwards compatibility maintained (default behavior unchanged)

## Open Questions

None - requirements are well-defined in the prompt.

## References

- Source: `openspec/prompts/02-add-persistent-state-directory.md`
- Related: `openspec/prompts/01-add-backend-config-support.md` (remote backend implementation)
