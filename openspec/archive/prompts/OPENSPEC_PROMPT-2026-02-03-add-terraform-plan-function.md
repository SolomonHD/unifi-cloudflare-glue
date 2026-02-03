# OpenSpec Change Prompt

## Context

The `unifi-cloudflare-glue` Dagger module provides containerized Terraform deployment functions (`deploy`, `deploy-unifi`, `deploy-cloudflare`) and destruction (`destroy`) with support for persistent state management and remote backends. However, it lacks a standalone `terraform plan` function for reviewing infrastructure changes before applying them.

In production workflows, teams typically follow a plan → review → apply cycle rather than applying changes directly. Without a `plan` function, users cannot:
- Preview changes before deployment
- Save plan artifacts for approval workflows
- Integrate with policy-as-code tools (OPA, Sentinel)
- Automate cost estimation (Infracost)
- Generate structured JSON output for CI/CD pipelines

## Goal

Add a `plan` Dagger function that generates Terraform plans for both UniFi DNS and Cloudflare Tunnel configurations without applying changes, exporting plans in multiple formats (binary, JSON, and human-readable text) for review and automation.

## Scope

**In scope:**
- Add new `plan()` Dagger function to `src/main/main.py`
- Generate plans for both UniFi and Cloudflare modules
- Export three plan formats:
  - Binary plan file (`*.tfplan`) - for subsequent `terraform apply -input=false plan.tfplan`
  - JSON format (`*.json`) - for tooling/automation via `terraform show -json`
  - Human-readable text (`*.txt`) - for manual review via `terraform show`
- Support same state management options as `deploy` and `destroy`:
  - `--state-dir` for persistent local state
  - `--backend-type` and `--backend-config-file` for remote backends
- Support same authentication parameters (UniFi, Cloudflare)
- Support same version pinning (`--terraform-version`, `--kcl-version`)
- Return plans as a `dagger.Directory` for export
- Support cache control (`--no-cache`, `--cache-buster`)
- Create plan summary file aggregating both module plans

**Out of scope:**
- Applying plans (existing `deploy` functions handle this)
- Plan approval workflows (external tooling concern)
- Automated plan parsing/analysis (users can use JSON output)
- Plan file signing/verification
- Incremental planning (plan both modules every time)

## Desired Behavior

### Function Signature

```python
@function
async def plan(
    self,
    kcl_source: Annotated[dagger.Directory, Doc("KCL source directory containing configuration schemas")],
    unifi_url: Annotated[str, Doc("UniFi controller URL (e.g., https://unifi.local:8443)")],
    cloudflare_token: Annotated[dagger.Secret, Doc("Cloudflare API token")],
    cloudflare_account_id: Annotated[str, Doc("Cloudflare account ID")],
    zone_name: Annotated[str, Doc("Cloudflare zone name (e.g., example.com)")],
    
    # UniFi authentication (same as deploy)
    unifi_api_key: Annotated[Optional[dagger.Secret], Doc("UniFi API key (recommended)")] = None,
    unifi_username: Annotated[Optional[dagger.Secret], Doc("UniFi username (alternative)")] = None,
    unifi_password: Annotated[Optional[dagger.Secret], Doc("UniFi password (alternative)")] = None,
    unifi_insecure: Annotated[bool, Doc("Skip TLS certificate verification")] = False,
    
    # State management (same as deploy/destroy)
    state_dir: Annotated[Optional[dagger.Directory], Doc("Persistent local state directory")] = None,
    backend_type: Annotated[str, Doc("Remote backend type (s3, azurerm, gcs, remote)")] = "local",
    backend_config_file: Annotated[Optional[dagger.File], Doc("Backend configuration file (.hcl)")] = None,
    
    # Version control (same as deploy)
    terraform_version: Annotated[str, Doc("Terraform version to use")] = "latest",
    kcl_version: Annotated[str, Doc("KCL version to use")] = "latest",
    
    # Cache control (same as test_integration)
    no_cache: Annotated[bool, Doc("Bypass Dagger cache, force fresh execution")] = False,
    cache_buster: Annotated[str, Doc("Custom cache key (advanced use)")] = "",
) -> dagger.Directory:
    """
    Generate Terraform plans for UniFi DNS and Cloudflare Tunnel without applying changes.
    
    Returns a directory containing:
    - unifi-plan.tfplan (binary plan file)
    - unifi-plan.json (structured JSON output)
    - unifi-plan.txt (human-readable plan)
    - cloudflare-plan.tfplan (binary plan file)
    - cloudflare-plan.json (structured JSON output)
    - cloudflare-plan.txt (human-readable plan)
    - plan-summary.txt (aggregated summary of both plans)
    
    Example usage:
        dagger call plan \\
            --kcl-source=./kcl \\
            --state-dir=./terraform-state \\
            --unifi-url=https://unifi.local:8443 \\
            --unifi-api-key=env:UNIFI_API_KEY \\
            --cloudflare-token=env:CF_TOKEN \\
            --cloudflare-account-id=xxx \\
            --zone-name=example.com \\
            export --path=./plans
    """
```

