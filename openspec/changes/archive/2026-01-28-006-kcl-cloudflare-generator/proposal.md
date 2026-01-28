# Proposal: KCL Cloudflare JSON Generator

## Change ID
`006-kcl-cloudflare-generator`

## Summary
Implement the KCL generator that transforms [`CloudflareConfig`](../../kcl/schemas/cloudflare.k:151) schema instances into Terraform-compatible JSON format for the Cloudflare Tunnel module. This generator bridges the unified KCL configuration layer with the Terraform Cloudflare provider, enabling secure public access to internal services through Cloudflare Zero Trust Tunnels.

## Motivation
With the Cloudflare schemas defined (see archived change `004-kcl-cloudflare-schemas`), we now need a generator to convert high-level KCL service definitions into the JSON format expected by the Terraform Cloudflare Tunnel module. This enables the "define once, deploy everywhere" workflow where users describe infrastructure in KCL and generate provider-specific configurations. The generator must enforce DNS loop prevention by ensuring `local_service_url` uses internal domains only.

## Scope

### In Scope
- Implement `generate_cloudflare_config()` function in [`kcl/generators/cloudflare.k`](../../kcl/generators/cloudflare.k)
- Transform [`CloudflareConfig`](../../kcl/schemas/cloudflare.k:151) to JSON matching Terraform module input schema
- Generate tunnels keyed by normalized MAC address
- Filter services by distribution (include `cloudflare_only` and `both`, exclude `unifi_only`)
- Construct `local_service_url` from service `internal_hostname` or device `friendly_hostname` + domain + port
- Generate `public_hostname` from service `public_hostname` or derive from service name + zone
- Implement DNS loop prevention validation
- Handle optional fields gracefully

### Out of Scope
- UniFi generator (already implemented in change `005`)
- Terraform module implementation (separate proposals `008` and `009`)
- Cross-provider validation (covered in proposal `007`)

## Proposed Solution

### Generator Architecture
The generator follows a functional transformation pattern similar to the UniFi generator:

1. **Input**: [`CloudflareConfig`](../../kcl/schemas/cloudflare.k:151) containing zone settings, account ID, and tunnel definitions
2. **Transform**: Map each tunnel to a MAC-keyed entry with:
   - Tunnel name and services
   - Services filtered by distribution (exclude `unifi_only`)
   - `local_service_url` constructed from internal hostnames
   - `public_hostname` derived from service configuration
3. **Validate**: Ensure no DNS loops by verifying `local_service_url` uses internal domains only
4. **Output**: JSON object matching the Cloudflare Terraform module input schema

### Key Design Decisions

1. **MAC Keying**: Tunnels dictionary uses normalized MAC address as key for easy lookup and consistency with UniFi configuration
2. **URL Construction**: `local_service_url` format: `{protocol}://{hostname}:{port}` using service protocol, internal hostname, and port
3. **Hostname Priority**: Use `service.internal_hostname` if set, otherwise fall back to `device.friendly_hostname` + internal domain
4. **DNS Loop Prevention**: Validate that `local_service_url` does not contain the public zone name to prevent resolution loops
5. **Distribution Filtering**: Only include services with `distribution` in `["cloudflare_only", "both"]`

## Dependencies

- **Depends On**: `004-kcl-cloudflare-schemas` (Cloudflare schemas must exist - archived)
- **Blocks**: `007-kcl-integration-validation` (generators needed for validation testing)

## Success Criteria

- `kcl run generators/cloudflare.k` outputs valid JSON
- JSON schema matches Cloudflare Terraform module expectations
- Tunnels are keyed by normalized MAC address (lowercase colon format)
- Services correctly filtered by distribution setting
- `local_service_url` constructed with internal domains only
- DNS loop prevention validation implemented and tested
- Generator handles optional fields gracefully

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Terraform module schema changes | Medium | Keep generator flexible; document expected schema |
| Complex URL construction logic | Low | Use KCL string interpolation; validate thoroughly |
| DNS loop prevention edge cases | High | Implement multiple validation checks; document constraints |
| MAC format inconsistencies | Low | Leverage existing `normalize_mac()` pattern from UniFi generator |

## Related Documents

- Prompt: [`006-kcl-cloudflare-generator.md`](../006-kcl-cloudflare-generator.md)
- Cloudflare Schemas: [`kcl/schemas/cloudflare.k`](../../kcl/schemas/cloudflare.k)
- Base Schemas: [`kcl/schemas/base.k`](../../kcl/schemas/base.k)
- UniFi Generator (reference pattern): [`kcl/generators/unifi.k`](../../kcl/generators/unifi.k)
- Terraform Module: [`terraform/modules/cloudflare-tunnel/`](../../terraform/modules/cloudflare-tunnel/)
