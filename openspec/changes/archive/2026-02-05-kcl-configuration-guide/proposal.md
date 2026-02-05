## Why

KCL is central to this project but minimally documented. Users struggle to understand schema structure, validation rules, and how to debug errors. Comprehensive documentation will reduce support burden and enable users to confidently configure their infrastructure without trial-and-error.

## What Changes

- Create [`docs/kcl-guide.md`](../../../docs/kcl-guide.md) with complete KCL schema reference
- Document all base schemas (Entity, Endpoint, Service, MACAddress, Hostname, Distribution)
- Document UniFi-specific schemas (UniFiConfig, UniFiEntity, UniFiEndpoint, UniFiController)
- Document Cloudflare-specific schemas (CloudflareConfig, CloudflareTunnel, TunnelService)
- Explain validation rules with rationale (MAC format, hostname requirements, DNS loop prevention, one tunnel per device)
- Add common configuration patterns (single service, multiple services, internal-only, external-only)
- Create debugging guide for syntax, type, and validation errors
- Add 4+ working example configurations in [`examples/`](../../../examples/) directory
- Add cross-references linking main README → docs → KCL module README → examples

## Capabilities

### New Capabilities
- `kcl-schema-reference`: Comprehensive documentation of all KCL schemas (base, UniFi, Cloudflare) with field descriptions, types, and examples
- `kcl-validation-rules`: Explanation of all validation rules with rationale and enforcement points
- `kcl-configuration-patterns`: Common patterns for organizing services and devices
- `kcl-debugging-guide`: Systematic approach to diagnosing and fixing KCL syntax, type, and validation errors
- `kcl-working-examples`: Multiple working example configurations covering different use cases

### Modified Capabilities
<!-- No existing capabilities are being modified - this is purely additive documentation -->

## Impact

**Documentation Structure:**
- New file: `docs/kcl-guide.md`
- Updates: `docs/README.md` (add index entry), `README.md` (add link), `kcl/README.md` (add link to guide)
- New directories: `examples/single-service/`, `examples/multiple-services/`, `examples/internal-only/`, `examples/external-only/`

**User Experience:**
- Users can reference schemas without reading source code
- Validation errors become self-service (debugging guide)
- Common patterns reduce configuration mistakes
- Working examples provide immediate starting points
- Cross-linked documentation improves discoverability

**No Breaking Changes:**
- Pure documentation addition - no schema or generator changes
- No impact on existing configurations or Terraform modules
- No external API changes
