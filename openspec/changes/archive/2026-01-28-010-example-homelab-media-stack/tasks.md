# Tasks: Homelab Media Stack Example

## Overview
Ordered tasks for implementing the complete homelab media stack example.

## Phase 1: KCL Configuration

- [x] Create `examples/homelab-media-stack/main.k` with complete media server configuration
  - [x] Define media server entity with two NICs (management + media)
  - [x] Configure UniFi-only services (*arr stack)
  - [x] Configure Cloudflare-only services (Paperless-ngx, Immich)
  - [x] Configure dual-exposure services (Jellyfin, Jellyseerr)
  - [x] Add placeholder comments for user customization

- [x] Create `examples/homelab-media-stack/kcl.mod` referencing parent module
  - [x] Import schemas from parent kcl/ directory
  - [x] Set up proper module dependencies

## Phase 2: Terraform Root Module

- [x] Create `examples/homelab-media-stack/terraform/main.tf`
  - [x] Instantiate `unifi-dns` module with generated JSON
  - [x] Instantiate `cloudflare-tunnel` module with generated JSON
  - [x] Add provider configuration blocks
  - [x] Configure remote state (commented example)

- [x] Create `examples/homelab-media-stack/terraform/variables.tf`
  - [x] Variable for UniFi controller credentials
  - [x] Variable for Cloudflare API token
  - [x] Variable for generated JSON file paths

- [x] Create `examples/homelab-media-stack/terraform/versions.tf`
  - [x] Pin Terraform version (~> 1.5)
  - [x] Pin UniFi provider version
  - [x] Pin Cloudflare provider version

- [x] Create `examples/homelab-media-stack/terraform/outputs.tf`
  - [x] Output created DNS records
  - [x] Output tunnel information

## Phase 3: Documentation

- [x] Update `examples/homelab-media-stack/README.md`
  - [x] Overview section explaining the example
  - [x] Prerequisites section with all requirements
  - [x] Step-by-step deployment workflow:
    1. Clone/copy the example
    2. Customize KCL configuration (replace placeholders)
    3. Run KCL to generate JSON
    4. Configure Terraform credentials
    5. Apply UniFi module first
    6. Apply Cloudflare module
    7. Configure cloudflared with tunnel tokens
  - [x] Customization guide (adding/removing services)
  - [x] Troubleshooting common issues
  - [x] Architecture diagram (ASCII or reference)

## Phase 4: Validation

- [x] Validate KCL configuration generates proper JSON
  - [x] Run `kcl run main.k` successfully
  - [x] Verify unifi.json structure matches module input
  - [x] Verify cloudflare.json structure matches module input

- [x] Validate Terraform configuration
  - [x] Run `terraform init` successfully
  - [x] Run `terraform validate` with no errors
  - [x] Run `terraform plan` (dry-run) successfully

- [x] Cross-reference with dependencies
  - [x] Verify 007 generators produce correct output
  - [x] Verify 008 UniFi module accepts the JSON
  - [x] Verify 009 Cloudflare module accepts the JSON

## Phase 5: Polish

- [x] Add `.gitignore` for generated files
  - [x] Ignore `outputs/*.json`
  - [x] Ignore `.terraform/`
  - [x] Ignore `*.tfstate*`

- [x] Create example placeholder values guide
  - [x] Document all `<your-*>` placeholders
  - [x] Provide example valid values

- [x] Add comments in KCL explaining key decisions
  - [x] Why each service has its distribution setting
  - [x] MAC normalization explanation
  - [x] local_service_url construction

## Dependencies

- **Blocked by**: 007-kcl-integration-validation, 008-terraform-unifi-dns-module, 009-terraform-cloudflare-tunnel-module
- **Blocks**: None (terminal example)

## Estimated Effort

Small-Medium: ~4-6 hours including documentation and validation.

## Implementation Notes

### Completed 2026-01-28

- All KCL configuration files created with proper imports using `unifi_cloudflare_glue` module name
- Example uses realistic placeholder values that pass validation:
  - MAC addresses: `aa:bb:cc:dd:ee:01`, `aa:bb:cc:dd:ee:02`
  - Domain: `example.com`
  - Account ID: `a1b2c3d4e5f6789012345678901234ab`
- Terraform root module created with correct relative paths (`../../../terraform/modules/`)
- All nine services configured with proper distribution settings:
  - UniFi-only: Sonarr, Radarr, Prowlarr, Lidarr, Readarr
  - Cloudflare-only: Paperless-ngx, Immich
  - Both: Jellyfin, Jellyseerr
- README.md includes comprehensive documentation with:
  - Architecture diagram (ASCII)
  - Service distribution explanations
  - Step-by-step deployment guide
  - Customization examples
  - Troubleshooting section
- Both KCL and Terraform configurations validated successfully
