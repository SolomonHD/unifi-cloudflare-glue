# Change: Project Scaffolding and Directory Structure

## Why

The `unifi-cloudflare-glue` project needs a foundational structure to support a hybrid DNS infrastructure that bridges local UniFi network DNS with Cloudflare Tunnel edge DNS. Without a well-organized monorepo layout, subsequent development of KCL schemas, Terraform modules, and examples will be fragmented and difficult to maintain.

## What Changes

- Create complete directory structure following stack-separation layout
- Initialize Terraform module skeletons (`unifi-dns` and `cloudflare-tunnel`) with `versions.tf` files
- Initialize KCL module with `kcl.mod` manifest and placeholder schema files
- Create root `README.md` with project overview and quickstart guide
- Create module-specific `README.md` files with placeholder sections
- Create `.gitignore` files for Terraform state, KCL build artifacts, and credentials

## Impact

- **Affected specs**: New capabilities for project structure, terraform modules, and kcl modules
- **Affected code**: Entire project foundation - all subsequent changes depend on this structure
- **Breaking**: None (initial project setup)

## Acceptance Criteria

- [ ] All directories exist with appropriate placeholder files
- [ ] `terraform/modules/unifi-dns/versions.tf` declares required providers (Terraform >= 1.5.0, unifi ~> 0.41)
- [ ] `terraform/modules/cloudflare-tunnel/versions.tf` declares required providers (Terraform >= 1.5.0, cloudflare ~> 4.0)
- [ ] `kcl/kcl.mod` is valid KCL module manifest with proper metadata
- [ ] Root `README.md` explains the project purpose and structure
- [ ] Each module has its own `README.md` with placeholder sections
- [ ] `.gitignore` files prevent committing sensitive or generated files
