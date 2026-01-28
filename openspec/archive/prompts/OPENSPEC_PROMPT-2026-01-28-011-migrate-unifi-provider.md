# OpenSpec Change Prompt

## Context

The current Terraform UniFi DNS module (`terraform/modules/unifi-dns/`) was implemented using the `paultyng/unifi` provider. However, this provider does not support DNS record management resources. The correct provider to use is `filipowm/unifi` (https://registry.terraform.io/providers/filipowm/unifi/latest/docs), which provides proper DNS record resources.

The module currently uses `unifi_user` resources with `local_dns_record` as a workaround, which is not the correct approach. The filipowm provider has dedicated DNS record resources.

## Goal

Migrate the UniFi DNS module from `paultyng/unifi` provider to `filipowm/unifi` provider, implementing proper DNS record management using the provider's actual DNS resources.

## Scope

**In scope:**
- Update provider source from `paultyng/unifi` to `filipowm/unifi` in versions.tf
- Update provider version constraint appropriately
- Refactor main.tf to use filipowm provider's DNS resources (not unifi_user)
- Update data sources to use filipowm provider syntax
- Update outputs.tf if resource types change
- Update README.md to reference the correct provider and its documentation
- Ensure all DNS record types (A, CNAME) work correctly
- Maintain existing input/output interface where possible

**Out of scope:**
- Changing the input variable schema
- Adding new features beyond provider migration
- Modifying other modules (cloudflare-tunnel is separate)

## Desired Behavior

1. **Provider Update**: Use `filipowm/unifi` provider with version ~> 1.0 or latest stable
2. **DNS Resources**: Use the provider's actual DNS record resources (e.g., `unifi_dns_record` if available)
3. **A-Records**: Create A-records for device hostnames pointing to their IPs
4. **CNAMEs**: Create CNAME records for service aliases (if provider supports them)
5. **MAC Lookup**: Continue to query devices by MAC to get current IP addresses
6. **Error Handling**: Preserve existing error handling for missing devices

## Constraints & Assumptions

- Provider: filipowm/unifi (https://registry.terraform.io/providers/filipowm/unifi/latest/docs)
- The provider likely has different resource names and schemas than paultyng
- Authentication method may differ - verify in provider docs
- DNS record resources should actually exist in this provider
- Maintain backward compatibility with existing KCL-generated JSON input format

## Acceptance Criteria

- [ ] versions.tf uses `filipowm/unifi` provider
- [ ] main.tf uses provider's DNS record resources (not unifi_user workaround)
- [ ] A-records are created for device friendly_hostnames
- [ ] CNAME records are created for service_cnames (if supported)
- [ ] Data sources query UniFi for device IPs by MAC
- [ ] outputs.tf exposes created DNS records
- [ ] README.md references correct provider documentation
- [ ] terraform validate passes
- [ ] All existing functionality preserved

## Reference

- Current implementation: `unifi-cloudflare-glue/terraform/modules/unifi-dns/`
- Provider docs: https://registry.terraform.io/providers/filipowm/unifi/latest/docs
- Current change ID: 008-terraform-unifi-dns-module
