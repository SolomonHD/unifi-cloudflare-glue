# OpenSpec Changes Index - unifi-cloudflare-glue

This index maps the sequence of changes needed to implement the `unifi-cloudflare-glue` project - a hybrid DNS infrastructure tool bridging UniFi network DNS with Cloudflare Tunnel edge DNS.

## Change Sequence

| Order | Change ID | Description | Dependencies |
|-------|-----------|-------------|--------------|
| 001 | [project-scaffolding](./001-project-scaffolding.md) | Project structure, Terraform/KCL module skeletons, READMEs | None |
| 002 | [kcl-base-schemas](./002-kcl-base-schemas.md) | KCL base schemas (Entity, Endpoint, Service, MACAddress) | 001 |
| 003 | [kcl-unifi-schemas](./003-kcl-unifi-schemas.md) | KCL UniFi schema extensions | 002 |
| 004 | [kcl-cloudflare-schemas](./004-kcl-cloudflare-schemas.md) | KCL Cloudflare schema extensions | 002 |
| 005 | [kcl-unifi-generator](./005-kcl-unifi-generator.md) | KCL UniFi JSON generator | 003 |
| 006 | [kcl-cloudflare-generator](./006-kcl-cloudflare-generator.md) | KCL Cloudflare JSON generator | 004 |
| 007 | [kcl-integration-validation](./007-kcl-integration-validation.md) | Cross-provider validation and unified config | 003, 004, 005, 006 |
| 008 | [terraform-unifi-dns-module](./008-terraform-unifi-dns-module.md) | Terraform UniFi DNS module | 001 |
| 009 | [terraform-cloudflare-tunnel-module](./009-terraform-cloudflare-tunnel-module.md) | Terraform Cloudflare Tunnel module | 001 |
| 010 | [example-homelab-media-stack](./010-example-homelab-media-stack.md) | Working example with media services | 007, 008, 009 |

## Implementation Phases

### Phase 1: Foundation (001)
- Project scaffolding and directory structure
- Terraform module skeletons
- KCL module initialization

### Phase 2: KCL Schema Layer (002-004)
- Base schemas defining core domain model
- UniFi-specific extensions for local DNS
- Cloudflare-specific extensions for tunnels

### Phase 3: KCL Generation Layer (005-007)
- UniFi JSON generator
- Cloudflare JSON generator
- Cross-provider validation and unified entrypoint

### Phase 4: Terraform Modules (008-009)
- UniFi DNS module for local DNS management
- Cloudflare Tunnel module for edge connectivity

### Phase 5: Integration Example (010)
- Complete working example demonstrating end-to-end workflow
- Media stack services with proper categorization

## Data Flow

```
User KCL Config → KCL Validation → JSON Generation → Terraform Apply
                     ↓                ↓                    ↓
               Cross-check       unifi.json          UniFi DNS
               MACs/domains      cloudflare.json     Cloudflare Tunnel
```

## Key Constraints

1. **DNS Loop Prevention**: Cloudflare local_service_url must use internal domains only
2. **MAC Normalization**: All MAC addresses normalized to lowercase colon format
3. **One Tunnel Per MAC**: Each physical device gets one tunnel
4. **Existing Resources**: Both modules use data sources for existing infrastructure
