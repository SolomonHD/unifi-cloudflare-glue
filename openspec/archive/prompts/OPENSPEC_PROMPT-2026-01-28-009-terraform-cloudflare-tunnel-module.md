# OpenSpec Prompt: Terraform Cloudflare Tunnel Module

## Context

The Terraform Cloudflare Tunnel module manages Zero Trust Tunnels and their configurations. It creates one tunnel per MAC address with multiple ingress rules, and outputs tunnel tokens for external cloudflared deployment.

## Goal

Implement a complete Terraform module that manages Cloudflare Tunnels, DNS records, and tunnel configurations based on JSON input mapping MAC addresses to tunnels and services.

## Scope

### In Scope
- Define all input variables with validation
- Use data source for existing Cloudflare Zone (do not create)
- Create `cloudflare_tunnel` resource for each MAC
- Create `cloudflare_tunnel_config` with ingress rules
- Create `cloudflare_record` CNAMEs pointing to tunnel
- Output tunnel tokens and credentials JSON
- Prevent DNS loop configurations

### Out of Scope
- UniFi module (separate prompt)
- Cloudflared container deployment (external)
- KCL configuration (already implemented)

## Desired Behavior

1. **Input Variables**:
   ```hcl
   variable "config" {
     type = object({
       zone_name             = string
       cloudflare_account_id = string
       tunnels = map(object({
         tunnel_name = string
         services = list(object({
           public_hostname = string
           local_service_url = string
           no_tls_verify   = optional(bool, false)
         }))
       }))
     })
   }
   ```

2. **Data Sources**:
   - Query existing Cloudflare Zone by name
   - Fail if zone does not exist

3. **Resources Created**:
   - `cloudflare_tunnel`: One per MAC address
   - `cloudflare_tunnel_config`: Ingress rules for each tunnel
   - `cloudflare_record`: CNAME from public_hostname to tunnel

4. **Ingress Rules**:
   - Each service becomes an ingress rule
   - local_service_url must use internal domain (validated)
   - Default catch-all rule returns 404

5. **Outputs**:
   - `tunnel_ids`: Map of MAC to tunnel ID
   - `tunnel_tokens`: Map of MAC to tunnel token (sensitive)
   - `credentials_json`: Map of MAC to credentials file content (sensitive)
   - `public_hostnames`: List of created public hostnames

## Constraints & Assumptions

1. **Existing Zone**: Cloudflare zone must already exist
2. **DNS Loop Prevention**: local_service_url cannot contain zone_name
3. **Token Security**: Mark tunnel tokens as sensitive
4. **External Deployment**: Tokens output for external cloudflared use

## Acceptance Criteria

- [ ] `terraform/modules/cloudflare-tunnel/variables.tf` defines all inputs
- [ ] `terraform/modules/cloudflare-tunnel/main.tf` creates tunnels and configs
- [ ] `terraform/modules/cloudflare-tunnel/outputs.tf` returns tokens (sensitive)
- [ ] Zone data source verifies existing zone
- [ ] DNS loop validation prevents misconfiguration
- [ ] One tunnel created per MAC address
- [ ] CNAME records point public hostnames to tunnels
- [ ] Ingress rules include catch-all 404
- [ ] Tunnel tokens marked as sensitive
- [ ] Module README documents usage and security
- [ ] Terraform validates successfully

## Dependencies

- **Depends On**: 001-project-scaffolding (module structure must exist)
- **Soft Depends On**: 006-kcl-cloudflare-generator (generates input format)

## Expected Files/Areas Touched

- `terraform/modules/cloudflare-tunnel/variables.tf` (complete implementation)
- `terraform/modules/cloudflare-tunnel/main.tf` (complete implementation)
- `terraform/modules/cloudflare-tunnel/outputs.tf` (complete implementation)
- `terraform/modules/cloudflare-tunnel/README.md` (documentation)
