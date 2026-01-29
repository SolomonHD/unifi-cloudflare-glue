# OpenSpec Change Prompt 02: Implement Real Cloudflare Resource Creation

## Context

Currently, Phase 2 of `test_integration` (lines 921-931) only prints simulated success messages without actually creating Cloudflare resources. The working `deploy_cloudflare()` function (lines 222-298) demonstrates the correct pattern for Terraform execution.

## Goal

Implement real Cloudflare tunnel and DNS record creation by executing Terraform in a container, similar to how `deploy_cloudflare()` works.

## Scope

**In scope:**
- Replace simulated Cloudflare creation with real Terraform execution
- Create a container with Terraform
- Mount the cloudflare-tunnel module
- Write the generated JSON config to the container
- Set required environment variables and secrets
- Run `terraform init` and `terraform apply -auto-approve`
- Capture and report actual Terraform output
- Handle errors properly

**Out of scope:**
- Modifying config generation (handled in Prompt 01)
- UniFi resource creation (handled in Prompt 03)
- Validation logic (handled in Prompt 04)
- Cleanup logic (handled in Prompt 05)

## Desired Behavior

### 1. Container Setup

```python
# Create Terraform container
ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

# Mount the Cloudflare Tunnel Terraform module
tf_module = dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")
ctr = ctr.with_directory("/module", tf_module)

# Write the cloudflare config JSON to a file in the container
ctr = ctr.with_new_file("/workspace/cloudflare.json", cloudflare_config_json)
```

### 2. Environment Variables

```python
# Set required variables
ctr = ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
ctr = ctr.with_env_variable("TF_VAR_zone_name", cloudflare_zone)
ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")

# Set Cloudflare token as secret (must be retrieved via await first)
cf_token_plain = await cloudflare_token.plaintext()
ctr = ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
```

### 3. Terraform Execution

```python
# Set working directory to the module
ctr = ctr.with_workdir("/module")

# Run terraform init
try:
    init_output = await ctr.with_exec(["terraform", "init"]).stdout()
    report_lines.append("  ✓ Terraform init completed")
except dagger.ExecError as e:
    report_lines.append(f"  ✗ Terraform init failed: {e.stderr}")
    raise  # Re-raise to trigger cleanup

# Run terraform apply
try:
    apply_output = await ctr.with_exec([
        "terraform", "apply", "-auto-approve"
    ]).stdout()
    report_lines.append(f"  ✓ Created tunnel: {tunnel_name}")
    report_lines.append(f"  ✓ Created DNS record: {test_hostname}")
    validation_results["cloudflare_tunnel"] = "created"
    validation_results["cloudflare_dns"] = "created"
except dagger.ExecError as e:
    report_lines.append(f"  ✗ Terraform apply failed: {e.stderr}")
    validation_results["cloudflare_error"] = str(e)
    raise  # Re-raise to trigger cleanup
```

### 4. Error Handling

- If `terraform init` fails, raise an exception to trigger cleanup phase
- If `terraform apply` fails, raise an exception to trigger cleanup phase
- Store error details in `validation_results` for the report

## Constraints & Assumptions

- The cloudflare config JSON is already generated (from Prompt 01)
- The `terraform/modules/cloudflare-tunnel/` directory exists
- Cloudflare credentials are valid
- The `cloudflare_token` Secret must be converted to plaintext before use in container setup
- Use the existing `terraform_version` parameter from function signature
- Follow the same pattern as the working `deploy_cloudflare()` function

## Dependencies

- Prompt 01: Fix Test Config Generation (must provide proper JSON)

## Acceptance Criteria

- [ ] Phase 2 creates a Terraform container with the correct image
- [ ] Cloudflare tunnel module is mounted at `/module`
- [ ] Cloudflare config JSON is written to `/workspace/cloudflare.json`
- [ ] All required environment variables are set
- [ ] Cloudflare token is passed as a secret
- [ ] `terraform init` is executed and output captured
- [ ] `terraform apply -auto-approve` is executed
- [ ] Success messages include actual Terraform output summary
- [ ] Errors are caught and reported, triggering cleanup
- [ ] State tracking variables (`validation_results`) are updated correctly

## Reference

- Target: Phase 2 in `test_integration` function (lines 921-931) in `src/main/main.py`
- Reference implementation: `deploy_cloudflare()` function (lines 222-298)
- Module path: `terraform/modules/cloudflare-tunnel/`
