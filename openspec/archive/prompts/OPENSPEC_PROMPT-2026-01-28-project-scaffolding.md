# OpenSpec Prompt: Project Scaffolding and Directory Structure

## Context

This is the first step in building the `unifi-cloudflare-glue` project - a hybrid DNS infrastructure tool that bridges local UniFi network DNS with Cloudflare Tunnel edge DNS using a unified configuration layer.

The project follows a stack-separation layout with Terraform modules for infrastructure, KCL for configuration schema, and examples for documentation.

## Goal

Establish the foundational project structure, configuration files, and build tooling needed for the entire monorepo. This creates the skeleton that all subsequent changes will build upon.

## Scope

### In Scope
- Create complete directory structure for the monorepo
- Initialize Terraform module skeletons with `versions.tf` and basic `main.tf`
- Initialize KCL module with `kcl.mod` manifest
- Create root `README.md` with project overview
- Create `.gitignore` files appropriate for Terraform and KCL
- Create empty placeholder files to establish module boundaries

### Out of Scope
- Implementation of Terraform resource logic
- KCL schema definitions (covered in subsequent prompts)
- KCL generators (covered in subsequent prompts)
- Example configurations (covered in final prompt)

## Desired Behavior

The project structure should match the stack-separation layout:

```
unifi-cloudflare-glue/
├── README.md                      # Project overview and quickstart
├── .gitignore                     # Root gitignore
├── terraform/
│   └── modules/
│       ├── unifi-dns/
│       │   ├── README.md
│       │   ├── versions.tf
│       │   ├── variables.tf       # Empty placeholders
│       │   ├── main.tf            # Empty placeholders
│       │   └── outputs.tf         # Empty placeholders
│       └── cloudflare-tunnel/
│           ├── README.md
│           ├── versions.tf
│           ├── variables.tf
│           ├── main.tf
│           └── outputs.tf
├── kcl/
│   ├── kcl.mod                    # KCL module manifest
│   ├── README.md
│   ├── schemas/
│   │   ├── base.k                 # Empty placeholder
│   │   ├── unifi.k                # Empty placeholder
│   │   └── cloudflare.k           # Empty placeholder
│   └── generators/
│       ├── unifi.k                # Empty placeholder
│       └── cloudflare.k           # Empty placeholder
└── examples/
    └── homelab-media-stack/
        └── README.md              # Empty placeholder
```

## Constraints & Assumptions

1. **Terraform Version**: Require Terraform >= 1.5.0
2. **KCL Version**: Use KCL v0.9.0 or later syntax
3. **Provider Versions**:
   - UniFi provider: `paultyng/unifi` ~> 0.41
   - Cloudflare provider: `cloudflare/cloudflare` ~> 4.0
4. **Gitignore Patterns**: Must cover Terraform state files, KCL build artifacts, and local credentials
5. **Module Independence**: Each Terraform module must be independently usable

## Acceptance Criteria

- [ ] All directories exist with appropriate `.gitkeep` or placeholder files
- [ ] `terraform/modules/unifi-dns/versions.tf` declares required providers
- [ ] `terraform/modules/cloudflare-tunnel/versions.tf` declares required providers
- [ ] `kcl/kcl.mod` is valid KCL module manifest with proper metadata
- [ ] Root `README.md` explains the project purpose and structure
- [ ] Each module has its own `README.md` with placeholder sections
- [ ] `.gitignore` files prevent committing sensitive or generated files

## Dependencies

None - this is the foundational change that enables all subsequent work.

## Expected Files/Areas Touched

- `README.md` (new)
- `.gitignore` (new)
- `terraform/modules/unifi-dns/*` (new)
- `terraform/modules/cloudflare-tunnel/*` (new)
- `kcl/kcl.mod` (new)
- `kcl/README.md` (new)
- `kcl/schemas/*.k` (new placeholders)
- `kcl/generators/*.k` (new placeholders)
- `examples/homelab-media-stack/README.md` (new)
