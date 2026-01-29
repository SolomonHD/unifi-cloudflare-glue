# Proposal: Implement Real UniFi Resource Creation in Integration Tests

## Change ID
`03-implement-unifi-creation`

## Summary

Replace the simulated UniFi DNS record creation in the `test_integration` function's Phase 3 with actual Terraform execution, following the same pattern as the working `deploy_unifi()` function. This change enables the integration test to create real UniFi DNS records during test execution.

## Motivation

Currently, Phase 3 of `test_integration` (lines 1019-1026) only prints a simulated success message without actually creating UniFi DNS records. This limits the integration test's ability to validate the full DNS infrastructure pipeline. By implementing real UniFi resource creation, the integration test will:

1. Validate the complete end-to-end flow from KCL configuration to UniFi DNS records
2. Ensure the UniFi DNS Terraform module works correctly with generated configurations
3. Provide actual error feedback when UniFi operations fail
4. Align Phase 3 behavior with Phase 2 (Cloudflare), which already creates real resources

## Scope

### In Scope
- Replace simulated UniFi creation with real Terraform execution in `test_integration`
- Create a Terraform container with the correct image version
- Mount the `unifi-dns` Terraform module at `/module`
- Write the generated UniFi JSON config to `/workspace/unifi.json`
- Set required environment variables (`TF_VAR_unifi_url`, `TF_VAR_api_url`, `TF_VAR_config_file`)
- Pass authentication credentials as secrets (API key OR username/password)
- Execute `terraform init` and capture output
- Execute `terraform apply -auto-approve` and capture output
- Update `validation_results` dictionary with actual status
- Handle errors properly and trigger cleanup phase on failure
- Add comment noting that UniFi may fail due to test MAC not being in controller

### Out of Scope
- Modifying config generation (handled in Prompt 01)
- Cloudflare resource creation (handled in Prompt 02)
- Validation logic (handled in Prompt 04)
- Cleanup logic (handled in Prompt 05)

## Proposed Solution

### Container Setup Pattern

Following the existing `deploy_unifi()` function pattern:

```python
# Create Terraform container
ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")

# Mount the UniFi DNS Terraform module
tf_module = source.directory("terraform/modules/unifi-dns")
ctr = ctr.with_directory("/module", tf_module)

# Create directory with UniFi config and mount at /workspace
unifi_dir = dagger.dag.directory().with_new_file("unifi.json", unifi_json)
ctr = ctr.with_directory("/workspace", unifi_dir)
```

### Environment Variable Configuration

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

### Terraform Execution Flow

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

## Dependencies

- **Prompt 01** (`01-fix-test-config-generation`): Must provide proper UniFi JSON configuration
- **Existing Code**: `deploy_unifi()` function (lines 113-220) serves as reference implementation

## Acceptance Criteria

- [ ] Phase 3 creates a Terraform container with the correct image (`hashicorp/terraform:{terraform_version}`)
- [ ] UniFi DNS module is mounted at `/module`
- [ ] UniFi config JSON is written to `/workspace/unifi.json`
- [ ] All required environment variables are set (`TF_VAR_unifi_url`, `TF_VAR_api_url`, `TF_VAR_config_file`)
- [ ] Authentication is passed correctly (API key OR username/password as secrets)
- [ ] `terraform init` is executed and output captured
- [ ] `terraform apply -auto-approve` is executed
- [ ] Success messages include actual Terraform output summary
- [ ] Errors are caught and reported, triggering cleanup phase
- [ ] State tracking variables (`validation_results`) are updated correctly
- [ ] Comment noting that UniFi may fail due to test MAC not being in controller

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| UniFi controller doesn't have test MAC | High (expected) | Document that this is expected behavior; test MAC (`aa:bb:cc:dd:ee:ff`) won't exist in real controllers |
| Terraform module path incorrect | Medium | Use `source.directory()` to get module from source directory; fallback to project root |
| Authentication credentials missing | Medium | Validate credentials exist before Phase 3; function signature already requires them |
| Network connectivity to UniFi | Medium | Error handling will catch and report; cleanup will still run |

## References

- Target: Phase 3 in `test_integration` function (lines 1019-1026) in `src/main/main.py`
- Reference implementation: `deploy_unifi()` function (lines 113-220)
- Module path: `terraform/modules/unifi-dns/`
- Related changes: `01-fix-test-config-generation`, `02-implement-cloudflare-creation`
