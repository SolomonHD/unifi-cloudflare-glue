# Change: Migrate UniFi DNS Module to filipowm/unifi Provider

## Why

The current Terraform UniFi DNS module uses the `paultyng/unifi` provider which does not support dedicated DNS record management resources. The implementation relies on a workaround using `unifi_user` resources with the `local_dns_record` attribute, which is not the intended use of that resource type.

The `filipowm/unifi` provider (https://registry.terraform.io/providers/filipowm/unifi/latest/docs) provides proper DNS record resources that allow direct management of DNS records in UniFi controllers. Migrating to this provider will:

- Use provider-native DNS resources instead of client alias workarounds
- Enable proper A-record and CNAME management
- Align with the provider's intended resource model
- Support future DNS record types if the provider adds them

## What Changes

- Update provider source from `paultyng/unifi` to `filipowm/unifi` in versions.tf
- Update provider version constraint to ~> 1.0 (latest stable)
- Refactor main.tf to use `unifi_dns_record` resources instead of `unifi_user.local_dns_record`
- Update data sources to use `filipowm/unifi` provider syntax
- Update outputs.tf to reference new resource types
- Update README.md to reference the correct provider and its documentation
- Verify all DNS record types (A, CNAME if supported) work correctly
- Maintain existing input/output interface for backward compatibility

## Impact

- Affected specs: `terraform-module` capability
- Affected code:
  - `terraform/modules/unifi-dns/versions.tf` - Provider source and version update
  - `terraform/modules/unifi-dns/main.tf` - Resource type changes (unifi_user → unifi_dns_record)
  - `terraform/modules/unifi-dns/outputs.tf` - Resource reference updates
  - `terraform/modules/unifi-dns/README.md` - Provider documentation update
- Provider authentication may differ - documentation update required

## Dependencies

- Depends on: Existing UniFi DNS module (`008-terraform-unifi-dns-module`)
- No changes to KCL generator output format required (maintain backward compatibility)

## Reference

- Provider docs: https://registry.terraform.io/providers/filipowm/unifi/latest/docs
- Current implementation: `terraform/modules/unifi-dns/`
