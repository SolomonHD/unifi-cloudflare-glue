# Tasks: Update Cloudflare Provider Version to v5.x

## Implementation Tasks

- [x] Update `required_providers.cloudflare.version` from `"~> 4.0"` to `"~> 5.0"` in `terraform/modules/cloudflare-tunnel/versions.tf`

## Verification Tasks

- [x] Verify the version constraint is correctly updated
- [x] Confirm source remains `"cloudflare/cloudflare"`
- [x] Confirm random provider version is unchanged (`~> 3.0`)
- [x] Confirm Terraform required_version is unchanged (`>= 1.5.0`)

## Dependencies

- **Must be applied BEFORE:**
  - migrate-cloudflare-tunnel-resource
  - migrate-tunnel-config-resource
  - migrate-dns-record-resource
  - update-zone-data-source

- **Can be applied AFTER or concurrent with:**
  - upgrade-dagger-engine
  - add-cloudflare-token-variable
