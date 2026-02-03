# OpenSpec Prompt: Add Persistent Local State Directory Support

## Context

Following the addition of remote backend support (prompt 01), this prompt adds support for persistent local state directories. This provides a middle-ground option between:
- **Ephemeral state** (current default): Lost when container exits, good for testing/CI
- **Remote backend** (prompt 01): Requires backend setup, credentials, good for production
- **Persistent local** (this prompt): Simple local persistence, good for solo development

Persistent local state allows developers to maintain Terraform state across deployments without setting up remote backends, making it easier to iterate on configurations during development.

**Critical constraint:** Persistent local state and remote backends are mutually exclusive - users must choose one approach.

## Goal

Add optional persistent local state directory support to deployment functions with validation to ensure mutual exclusion with remote backend configuration.

## Scope

### In Scope

- Add `state_dir` parameter to deployment functions (Optional[Directory])
- Add validation to ensure `state_dir` and `backend_type != "local"` are mutually exclusive
- Mount user-provided directory for persistent state storage
- Copy Terraform module files into state directory for co-location
- Update these functions:
  - `deploy_unifi` in src/main/main.py
  - `deploy_cloudflare` in src/main/main.py
  - `deploy` in src/main/main.py (orchestration function)
  - `destroy` in src/main/main.py (cleanup function)
- Add documentation in README.md explaining three state modes
- Add comparison matrix showing when to use each mode

### Out of Scope

- State locking for local directories (not a Terraform feature for local backend)
- Automatic state directory creation (user must provide existing directory)
- State migration tooling between modes
- Changes to test_integration function (uses ephemeral state by design)
- Team collaboration features (use remote backend instead)

## Desired Behavior

### Function Signature Addition

Add one new parameter to deployment functions (in addition to backend_type/backend_config_file from prompt 01):

```python
@function
async def deploy_cloudflare(
    self,
    source: Annotated[Directory, Doc("Source directory containing cloudflare.json")],
    cloudflare_token: Annotated[Secret, Doc("Cloudflare API Token")],
    cloudflare_account_id: Annotated[str, Doc("Cloudflare Account ID")],
    zone_name: Annotated[str, Doc("DNS zone name")],
    terraform_version: Annotated[str, Doc("Terraform version")] = "latest",
    
    # From prompt 01: Remote backend support
    backend_type: Annotated[str, Doc("Backend type")] = "local",
    backend_config_file: Annotated[Optional[File], Doc("Backend config file")] = None,
    
    # NEW: Persistent local state directory
    state_dir: Annotated[Optional[Directory], Doc(
        "Directory for persistent local Terraform state storage. "
        "State will be written to <state_dir>/terraform.tfstate and persist between runs. "
        "Useful for solo development without remote backend setup. "
        "Cannot be used with remote backend (backend_type != 'local'). "
        "Default: None (ephemeral container-local state)"
    )] = None,
) -> str:
```

### Validation Logic

Add validation BEFORE backend configuration logic:

```python
# Validate mutually exclusive state storage options
if backend_type != "local" and state_dir is not None:
    return (
        "✗ Failed: Cannot use both remote backend and local state directory.\n\n"
        "You specified:\n"
        f"  • Remote backend: --backend-type={backend_type}\n"
        "  • Local state dir: --state-dir\n\n"
        "These options are mutually exclusive. Choose ONE approach:\n\n"
        "Option 1 - Remote Backend (for production):\n"
        "  dagger call deploy-cloudflare \\\n"
        "    --backend-type=s3 \\\n"
        "    --backend-config-file=./backend.hcl \\\n"
        "    ...\n\n"
        "Option 2 - Persistent Local (for solo development):\n"
        "  dagger call deploy-cloudflare \\\n"
        "    --state-dir=./terraform-state \\\n"
        "    ...\n\n"
        "Option 3 - Ephemeral (for testing/CI):\n"
        "  dagger call deploy-cloudflare \\\n"
        "    ... (no state options)\n"
    )
```

### Implementation Pattern

Add state directory handling BEFORE terraform init:

```python
# After creating Terraform container and mounting module...

# Handle persistent local state directory
if state_dir is not None:
    # Mount state directory
    ctr = ctr.with_directory("/state", state_dir)
    
    # Copy module files to state directory (for co-location with state)
    ctr = ctr.with_exec([
        "sh", "-c",
        "cp -r /module/* /state/ && ls -la /state"
    ])
    
    # Set working directory to state directory
    ctr = ctr.with_workdir("/state")
    report_lines.append("  ✓ Mounted persistent state directory")
else:
    # Default: work in module directory (ephemeral state)
    ctr = ctr.with_workdir("/module")

# Backend configuration logic continues here...
# (from prompt 01 - backend block generation, config file mounting)

# Then run terraform init...
```

