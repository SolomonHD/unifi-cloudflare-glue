# Tasks: Project Scaffolding

## 1. Root Project Files

- [x] Create root `README.md` with project overview, purpose, and quickstart
- [x] Create root `.gitignore` for Terraform and KCL artifacts
- [x] Verify root directory structure exists

## 2. Terraform Module Structure

### 2.1 unifi-dns Module
- [x] Create `terraform/modules/unifi-dns/` directory structure
- [x] Create `versions.tf` with Terraform >= 1.5.0 and unifi provider ~> 0.41
- [x] Create empty `main.tf` placeholder
- [x] Create empty `variables.tf` placeholder
- [x] Create empty `outputs.tf` placeholder
- [x] Create `README.md` with module purpose and placeholder sections

### 2.2 cloudflare-tunnel Module
- [x] Create `terraform/modules/cloudflare-tunnel/` directory structure
- [x] Create `versions.tf` with Terraform >= 1.5.0 and cloudflare provider ~> 4.0
- [x] Create empty `main.tf` placeholder
- [x] Create empty `variables.tf` placeholder
- [x] Create empty `outputs.tf` placeholder
- [x] Create `README.md` with module purpose and placeholder sections

## 3. KCL Module Structure

- [x] Create `kcl/` directory structure
- [x] Create `kcl.mod` manifest with module metadata
- [x] Create `README.md` explaining KCL schemas and generators
- [x] Create `schemas/` subdirectory with placeholder files:
  - [x] `base.k` - Base schemas (Entity, Endpoint, Service, MACAddress)
  - [x] `unifi.k` - UniFi-specific schemas (UniFiClient, UniFiDNSRecord)
  - [x] `cloudflare.k` - Cloudflare-specific schemas (CloudflareTunnel, CloudflareIngress)
- [x] Create `generators/` subdirectory with placeholder files:
  - [x] `unifi.k` - UniFi configuration generator
  - [x] `cloudflare.k` - Cloudflare configuration generator

## 4. Examples Structure

- [x] Create `examples/homelab-media-stack/` directory
- [x] Create `README.md` placeholder for example documentation

## 5. Validation

- [x] Run `terraform init` validation in both module directories (verify versions.tf syntax)
  - [x] unifi-dns module: Terraform init successful with unifi provider v0.41.0
  - [x] cloudflare-tunnel module: Terraform init successful with cloudflare provider v4.52.5
- [x] Run KCL validation on all schema and generator files
  - [x] schemas/base.k: Valid KCL syntax
  - [x] schemas/unifi.k: Valid KCL syntax
  - [x] schemas/cloudflare.k: Valid KCL syntax
  - [x] generators/unifi.k: Valid KCL syntax
  - [x] generators/cloudflare.k: Valid KCL syntax
- [x] Verify all expected files exist with correct permissions
- [x] Confirm `.gitignore` covers:
  - [x] Terraform state files (`*.tfstate`, `*.tfstate.*`)
  - [x] Terraform plan files (`*.tfplan`)
  - [x] Terraform lock file (`.terraform.lock.hcl`)
  - [x] `.terraform/` directory
  - [x] KCL build artifacts
  - [x] Local credential files
