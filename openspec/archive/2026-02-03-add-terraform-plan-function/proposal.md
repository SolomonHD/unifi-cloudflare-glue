# Proposal: Add Terraform Plan Function

## Summary

Add a `plan()` Dagger function that generates Terraform plans for both UniFi DNS and Cloudflare Tunnel configurations without applying changes, enabling plan → review → apply workflows.

## Problem Statement

The current deployment workflow applies infrastructure changes immediately via `deploy`, `deploy-unifi`, and `deploy-cloudflare` functions. This lacks the industry-standard "plan → review → apply" cycle where teams preview changes before deployment.

Without a dedicated `plan` function, users cannot:
- Preview infrastructure changes before applying them
- Save plan artifacts for approval workflows
- Integrate with policy-as-code tools (OPA, Sentinel)
- Automate cost estimation (Infracost)
- Generate structured JSON output for CI/CD pipelines
- Share plans with team members for review

## Proposed Solution

Add a `plan()` Dagger function to `src/main/main.py` that:

1. Generates KCL configuration using existing `_generate_*_config()` methods
2. Prepares Terraform containers for both modules (UniFi DNS, Cloudflare Tunnel)
3. Runs `terraform plan -out=MODULE-plan.tfplan` for each module
4. Exports three formats per module:
   - Binary plan file (`*.tfplan`) - for subsequent `terraform apply`
   - JSON format (`*.json`) - for tooling/automation
   - Human-readable text (`*.txt`) - for manual review
5. Creates `plan-summary.txt` aggregating resource counts from both modules
6. Returns a `dagger.Directory` containing all plan artifacts

### Key Design Decisions

**Same State Management as Deploy/Destroy**: 
- Supports `--state-dir` for persistent local state
- Supports `--backend-type` and `--backend-config-file` for remote backends
- Enforces mutual exclusivity between local and remote state

**Same Authentication as Deploy**:
- UniFi: API key (recommended) OR username/password
- Cloudflare: API token
- Same validation logic as existing functions

**Container Reference Preservation**:
- Critical pattern: Save container references after `terraform plan` execution
- Enables exporting plan files from executed containers
- Follows Dagger's immutable container model

**Plan Execution Order**:
- Plans both modules sequentially (UniFi first, then Cloudflare)
- Matches deployment order for consistency

## Scope

### In Scope
- New `plan()` function in `src/main/main.py`
- Generate plans for both UniFi DNS and Cloudflare Tunnel modules
- Export three formats per module (binary, JSON, text)
- Plan summary file with resource counts
- Support for persistent local state (`--state-dir`)
- Support for remote backends (`--backend-type`, `--backend-config-file`)
- Version pinning (`--terraform-version`, `--kcl-version`)
- Cache control (`--no-cache`, `--cache-buster`)
- Documentation in [`README.md`](../../README.md)
- Changelog entry in [`CHANGELOG.md`](../../CHANGELOG.md)

### Out of Scope
- Applying plans (existing `deploy` functions handle this)
- Plan approval workflows (external tooling concern)
- Automated plan parsing/analysis (users can use JSON output)
- Plan file signing/verification
- Incremental planning (always plan both modules)
- Modifying existing deployment functions

## Requirements

### Functional Requirements

1. **FR-1**: Function accepts same authentication parameters as `deploy` (UniFi, Cloudflare)
2. **FR-2**: Function accepts same state management parameters as `deploy` and `destroy`
3. **FR-3**: Function validates UniFi authentication mutual exclusivity (API key XOR username/password)
4. **FR-4**: Function validates state management mutual exclusivity (state_dir XOR remote backend)
5. **FR-5**: Function validates cache control mutual exclusivity (no_cache XOR cache_buster)
6. **FR-6**: Function generates KCL configuration for both modules
7. **FR-7**: Function runs `terraform plan -out=plan.tfplan` for each module
8. **FR-8**: Function exports binary plan file (`.tfplan`) per module
9. **FR-9**: Function exports JSON plan (`terraform show -json`) per module
10. **FR-10**: Function exports human-readable plan (`terraform show`) per module
11. **FR-11**: Function creates `plan-summary.txt` with aggregated resource counts
12. **FR-12**: Function returns `dagger.Directory` containing all artifacts
13. **FR-13**: Function preserves container references after plan execution for file export

### Non-Functional Requirements

1. **NFR-1**: Clear error messages for validation failures
2. **NFR-2**: Comprehensive docstring with example usage
3. **NFR-3**: Type annotations using `Annotated[..., Doc(...)]`
4. **NFR-4**: Async function signature following Dagger patterns
5. **NFR-5**: Documentation examples in README
6. **NFR-6**: Changelog entry documenting new capability

## Dependencies

- Existing `_generate_unifi_config()` method
- Existing `_generate_cloudflare_config()` method
- Existing `_prepare_terraform_container()` helper method
- Existing state management logic patterns
- Existing authentication validation patterns
- Terraform container image (pinnable via `--terraform-version`)
- KCL container image (pinnable via `--kcl-version`)

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Plan files may contain sensitive data | High | Document security best practices, recommend `.gitignore` entries |
| Large plan output directories | Medium | Document cleanup, provide example scripts |
| Container reference loss (can't export files) | High | Follow critical pattern: save container refs after execution |
| State mismatch between plan and apply | High | Document requirement to use same state backend for both |
| JSON parsing failures in summary | Low | Fallback to text-based resource count parsing |

## Success Criteria

- [ ] `plan()` function successfully generates plans for both modules
- [ ] All three output formats (binary, JSON, text) are exported correctly
- [ ] Plan summary accurately aggregates resource counts
- [ ] Function works with `--state-dir` (persistent local state)
- [ ] Function works with `--backend-type` and `--backend-config-file` (remote backends)
- [ ] Validation enforces mutual exclusivity constraints
- [ ] Documentation includes usage examples
- [ ] Changelog documents new feature
- [ ] Function follows existing Dagger module patterns

## Open Questions

None. Requirements are well-defined in the prompt file.
