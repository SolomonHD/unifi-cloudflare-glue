# OpenSpec Change Prompt 03: Implement Real UniFi Resource Creation

## Context

Currently, Phase 3 of `test_integration` (lines 933-940) only prints a simulated success message without actually creating UniFi DNS records. The working `deploy_unifi()` function (lines 113-220) demonstrates the correct pattern for Terraform execution with UniFi.

## Goal

Implement real UniFi DNS record creation by executing Terraform in a container, similar to how `deploy_unifi()` works.

## Scope

**In scope:**
- Replace simulated UniFi creation with real Terraform execution
- Create a container with Terraform
- Mount the unifi-dns module
- Write the generated JSON config to the container
- Set required environment variables and secrets (API key OR username/password)
- Run `terraform init` and `terraform apply -auto-approve`
- Capture and report actual Terraform output
- Handle errors properly

**Out of scope:**
- Modifying config generation (handled in Prompt 01)
- Cloudflare resource creation (handled in Prompt 02)
- Validation logic (handled in Prompt 04)
- Cleanup logic (handled in Prompt 05)

## Desired Behavior

### 1. Container Setup

```python
# Create Terraform container
ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

# Mount the UniFi DNS Terraform module
tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
ctr = ctr.with_directory("/module", tf_module)

# Write the unifi config JSON to a file in the container
ctr = ctr.with_new_file("/workspace/unifi.json", unifi_config_json)
```

### 2. Environment Variables

```python
# Set required variables
ctr = ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
ctr = ctr.with_env_variable("TF_VAR_api_url", api_url if api_url else unifi_url)
ctr = ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")

# Set authentication (API key OR username/password)
if unifi_api_key:
    ctr = ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
elif unifi_username and unifi_password:
    ctr = ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
    ctr = ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)
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
    report_lines.append(f"  ✓ Created UniFi DNS records")
    validation_results["unifi_dns"] = "created"
except dagger.ExecError as e:
    report_lines.append(f"  ✗ Terraform apply failed: {e.stderr}")
    validation_results["unifi_error"] = str(e)
    raise  # Re-raise to trigger cleanup
```

### 4. Error Handling

- If `terraform init` fails, raise an exception to trigger cleanup phase
- If `terraform apply` fails, raise an exception to trigger cleanup phase
- Store error details in `validation_results` for the report
- Note: UniFi may fail if the MAC address isn't found in the controller (expected for test MACs)

## Constraints & Assumptions

- The unifi config JSON is already generated (from Prompt 01)
- The `terraform/modules/unifi-dns/` directory exists
- UniFi credentials are valid (either API key or username/password)
- Use the existing `terraform_version` parameter from function signature
- Follow the same pattern as the working `deploy_unifi()` function
- UniFi deployment may fail because the test MAC address (`aa:bb:cc:dd:ee:ff`) won't exist in the controller - this is expected behavior for integration testing

## Dependencies

- Prompt 01: Fix Test Config Generation (must provide proper JSON)

## Acceptance Criteria

- [ ] Phase 3 creates a Terraform container with the correct image
- [ ] UniFi DNS module is mounted at `/module`
- [ ] UniFi config JSON is written to `/workspace/unifi.json`
- [ ] All required environment variables are set
- [ ] Authentication is passed correctly (API key OR username/password as secrets)
- [ ] `terraform init` is executed and output captured
- [ ] `terraform apply -auto-approve` is executed
- [ ] Success messages include actual Terraform output summary
- [ ] Errors are caught and reported, triggering cleanup
- [ ] State tracking variables (`validation_results`) are updated correctly
- [ ] Comment noting that UniFi may fail due to test MAC not being in controller

## Reference

- Target: Phase 3 in `test_integration` function (lines 933-940) in `src/main/main.py`
- Reference implementation: `deploy_unifi()` function (lines 113-220)
- Module path: `terraform/modules/unifi-dns/`