### Plan Generation Process

For each module (UniFi DNS, Cloudflare Tunnel):
1. Generate KCL configuration using existing `_generate_*_config()` methods
2. Prepare Terraform container with module files
3. Apply state management configuration (backend or state mount)
4. Run `terraform init`
5. Run `terraform plan -out=MODULE-plan.tfplan`
6. Generate JSON: `terraform show -json MODULE-plan.tfplan > MODULE-plan.json`
7. Generate text: `terraform show MODULE-plan.tfplan > MODULE-plan.txt`

### Plan Summary File

Create `plan-summary.txt` with:
```
Terraform Plan Summary
======================

UniFi DNS Module:
- Resources to add: X
- Resources to change: Y
- Resources to destroy: Z
- Total: X + Y + Z

Cloudflare Tunnel Module:
- Resources to add: X
- Resources to change: Y
- Resources to destroy: Z
- Total: X + Y + Z

Overall Changes:
- Total resources to add: X
- Total resources to change: Y
- Total resources to destroy: Z
- Grand total: X + Y + Z

Generated at: [ISO 8601 timestamp]
Terraform version: [version]
KCL version: [version]
Backend type: [backend_type]
```

### Output Directory Structure

```
plans/
├── unifi-plan.tfplan        # Binary plan (for terraform apply)
├── unifi-plan.json          # Structured JSON (for automation)
├── unifi-plan.txt           # Human-readable (for review)
├── cloudflare-plan.tfplan   # Binary plan
├── cloudflare-plan.json     # Structured JSON
├── cloudflare-plan.txt      # Human-readable
└── plan-summary.txt         # Aggregated summary
```

### Container Reference Management

**CRITICAL:** Preserve container references after plan execution to export artifacts:

```python
# ✅ CORRECT - Save container reference
container = container.with_exec(["terraform", "plan", "-out=plan.tfplan"])
plan_result = await container.stdout()

# Now export plan files from the executed container
plan_binary = container.file("/module/plan.tfplan")
```

## Constraints & Assumptions

- Plans are read-only operations - no infrastructure changes
- Both modules (UniFi and Cloudflare) are always planned together
- Plans must be executed in same order as `deploy`: UniFi first, then Cloudflare
- State consistency: plan must use same state backend as subsequent apply
- Plans should complete even if one module has no changes
- Same authentication validation as `deploy` (API key XOR username/password)
- Same state backend validation (mutual exclusion: `state_dir` XOR remote backend)
- Cache busting follows same pattern as `test_integration`

## Acceptance Criteria

- [ ] `plan()` function added to `src/main/main.py`
- [ ] Function signature matches desired behavior (all parameters)
- [ ] Generates plans for both UniFi DNS and Cloudflare Tunnel modules
- [ ] Exports three formats per module: `.tfplan`, `.json`, `.txt`
- [ ] Creates `plan-summary.txt` with aggregated resource counts
- [ ] Returns `dagger.Directory` containing all plan artifacts
- [ ] Supports persistent local state via `--state-dir`
- [ ] Supports remote backends via `--backend-type` and `--backend-config-file`
- [ ] Validates state management mutual exclusivity
- [ ] Validates UniFi authentication mutual exclusivity
- [ ] Supports version pinning (`--terraform-version`, `--kcl-version`)
- [ ] Supports cache control (`--no-cache`, `--cache-buster`)
- [ ] Preserves container references to export plan files correctly
- [ ] Updates `README.md` with `plan` function documentation
- [ ] Updates `CHANGELOG.md` with new feature entry
- [ ] Function includes comprehensive docstring with example usage
- [ ] Error handling returns clear messages on plan failures
