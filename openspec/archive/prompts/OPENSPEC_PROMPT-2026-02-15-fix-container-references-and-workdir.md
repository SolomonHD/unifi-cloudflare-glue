# OpenSpec Prompt: Fix Container References and Working Directory Logic

## Context

The `plan` function correctly preserves container references after execution, allowing it to access files created during Terraform operations. However, `deploy_unifi`, `deploy_cloudflare`, and `destroy` have a critical bug where they lose container references. Additionally, they use fragile working directory logic that relies on string checks.

The `plan` function serves as the correct reference implementation (lines 1181-1212 for state handling, lines 1198-1207 for container reference preservation).

## Goal

Fix container reference preservation and working directory logic in deployment functions to match the `plan` function's robust implementation.

## Scope (In)

### Functions to Modify

1. **`deploy_unifi()`** (line ~356)
   - Fix container reference preservation after `terraform init` and `terraform apply`
   - Fix working directory logic for state directory vs ephemeral state
   - Ensure files can be accessed from the executed container

2. **`deploy_cloudflare()`** (line ~542)
   - Fix container reference preservation after `terraform init` and `terraform apply`
   - Fix working directory logic for state directory vs ephemeral state
   - Ensure files can be accessed from the executed container

3. **`destroy()`** (line ~1385)
   - Fix container reference preservation for both Cloudflare and UniFi destroy operations
   - Fix working directory logic throughout

### Current Bugs to Fix

**Bug 1: Container Reference Loss**

Current (incorrect) in `deploy_unifi` (lines 527-530):
```python
# WRONG: Container reference is lost!
apply_result = await ctr.with_exec([
    "terraform", "apply", "-auto-approve"
]).stdout()
# ctr still points to pre-execution container
```

Required (correct) pattern from `plan` (lines 1198-1207):
```python
# CORRECT: Save container reference after execution
unifi_ctr = unifi_ctr.with_exec(["terraform", "plan", "-out=unifi-plan.tfplan"])
_ = await unifi_ctr.stdout()
# unifi_ctr now points to post-execution container with generated files
```

**Bug 2: Fragile Working Directory Logic**

Current (incorrect) in `deploy_unifi` (line 506):
```python
# FRAGILE: String check is unreliable
ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")
```

Required (correct) pattern from `plan` (lines 1181-1187):
```python
# ROBUST: Explicit state directory handling
if using_persistent_state:
    unifi_ctr = unifi_ctr.with_directory("/state", state_dir)
    unifi_ctr = unifi_ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
    unifi_ctr = unifi_ctr.with_workdir("/state")
else:
    unifi_ctr = unifi_ctr.with_workdir("/module")
```

## Scope (Out)

- Cache busting parameters (covered in Prompt 01)
- Changes to `plan()` function (already correct)
- Changes to `test_integration()` function
- Changes to `get_tunnel_secrets()` function
- Changes to `generate_*_config()` functions

## Desired Behavior

1. Container references are preserved after each `.with_exec()` call
2. Working directory is explicitly set based on `using_persistent_state` boolean
3. No reliance on string checks like `"/module" in str(ctr)`
4. Files created during execution (like terraform.tfstate) are accessible from the preserved container
5. Consistent pattern with `plan` function implementation

## Constraints & Assumptions

- Follow the exact pattern from `plan` function (lines 1181-1212)
- Must maintain backward compatibility
- Use explicit boolean checks (`using_persistent_state`) instead of string checks
- Reassign container variable after each `.with_exec()` call
- Use `_ = await container.stdout()` pattern when output isn't needed

## Detailed Implementation Guide

### Pattern for `deploy_unifi` and `deploy_cloudflare`

Replace the current container handling (lines 496-530 in deploy_unifi):

```python
# BEFORE (fragile):
using_persistent_state = state_dir is not None
if using_persistent_state:
    ctr = ctr.with_directory("/state", state_dir)
    ctr = ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
    ctr = ctr.with_workdir("/state")
else:
    ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")

# Run terraform init
init_cmd = ["terraform", "init"]
if backend_config_file is not None:
    init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

init_result = await ctr.with_exec(init_cmd).stdout()  # BUG: lost reference

# Run terraform apply
apply_result = await ctr.with_exec([
    "terraform", "apply", "-auto-approve"
]).stdout()  # BUG: lost reference
```

With the correct pattern:

```python
# AFTER (robust):
using_persistent_state = state_dir is not None
if using_persistent_state:
    ctr = ctr.with_directory("/state", state_dir)
    ctr = ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
    _ = await ctr.stdout()  # Wait for copy to complete
    ctr = ctr.with_workdir("/state")
else:
    ctr = ctr.with_workdir("/module")

# Run terraform init
init_cmd = ["terraform", "init"]
if backend_config_file is not None:
    init_cmd.extend(["-backend-config=/root/.terraform/backend.tfbackend"])

ctr = ctr.with_exec(init_cmd)  # Save reference
_ = await ctr.stdout()

# Run terraform apply
ctr = ctr.with_exec(["terraform", "apply", "-auto-approve"])  # Save reference
apply_result = await ctr.stdout()

# Now ctr can be used to access files created during apply
# Example: state_file = await ctr.file("/state/terraform.tfstate")  # or /module/
```

### Pattern for `destroy`

The `destroy` function has similar issues in both Cloudflare (lines 1528-1599) and UniFi (lines 1622-1698) phases. Apply the same fixes:

1. Track `using_persistent_state = state_dir is not None`
2. Use explicit working directory setup (not string checks)
3. Preserve container references after each `with_exec()`
4. Use `_ = await ctr.stdout()` when output isn't needed

## Acceptance Criteria

- [ ] `deploy_unifi()` preserves container references after `terraform init`
- [ ] `deploy_unifi()` preserves container references after `terraform apply`
- [ ] `deploy_unifi()` uses explicit `using_persistent_state` boolean for workdir logic
- [ ] `deploy_unifi()` does NOT use `"/module" in str(ctr)` string check
- [ ] `deploy_cloudflare()` preserves container references after `terraform init`
- [ ] `deploy_cloudflare()` preserves container references after `terraform apply`
- [ ] `deploy_cloudflare()` uses explicit `using_persistent_state` boolean for workdir logic
- [ ] `deploy_cloudflare()` does NOT use `"/module" in str(ctr)` string check
- [ ] `destroy()` preserves container references in Cloudflare phase
- [ ] `destroy()` preserves container references in UniFi phase
- [ ] `destroy()` uses explicit `using_persistent_state` boolean for workdir logic
- [ ] `destroy()` does NOT use `"/module" in str(ctr)` string check
- [ ] All functions properly await intermediate steps with `_ = await ctr.stdout()`

## Expected Files/Areas Touched

- `src/main/main.py`:
  - `deploy_unifi()` function container handling (lines ~496-530)
  - `deploy_cloudflare()` function container handling (lines ~650-690)
  - `destroy()` function Cloudflare phase (lines ~1528-1599)
  - `destroy()` function UniFi phase (lines ~1622-1698)

## Dependencies

- Depends on: Prompt 01 - Add Cache Busting to Deploy and Destroy Functions
- Reason: The `using_persistent_state` variable and container setup patterns should be consistent with the cache busting changes

## Notes

The key insight from the `plan` function is:
1. **Always reassign** the container variable after `with_exec()`: `ctr = ctr.with_exec([...])`
2. **Then await** to get output: `output = await ctr.stdout()`
3. **Use explicit booleans** for logic branches, not string checks on the container object

This pattern is critical because Dagger containers are immutable - each operation returns a new container reference. If you don't save the reference, you lose access to any files or state created during execution.
