# OpenSpec Prompts Index

This directory contains OpenSpec change prompts for the unifi-cloudflare-glue project.

## Prompts

### 01-add-get-tunnel-secrets-function.md
**Status**: Pending  
**Description**: Add `get_tunnel_secrets()` Dagger function to retrieve Cloudflare tunnel tokens from Terraform state.

Creates a new function that allows users to retrieve tunnel credentials on-demand after deployment, without storing sensitive tokens in deployment logs.

**Dependencies**: None

---

### 02-add-tunnel-token-guidance-to-deploy.md
**Status**: Pending  
**Description**: Update `deploy()` and `deploy_cloudflare()` functions to add guidance messages about retrieving tunnel tokens.

Modifies success messages in deployment functions to inform users how to retrieve tunnel secrets using either Terraform outputs or the new Dagger function.

**Dependencies**: 01-add-get-tunnel-secrets-function.md (for Dagger command example)

---

## Execution Order

1. Implement `01-add-get-tunnel-secrets-function.md` first (creates the function)
2. Then implement `02-add-tunnel-token-guidance-to-deploy.md` (adds references to the new function)

## About This Directory

Each prompt file follows OpenSpec format with:
- Context: Background and motivation
- Goal: What this change accomplishes
- Scope: What's in/out of scope
- Desired Behavior: Expected functionality
- Constraints & Assumptions: Technical limitations
- Acceptance Criteria: Testable requirements

To implement a prompt:
1. Copy the prompt to `OPENSPEC_PROMPT.md` at project root
2. Run your OpenSpec proposal workflow
3. Review and implement the generated proposal
