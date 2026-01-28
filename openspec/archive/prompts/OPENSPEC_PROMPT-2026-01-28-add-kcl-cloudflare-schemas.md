# OpenSpec Prompt: KCL Cloudflare Schema Extensions

## Context

The Cloudflare schema extensions build on base schemas to add Cloudflare Tunnel-specific configuration. This includes tunnel definitions, ingress rules, and public DNS settings.

## Goal

Extend the base schemas with Cloudflare-specific fields for managing Zero Trust Tunnels, public hostnames, and tunnel configurations.

## Scope

### In Scope
- Define `CloudflareTunnel` schema for tunnel configuration
- Define `TunnelService` schema for ingress rules
- Define `CloudflareConfig` schema for root configuration
- Add Cloudflare-specific validation rules
- Define tunnel token handling

### Out of Scope
- UniFi-specific extensions (already defined)
- JSON generator logic (covered in later prompt)
- Cross-provider validation (covered in later prompt)

## Desired Behavior

1. **CloudflareTunnel Schema**:
   - `tunnel_name`: Unique name for the tunnel
   - `mac_address`: MAC address linking tunnel to physical device
   - `services`: List of TunnelService ingress rules
   - `credentials_path`: Optional path for tunnel credentials

2. **TunnelService Schema**:
   - `public_hostname`: Public-facing hostname (e.g., "media.example.com")
   - `local_service_url`: Internal URL MUST use UniFi internal domain
   - `no_tls_verify`: Boolean to skip TLS verification
   - `path_prefix`: Optional path prefix for routing

3. **CloudflareConfig Schema** (root configuration):
   - `zone_name`: Cloudflare zone (e.g., "example.com")
   - `account_id`: Cloudflare account ID
   - `tunnels`: Dictionary mapping MAC addresses to CloudflareTunnel objects
   - `default_no_tls_verify`: Default TLS verification setting

4. **Validation Rules**:
   - local_service_url must use internal domain (.internal.lan, .local, etc.)
   - public_hostname must use the configured zone_name
   - Each MAC address can have only one tunnel
   - no_tls_verify warnings when enabled

## Constraints & Assumptions

1. **No DNS Loops**: local_service_url must never use public hostnames
2. **One Tunnel Per MAC**: Enforce single tunnel per physical device
3. **Existing Zone**: Cloudflare zone must already exist
4. **Zone Matching**: public_hostname must belong to configured zone

## Acceptance Criteria

- [ ] `kcl/schemas/cloudflare.k` contains CloudflareTunnel schema
- [ ] `kcl/schemas/cloudflare.k` contains TunnelService schema
- [ ] `kcl/schemas/cloudflare.k` contains CloudflareConfig as root configuration
- [ ] Validation prevents DNS loops (local_service_url cannot use public domains)
- [ ] Validation ensures public hostnames match zone
- [ ] MAC to tunnel mapping is one-to-one
- [ ] Schema properly imports and references base.k
- [ ] KCL module validates without errors

## Dependencies

- **Depends On**: 002-kcl-base-schemas (base schemas must exist)

## Expected Files/Areas Touched

- `kcl/schemas/cloudflare.k` (new/complete implementation)
