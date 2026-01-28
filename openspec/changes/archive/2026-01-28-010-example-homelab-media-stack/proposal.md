# Proposal: Homelab Media Stack Example

## Change ID
010-example-homelab-media-stack

## Summary
Create a comprehensive, production-ready example configuration that demonstrates the complete unifi-cloudflare-glue workflow. This example showcases how to configure a homelab media stack with services distributed across UniFi-only (internal), Cloudflare-only (external), and dual-exposure (both providers) categories.

## Motivation
A complete working example is essential for users to understand the full workflow from KCL configuration to deployed infrastructure. The media stack use case is universally relatable in the homelab community and demonstrates all three service distribution patterns effectively.

## Goals

1. **Demonstrate Complete Workflow**: Show end-to-end process from KCL to Terraform
2. **Showcase All Distribution Patterns**: UniFi-only, Cloudflare-only, and Both
3. **Provide Copy-Paste Ready Configuration**: Users can adapt with minimal changes
4. **Document Best Practices**: Proper service categorization, naming conventions, MAC handling
5. **Enable Learning**: Clear documentation explaining why decisions were made

## Non-Goals

1. Actual application deployment (Docker, Kubernetes configs)
2. SSL certificate management beyond Cloudflare Tunnel
3. Authentication/authorization setup for services
4. Network-level security configuration (VLANs, firewall rules)

## Capabilities

### 1. Example Configuration (example-configuration)
Complete KCL configuration demonstrating the media stack with proper device, endpoint, and service definitions.

### 2. Documentation (documentation)
Comprehensive README with deployment workflow, customization guide, and troubleshooting.

### 3. Terraform Root Module (terraform-root-module)
Terraform configuration that consumes the KCL-generated JSON and applies to both UniFi and Cloudflare.

## Dependencies

- **007-kcl-integration-validation**: Generators must work correctly
- **008-terraform-unifi-dns-module**: UniFi DNS module must exist
- **009-terraform-cloudflare-tunnel-module**: Cloudflare Tunnel module must exist

## Success Criteria

- [ ] KCL configuration validates and generates JSON successfully
- [ ] All three service distribution types are represented
- [ ] Documentation explains deployment workflow clearly
- [ ] Placeholder values are clearly marked
- [ ] Example demonstrates MAC normalization
- [ ] Example shows proper local_service_url construction
- [ ] Terraform plan succeeds with generated JSON

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Provider version drift | Medium | Pin provider versions in example |
| Schema changes | Low | Lock to current schema version |
| User confusion about placeholders | Medium | Use consistent `<placeholder>` format |

## Related Changes

- 007-kcl-integration-validation
- 008-terraform-unifi-dns-module
- 009-terraform-cloudflare-tunnel-module
