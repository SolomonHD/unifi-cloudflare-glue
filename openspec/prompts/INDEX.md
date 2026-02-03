# OpenSpec Prompts Index

This directory contains OpenSpec prompts for planned changes to the unifi-cloudflare-glue project.

## Current Prompts

### State Management Enhancements

1. **[01-add-backend-config-support.md](./01-add-backend-config-support.md)** - Add remote Terraform backend support via config file mounting
2. **[02-add-persistent-state-directory.md](./02-add-persistent-state-directory.md)** - Add persistent local state directory support with mutual exclusion

## Previous Prompts (Completed/Archived)

- **fix-test-config-domain** - Fixed test integration domain configuration
- **preserve-terraform-state** - Preserved Terraform state between operations
- **fix-state-mount-bug** - Fixed state file mounting in cleanup phase
- **fix-unifi-fqdn** - Fixed UniFi FQDN configuration

## Workflow

1. Each prompt file is numbered: `NN-<change-id>.md`
2. Prompts should be processed in order
3. Use `/openspec-proposal.md` workflow to generate proposals from each prompt
4. After implementation, archive completed prompts to `openspec/archive/`

## Creating New Prompts

When adding new prompts:
1. Use the next available number
2. Follow the standard OpenSpec prompt structure (Context, Goal, Scope, etc.)
3. Update this INDEX.md file
4. Keep prompts focused on a single, reviewable change
