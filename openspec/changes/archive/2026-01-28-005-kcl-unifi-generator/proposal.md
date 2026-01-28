# Proposal: KCL UniFi JSON Generator

## Change ID
`005-kcl-unifi-generator`

## Summary
Implement the KCL generator that transforms [`UniFiConfig`](../../kcl/schemas/unifi.k:187) schema instances into Terraform-compatible JSON format for the UniFi DNS module. This generator bridges the unified KCL configuration layer with the Terraform UniFi provider.

## Motivation
With the UniFi schemas defined (see archived change `003-kcl-unifi-schemas`), we now need a generator to convert high-level KCL service definitions into the JSON format expected by the Terraform UniFi DNS module. This enables the "define once, deploy everywhere" workflow where users describe infrastructure in KCL and generate provider-specific configurations.

## Scope

### In Scope
- Implement `generate_unifi_config()` function in [`kcl/generators/unifi.k`](../../kcl/generators/unifi.k)
- Transform [`UniFiEntity`](../../kcl/schemas/unifi.k:98) records to device JSON format
- Generate service CNAMEs based on [`Distribution`](../../kcl/schemas/unifi.k:20) settings
- Normalize MAC addresses using [`normalize_mac()`](../../kcl/schemas/base.k:37)
- Handle round-robin A-record data for multi-NIC devices

### Out of Scope
- Cloudflare generator (separate proposal `006-kcl-cloudflare-generator`)
- Terraform module implementation (separate proposals `008` and `009`)
- Cross-provider validation (covered in proposal `007`)

## Proposed Solution

### Generator Architecture
The generator follows a functional transformation pattern:

1. **Input**: [`UniFiConfig`](../../kcl/schemas/unifi.k:187) containing devices, domain, and controller settings
2. **Transform**: Map each [`UniFiEntity`](../../kcl/schemas/unifi.k:98) to a device record with:
   - Device-level CNAMEs from `service_cnames` field
   - NIC-level records from `endpoints` with MAC normalization
   - Service filtering based on `distribution` field
3. **Output**: JSON object matching the UniFi Terraform module input schema

### Key Design Decisions

1. **MAC Normalization**: Reuse existing [`normalize_mac()`](../../kcl/schemas/base.k:37) function to ensure consistent `aa:bb:cc:dd:ee:ff` format
2. **Service Filtering**: Only include services with `distribution != "cloudflare_only"`
3. **FQDN Construction**: Always append domain suffix to hostnames for full DNS names
4. **Null Handling**: Use KCL's automatic omission of optional undefined fields

## Dependencies

- **Depends On**: `003-kcl-unifi-schemas` (UniFi schemas must exist - archived)
- **Blocks**: `007-kcl-integration-validation` (generators needed for validation testing)

## Success Criteria

- `kcl run generators/unifi.k` outputs valid JSON
- JSON schema matches UniFi Terraform module expectations
- MAC addresses normalized to lowercase colon format
- Services correctly filtered by distribution setting
- Device and NIC-level CNAMEs properly generated

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Terraform module schema changes | Medium | Keep generator flexible; document expected schema |
| Complex filtering logic | Low | Use KCL comprehensions for clarity |
| MAC format edge cases | Low | Leverage existing `normalize_mac()` function |

## Related Documents

- Prompt: [`005-kcl-unifi-generator.md`](../005-kcl-unifi-generator.md)
- UniFi Schemas: [`kcl/schemas/unifi.k`](../../kcl/schemas/unifi.k)
- Base Schemas: [`kcl/schemas/base.k`](../../kcl/schemas/base.k)
- Terraform Module: [`terraform/modules/unifi-dns/`](../../terraform/modules/unifi-dns/)