### Three State Storage Modes

| Mode | Configuration | State Location | Best For |
|------|--------------|----------------|----------|
| **Ephemeral** | (default, no flags) | Container-local `/module/terraform.tfstate` (lost on exit) | Testing, CI/CD |
| **Remote Backend** | `--backend-type=s3 --backend-config-file=./backend.hcl` | S3/Azure/GCS/TFC | Production, teams |
| **Persistent Local** | `--state-dir=./tf-state` | `./tf-state/terraform.tfstate` (persists on host) | Solo development |

### Usage Examples

**Mode 1: Ephemeral State (default - no change from current behavior):**
```bash
dagger call deploy-cloudflare \
    --source=. \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com

# State: /module/terraform.tfstate (ephemeral, lost on container exit)
```

**Mode 2: Remote Backend (from prompt 01):**
```bash
# Create s3-backend.hcl with backend configuration
# Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY

dagger call deploy-cloudflare \
    --source=. \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com

# State: s3://my-bucket/cloudflare.tfstate (persistent, remote)
```

**Mode 3: Persistent Local Directory (NEW):**
```bash
# Create state directory (only needed once)
mkdir -p ./terraform-state

# Deploy with persistent state
dagger call deploy-cloudflare \
    --source=. \
    --state-dir=./terraform-state \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com

# State: ./terraform-state/terraform.tfstate (persistent, local)
```

### Destroy Function Behavior

The destroy function must use the SAME state configuration as deploy:

```bash
# Destroy must match deploy's state configuration

# Ephemeral state (no state params)
dagger call destroy --source=. ...

# Remote backend
dagger call destroy \
    --source=. \
    --backend-type=s3 \
    --backend-config-file=./s3-backend.hcl \
    ...

# Persistent local
dagger call destroy \
    --source=. \
    --state-dir=./terraform-state \
    ...
```

## Constraints & Assumptions

- Users must create the state directory before first use: `mkdir -p ./terraform-state`
- State directory is mounted read-write, allowing Terraform to write/update state
- Module files are copied to state directory to co-locate code and state
- Local backend does NOT provide state locking - suitable for solo development only
- Users are responsible for backing up their state directory
- State directory must be excluded from version control (.gitignore)
- For team collaboration or state locking, users should use remote backend instead
- The three modes (ephemeral, remote, persistent local) are mutually exclusive
- Default behavior (ephemeral) remains unchanged for backwards compatibility

## Acceptance Criteria

- [ ] `state_dir` parameter added to `deploy_unifi`, `deploy_cloudflare`, `deploy`, `destroy`
- [ ] Validation ensures `state_dir` and `backend_type != "local"` are mutually exclusive
- [ ] Clear error message explains mutual exclusion and shows all three options
- [ ] State directory mounted at `/state` when provided
- [ ] Module files copied to `/state` directory for co-location
- [ ] Working directory set to `/state` when using persistent local state
- [ ] Working directory remains `/module` for ephemeral and remote backend modes
- [ ] README.md updated with:
  - "State Management in Dagger Functions" section
  - Comparison matrix showing three modes
  - Usage examples for all three modes
  - Guidance on when to use each mode
  - Note about state locking and team collaboration
- [ ] CHANGELOG.md updated with new feature
- [ ] All four affected functions work consistently
- [ ] Backwards compatibility maintained (default behavior unchanged)
- [ ] Error message provides clear guidance when conflicting options used

## Expected Files Modified

- `src/main/main.py` - Add parameter and implementation to 4 functions
- `README.md` - Add comprehensive state management section
- `CHANGELOG.md` - Document new feature

## Dependencies

- This prompt depends on prompt 01 (backend config support) being implemented first
- The validation logic checks for conflicts with `backend_type` parameter from prompt 01
- Both features must work together with proper mutual exclusion

## Notes

- This is part 2 of 2 for state management improvements
- Implementation should be identical across all four deployment functions
- Consider adding helper function to reduce duplication: `_configure_state_storage(ctr, backend_type, backend_config_file, state_dir)`
- The trois state modes provide clear migration paths:
  - Start with ephemeral for testing
  - Upgrade to persistent local for development
  - Graduate to remote backend for production
- State directory should be added to .gitignore template in documentation
