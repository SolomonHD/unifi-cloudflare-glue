## Context

After successful Cloudflare tunnel deployment via [`deploy_cloudflare()`](../../src/main/main.py:422-571) or [`deploy()`](../../src/main/main.py:574-742), users need to retrieve tunnel tokens to configure [`cloudflared`](../../examples/homelab-media-stack/README.md:325) on their devices. Currently, these functions return success messages that confirm deployment but provide no guidance on the critical next step.

The [`get_tunnel_secrets()`](../../src/main/main.py:28) function was recently added (prompt 01) to retrieve tunnel tokens from Terraform state. However, users don't know this function exists or how to use it after deployment.

**Current state:**
- Deployment functions return success with backend type info
- Users must independently discover `terraform output` or [`get_tunnel_secrets()`](../../src/main/main.py:28)
- Example documentation shows the workflow but users don't reference it during deployment
- Poor handoff between deployment completion and configuration start

**Constraints:**
- Success messages must not include actual tunnel tokens (security)
- Guidance must reflect actual deployment parameters (account ID, zone, backend)
- Must preserve existing success indicators and formatting
- Line length should remain under 80 characters where possible

## Goals / Non-Goals

**Goals:**
- Add clear, actionable next-step guidance to deployment success messages
- Show both Terraform and Dagger retrieval options
- Parameterize Dagger commands with actual deployment values
- Maintain backward compatibility with existing success message format
- Keep guidance concise (under 20 lines)

**Non-Goals:**
- Including actual tunnel tokens in success messages (security risk)
- Modifying other function success messages (`plan()`, `destroy()`, etc.)
- Changing error message formatting
- Adding new function parameters for guidance customization
- Supporting credential retrieval methods beyond Terraform/Dagger

## Decisions

### Decision 1: Add guidance to both deploy_cloudflare() and deploy()

**Rationale:** Both functions can successfully deploy Cloudflare tunnels, so both need guidance.

**Alternatives considered:**
- Only add to [`deploy()`](../../src/main/main.py:574-742) - rejected because users may call [`deploy_cloudflare()`](../../src/main/main.py:422-571) directly
- Create separate formatting function - rejected as overkill for simple string concatenation
- Use Python format strings - rejected in favor of explicit concatenation for maintainability

**Implementation:**
- [`deploy_cloudflare()`](../../src/main/main.py:422-571): Add after line 563 before final return
- [`deploy()`](../../src/main/main.py:574-742): Add in final summary section, only if both deployments succeed

### Decision 2: Include both Terraform and Dagger command options

**Rationale:** Users may have Terraform installed locally or prefer native Terraform workflows. Providing both options respects different workflows.

**Alternatives considered:**
- Only Dagger command - rejected because some users may not have Dagger locally
- Only Terraform - rejected because inconsistent with project's Dagger-first approach
- Let user choose via parameter - rejected as premature complexity

**Implementation:**
- Show Terraform command first (simpler, fewer parameters)
- Show Dagger command second (recommended, more consistent with project)
- Label Dagger option with "(recommended)"

### Decision 3: Parameterize Dagger commands with actual deployment values

**Rationale:** Copy-paste commands improve user experience. Placeholder values force users to manually substitute, increasing friction.

**Alternatives considered:**
- Use placeholder values (`<account-id>`, `<zone>`) - rejected due to poor UX
- Generate command in separate function - rejected as unnecessary abstraction
- Store command template as class variable - rejected due to parameter differences between functions

**Implementation:**
- Build Dagger command string using f-strings with actual parameter values
- Include backend flags conditionally based on `backend_type`
- Use multi-line format with backslash continuations

### Decision 4: Source directory differs between deploy_cloudflare() and deploy()

**Rationale:** Functions use different source directories for Terraform modules.

**Implementation:**
- [`deploy_cloudflare()`](../../src/main/main.py:422-571): `--source=.` (expects user in project root with Terraform files)
- [`deploy()`](../../src/main/main.py:574-742): `--source=./kcl` (use KCL-generated Terraform in kcl directory)

This reflects the actual directory structure users work with in each context.

### Decision 5: Conditional guidance in deploy() based on both-success

**Rationale:** Guidance is only useful when Cloudflare deployment succeeds. If UniFi succeeds but Cloudflare fails, there are no tunnel tokens to retrieve.

**Implementation:**
- Check `"✓ Success" in cloudflare_result` and `"✓ Success" in unifi_result`
- Add guidance block only inside the both-success branch
- Preserve existing failure messaging

### Decision 6: Visual separators for guidance section

**Rationale:** Distinguish guidance from deployment logs which may be verbose.

**Alternatives considered:**
- ANSI color codes - rejected due to terminal compatibility issues
- Blank lines only - rejected as insufficient visual separation
- Section with borders - rejected as too heavy

**Implementation:**
- Dash separator lines (60 characters: `"-" * 60`)
- Clear section header: "Next Step: Retrieve Tunnel Credentials"
- Numbered steps for clarity (1. Terraform, 2. Dagger, 3. Install)

## Risks / Trade-offs

### Risk: Message length increases significantly
[Risk] Success messages grow from ~5 lines to ~25 lines.
→ **Mitigation:** Keep guidance concise, use line continuations, users prefer complete info over brevity.

### Risk: Commands become outdated if function signatures change
[Risk] If [`get_tunnel_secrets()`](../../src/main/main.py:28) parameters change, guidance will be incorrect.
→ **Mitigation:** Unit tests will verify command includes required parameters. Manual maintenance needed if signature changes.

### Risk: Users still skip reading success messages
[Risk] Users may not scroll up to read full output.
→ **Mitigation:** Can't force users to read; providing clear guidance is best we can do. Visual separators help.

### Trade-off: Example commands assume environment variable for CF_TOKEN
[Trade-off] Guidance shows `--cloudflare-token=env:CF_TOKEN` but users may have different variable names.
→ **Accept:** Common convention; alternative would be placeholder `env:YOUR_CF_TOKEN` which is also imperfect.

### Trade-off: Backend config file path hardcoded as "./backend.hcl"
[Trade-off] Actual filename may differ from example.
→ **Accept:** Most common convention; users can adjust path if needed. True path not stored in deployment parameters.

### Trade-off: Terraform command doesn't include backend flags
[Trade-off] `terraform output` command assumes user is in same directory context as deployment.
→ **Accept:** Terraform commands are environment-dependent anyway; users familiar with Terraform understand this.

## Migration Plan

No migration needed - this is a purely additive change to success message formatting.

**Deployment:**
1. Merge changes to main
2. No version bump required (non-breaking enhancement)
3. Users immediately benefit on next deployment

**Rollback:**
If guidance causes issues (e.g., terminal rendering problems):
1. Revert commit
2. Users see original terse success messages
3. No data or state impact

## Open Questions

None - design is straightforward string formatting enhancement.
