# OpenSpec Change Prompt 05: Implement Real Resource Cleanup

## Context

Currently, Phase 5 (the `finally` block, lines 979-1011) of `test_integration` only prints simulated cleanup messages without actually destroying resources. Real cleanup must run `terraform destroy` to remove the Cloudflare tunnels, DNS records, and UniFi DNS records created during the test.

## Goal

Implement real cleanup by executing `terraform destroy` for both Cloudflare and UniFi resources.

## Scope

**In scope:**
- Replace simulated cleanup with real Terraform destroy execution
- Create containers with Terraform for cleanup (separate from creation containers)
- Mount the appropriate Terraform modules
- Write the config JSON files (needed for destroy)
- Set required environment variables and secrets
- Run `terraform init` and `terraform destroy -auto-approve`
- Handle cleanup errors gracefully (don't fail if resources already gone)
- Update cleanup status in the report

**Out of scope:**
- Resource creation (handled in Prompts 02 and 03)
- Validation logic (handled in Prompt 04)
- Modifying the overall test flow or error handling

## Desired Behavior

### 1. Cloudflare Cleanup

```python
# Phase 5: Guaranteed Cleanup
if cleanup:
    report_lines.append("")
    report_lines.append("PHASE 5: Cleanup (guaranteed execution)...")

    # Cleanup Cloudflare resources first (reverse order of creation)
    report_lines.append("  Cleaning up Cloudflare resources...")
    
    try:
        # Create cleanup container
        cf_cleanup_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")
        
        # Mount module
        tf_module = dagger.dag.directory().directory("terraform/modules/cloudflare-tunnel")
        cf_cleanup_ctr = cf_cleanup_ctr.with_directory("/module", tf_module)
        
        # Write config file (needed for destroy)
        cf_cleanup_ctr = cf_cleanup_ctr.with_new_file("/workspace/cloudflare.json", configs["cloudflare"])
        
        # Set environment variables
        cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_cloudflare_account_id", cloudflare_account_id)
        cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_zone_name", cloudflare_zone)
        cf_cleanup_ctr = cf_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/cloudflare.json")
        cf_cleanup_ctr = cf_cleanup_ctr.with_secret_variable("TF_VAR_cloudflare_token", cloudflare_token)
        
        # Set working directory and run destroy
        cf_cleanup_ctr = cf_cleanup_ctr.with_workdir("/module")
        
        # Init (required before destroy)
        await cf_cleanup_ctr.with_exec(["terraform", "init"]).stdout()
        
        # Destroy
        destroy_output = await cf_cleanup_ctr.with_exec([
            "terraform", "destroy", "-auto-approve"
        ]).stdout()
        
        report_lines.append(f"    ✓ Destroyed tunnel: {tunnel_name}")
        report_lines.append(f"    ✓ Deleted DNS record: {test_hostname}")
        cleanup_status["cloudflare"] = "success"
    except Exception as e:
        cleanup_status["cloudflare"] = f"failed: {str(e)}"
        report_lines.append(f"    ✗ Failed to cleanup Cloudflare: {str(e)}")
        report_lines.append("      (Resources may need manual cleanup)")
```

### 2. UniFi Cleanup

```python
    # Cleanup UniFi resources second
    report_lines.append("  Cleaning up UniFi resources...")
    
    try:
        # Create cleanup container
        unifi_cleanup_ctr = dagger.dag.container().from_(f"hashicorp/terraform:{terraform_version}")
        
        # Mount module
        tf_module = dagger.dag.directory().directory("terraform/modules/unifi-dns")
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_directory("/module", tf_module)
        
        # Write config file
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_new_file("/workspace/unifi.json", configs["unifi"])
        
        # Set environment variables
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_unifi_url", unifi_url)
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_api_url", api_url if api_url else unifi_url)
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_env_variable("TF_VAR_config_file", "/workspace/unifi.json")
        
        # Set authentication
        if unifi_api_key:
            unifi_cleanup_ctr = unifi_cleanup_ctr.with_secret_variable("TF_VAR_unifi_api_key", unifi_api_key)
        elif unifi_username and unifi_password:
            unifi_cleanup_ctr = unifi_cleanup_ctr.with_secret_variable("TF_VAR_unifi_username", unifi_username)
            unifi_cleanup_ctr = unifi_cleanup_ctr.with_secret_variable("TF_VAR_unifi_password", unifi_password)
        
        # Set working directory and run destroy
        unifi_cleanup_ctr = unifi_cleanup_ctr.with_workdir("/module")
        
        # Init
        await unifi_cleanup_ctr.with_exec(["terraform", "init"]).stdout()
        
        # Destroy
        destroy_output = await unifi_cleanup_ctr.with_exec([
            "terraform", "destroy", "-auto-approve"
        ]).stdout()
        
        report_lines.append(f"    ✓ Deleted UniFi DNS records")
        cleanup_status["unifi"] = "success"
    except Exception as e:
        cleanup_status["unifi"] = f"failed: {str(e)}"
        report_lines.append(f"    ✗ Failed to cleanup UniFi: {str(e)}")
```

### 3. State File Cleanup

```python
    # Note: Terraform state is in the container, so it's automatically cleaned up
    # when the container is destroyed. No local state files to clean.
    report_lines.append("  Cleaning up local state files...")
    report_lines.append("    ✓ Terraform state is container-local (automatically cleaned)")
    cleanup_status["state_files"] = "success"
```

### 4. Cleanup Summary

```python
    report_lines.append("")
    report_lines.append("-" * 60)
    report_lines.append("CLEANUP SUMMARY")
    report_lines.append("-" * 60)
    report_lines.append(f"  Cloudflare: {cleanup_status['cloudflare']}")
    report_lines.append(f"  UniFi: {cleanup_status['unifi']}")
    report_lines.append(f"  State Files: {cleanup_status['state_files']}")
    
    # Warning if any cleanup failed
    if not all(v == "success" for v in cleanup_status.values()):
        report_lines.append("")
        report_lines.append("⚠ WARNING: Some resources may not have been cleaned up!")
        report_lines.append("   Please verify manually in Cloudflare and UniFi dashboards.")
```

## Constraints & Assumptions

- Cleanup must run in the `finally` block to guarantee execution
- Cleanup errors should be caught and reported but not re-raised (don't mask original errors)
- Both Cloudflare and UniFi cleanup should be attempted even if one fails
- Terraform state is stored in the container (local backend), so state files don't persist
- The same config JSON used for creation must be available for destroy
- Use separate containers for Cloudflare and UniFi cleanup to avoid conflicts

## Dependencies

- Prompt 01: Fix Test Config Generation (configs must be available)
- Prompt 02: Implement Cloudflare Creation (resources exist to destroy)
- Prompt 03: Implement UniFi Creation (resources exist to destroy)

## Acceptance Criteria

- [ ] Phase 5 creates separate Terraform containers for Cloudflare and UniFi cleanup
- [ ] Both Terraform modules are mounted in their respective containers
- [ ] Config JSON files are written to both containers
- [ ] All required environment variables and secrets are set in both containers
- [ ] `terraform init` is run in both containers before destroy
- [ ] `terraform destroy -auto-approve` is executed for Cloudflare resources
- [ ] `terraform destroy -auto-approve` is executed for UniFi resources
- [ ] Cleanup errors are caught and logged without raising
- [ ] Cleanup status is accurately reported in the summary
- [ ] Warning is displayed if any cleanup step fails
- [ ] State file cleanup notes that state is container-local

## Reference

- Target: Phase 5 (finally block) in `test_integration` function (lines 979-1011) in `src/main/main.py`
- Reference implementation: `destroy()` function (lines 431-623)
- Cloudflare module: `terraform/modules/cloudflare-tunnel/`
- UniFi module: `terraform/modules/unifi-dns/`
