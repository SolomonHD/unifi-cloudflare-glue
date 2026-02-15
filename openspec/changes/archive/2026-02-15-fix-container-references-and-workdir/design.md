## Context

The `deploy_unifi()`, `deploy_cloudflare()`, and `destroy()` functions in the Dagger module have critical bugs related to container reference management and working directory logic. These bugs were identified during code review of the `plan()` function, which correctly implements the required patterns.

### Current State

**Bug 1: Container Reference Loss**
The deployment functions lose container references after `with_exec()` calls:
```python
# WRONG - Container reference is lost!
apply_result = await ctr.with_exec([
    "terraform", "apply", "-auto-approve"
]).stdout()
# ctr still points to pre-execution container
```

This prevents access to files created during execution, such as `terraform.tfstate`.

**Bug 2: Fragile Working Directory Logic**
The functions use unreliable string checks to determine working directory:
```python
# FRAGILE: String check is unreliable
ctr = ctr.with_workdir("/module" if "/module" in str(ctr) else "/workspace")
```

This approach depends on string representation of container objects, which is implementation-dependent and fragile.

### Reference Implementation

The `plan()` function (lines 1181-1212) demonstrates the correct pattern:
```python
# CORRECT: Save container reference after execution
unifi_ctr = unifi_ctr.with_exec(["terraform", "plan", "-out=unifi-plan.tfplan"])
_ = await unifi_ctr.stdout()
# unifi_ctr now points to post-execution container with generated files
```

And for working directory logic (lines 1181-1187):
```python
# ROBUST: Explicit state directory handling
if using_persistent_state:
    unifi_ctr = unifi_ctr.with_directory("/state", state_dir)
    unifi_ctr = unifi_ctr.with_exec(["sh", "-c", "cp -r /module/* /state/ && ls -la /state"])
    unifi_ctr = unifi_ctr.with_workdir("/state")
else:
    unifi_ctr = unifi_ctr.with_workdir("/module")
```

## Goals / Non-Goals

**Goals:**
- Fix container reference preservation in `deploy_unifi()`, `deploy_cloudflare()`, and `destroy()`
- Replace fragile string checks with explicit `using_persistent_state` boolean logic
- Ensure files created during execution are accessible from preserved container references
- Align all deployment functions with the proven `plan()` implementation pattern
- Maintain backward compatibility (no API changes)

**Non-Goals:**
- Changes to `plan()` function (already correct)
- Changes to `test_integration()` function
- Changes to `get_tunnel_secrets()` function
- Changes to `generate_*_config()` functions
- Adding new features or capabilities beyond bug fixes

## Decisions

### Decision: Use Reassignment Pattern for Container References
**Rationale:** Dagger containers are immutable - each operation returns a new container. The reassignment pattern (`ctr = ctr.with_exec(...)`) is the idiomatic way to preserve access to execution results.

**Alternatives considered:**
- Using a container manager class: Would add unnecessary complexity for this fix
- Passing containers through a wrapper: Would require significant refactoring

### Decision: Explicit Boolean for State Directory Detection
**Rationale:** Using `using_persistent_state = state_dir is not None` is explicit, testable, and not dependent on container string representation.

**Alternatives considered:**
- Keeping string checks: Rejected due to fragility and potential for silent failures
- Using container inspection methods: Would couple logic to Dagger internals

### Decision: Use `_ = await ctr.stdout()` for Intermediate Steps
**Rationale:** This pattern clearly indicates the operation is executed for side effects only, while still preserving the container reference.

**Alternatives considered:**
- Using `.sync()` or similar: Not available in the Dagger Python SDK
- Discarding the await entirely: Would create race conditions

### Decision: Apply Pattern Consistently Across All Functions
**Rationale:** Consistency reduces cognitive load and prevents regression. The `plan()` function already proves this pattern works.

**Alternatives considered:**
- Fixing only the most critical function: Would leave technical debt
- Creating utility functions: Premature abstraction for this scope

## Risks / Trade-offs

**Risk:** Existing code may depend on the buggy behavior (unlikely but possible)
→ **Mitigation:** Thorough testing of `deploy` and `destroy` functions after changes

**Risk:** Container reference changes could affect file access paths
→ **Mitigation:** Ensure working directory logic is correct and tested with both persistent and ephemeral state

**Risk:** Forgotten container reference updates in edge cases
→ **Mitigation:** Code review checklist and search for all `.with_exec()` calls

**Risk:** Tests may be mocking container behavior incorrectly
→ **Mitigation:** Run full integration tests after changes

## Migration Plan

This is a bug fix with no migration required:
1. Changes are internal implementation only
2. External API remains unchanged
3. No user-facing behavior changes (except fixing broken behavior)
4. No database migrations or state changes

## Open Questions

None - the `plan()` function provides a complete reference implementation that has been tested and validated.
