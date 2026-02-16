# OpenSpec Change Prompt

## Context

The `get_tunnel_secrets` Dagger function in `/home/solomong/Code/TF_Modules/unifi-cloudflare-glue/src/main/main.py` returns inconsistent results due to Dagger's aggressive multi-level caching. Sometimes it returns tunnel secrets correctly, sometimes it returns empty results. This is because the function lacks any cache-busting mechanism.

Other functions in the same module (`deploy()`, `destroy()`, `test_integration()`) successfully implement cache busting using a 3-level pattern per the project's dagger.md coding rules.

## Goal

Add comprehensive cache-busting capability to the `get_tunnel_secrets()` function to ensure consistent, deterministic results on every invocation when accessing remote Terraform state (especially from remote backends like S3).

## Scope

**In scope:**
- Add `cache_buster` parameter to `get_tunnel_secrets()` function signature
- Apply cache busting at container environment level
- Apply cache busting at terraform command execution level  
- Apply cache busting at return value level (for function result cache)
- Update function docstring with cache-buster usage examples
- Follow the exact same pattern as deploy(), destroy(), and test_integration()

**Out of scope:**
- Modifying other functions
- Changing the backend configuration or state management logic
- Altering the output format options or parsing logic

## Desired Behavior

When called with `--cache-buster=$(date +%s)`, the function should:
1. Accept the cache_buster parameter (Annotated[str, Doc(...)])
2. Add CACHE_BUSTER environment variable to the container if cache_buster is provided
3. Wrap `terraform output` commands with shell comment containing cache_buster value
4. Append execution ID to the return value when cache_buster is provided
5. Always fetch fresh Terraform output data instead of using cached results

## Constraints & Assumptions

**Constraints:**
- Must follow dagger.md cache busting rules exactly
- Cache busting must be applied at ALL levels (per dagger.md: container env, exec command, return value)
- Parameter must be optional with empty string default (consistent with other functions)
- Must not break existing callers who don't use cache_buster parameter

**Assumptions:**
- The cache-busting pattern used in deploy(), destroy(), test_integration() is proven to work
- The symptom "sometimes get secrets, sometimes empty" is caused by Dagger caching
- Remote backends (S3, Azure, etc.) state fetching is subject to caching
- The terraform output commands (lines 2901-2944) are the primary cache target

## Acceptance Criteria

- [ ] `cache_buster` parameter added to function signature with proper type annotation and documentation
- [ ] Container environment variable `CACHE_BUSTER` set when cache_buster is provided
- [ ] All three `terraform output` execution commands wrapped with shell comment cache busting
- [ ] Return value includes execution ID when cache_buster is provided (both human and JSON formats)
- [ ] Function docstring updated with cache-buster usage examples
- [ ] Implementation matches the pattern in deploy() function (lines 423, 622-624, 769-771, 789-791)
- [ ] No breaking changes - existing callers without cache_buster still work
- [ ] Cache busting applied at directory, container, command, and return levels per dagger.md rules
