# OpenSpec Prompt: KCL Cloudflare JSON Generator

## Context

The Cloudflare generator transforms CloudflareConfig schema instances into JSON output suitable for the Terraform Cloudflare Tunnel module. This includes tunnel definitions, ingress rules, and service mappings.

## Goal

Implement the KCL generator that converts CloudflareConfig into Terraform-compatible JSON format for Cloudflare Tunnel management.

## Scope

### In Scope
- Implement `generate_cloudflare_config()` function
- Transform tunnels keyed by MAC address
- Generate ingress rules for each service
- Construct local_service_url from service and endpoint info
- Validate no DNS loops in generated URLs

### Out of Scope
- UniFi generator (already implemented)
- Terraform module implementation (separate prompts)
- Cross-provider validation (covered in later prompt)

## Desired Behavior

1. **Input**: CloudflareConfig schema instance
2. **Output**: JSON matching the Cloudflare Terraform module input schema:

```json
{
  "zone_name": "example.com",
  "cloudflare_account_id": "xxx",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "tunnel-media",
      "services": [{
        "public_hostname": "media.example.com",
        "local_service_url": "http://jellyfin.internal.lan:8096",
        "no_tls_verify": true
      }]
    }
  }
}
```

3. **Generation Rules**:
   - Tunnels keyed by normalized MAC address
   - One tunnel per MAC (enforced by schema, validated here)
   - Services filtered to `cloudflare_only` or `both` distribution
   - local_service_url constructed from service internal_hostname or friendly_hostname + domain + port
   - public_hostname uses service public_hostname or generates from name + zone

4. **DNS Loop Prevention**:
   - Validate local_service_url uses internal domain only
   - Reject URLs containing the public zone name
   - Log warnings for potential issues

## Constraints & Assumptions

1. **MAC Key**: Tunnels dictionary uses MAC as key for easy lookup
2. **URL Construction**: local_service_url format: `{protocol}://{hostname}:{port}`
3. **Hostname Priority**: Use service.internal_hostname if set, else device.friendly_hostname
4. **Zone Consistency**: All public hostnames must use the configured zone

## Acceptance Criteria

- [ ] `kcl/generators/cloudflare.k` contains `generate_cloudflare_config()` function
- [ ] Generator outputs valid JSON matching Cloudflare module input schema
- [ ] Tunnels are keyed by normalized MAC address
- [ ] Services filtered by distribution (excludes unifi_only)
- [ ] local_service_url constructed with internal domains only
- [ ] DNS loop prevention validation implemented
- [ ] Generator handles optional fields gracefully
- [ ] Generator can be called from KCL with `generate_cloudflare_config(config)`

## Dependencies

- **Depends On**: 004-kcl-cloudflare-schemas (Cloudflare schemas must exist)

## Expected Files/Areas Touched

- `kcl/generators/cloudflare.k` (new/complete implementation)
