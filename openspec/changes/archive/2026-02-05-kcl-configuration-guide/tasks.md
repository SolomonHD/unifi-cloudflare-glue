## 1. Create Main KCL Guide

- [x] 1.1 Create `docs/kcl-guide.md` with complete file structure (headers, TOC)
- [x] 1.2 Write Overview section explaining KCL purpose and benefits
- [x] 1.3 Document all base schemas (Entity, Endpoint, Service, MACAddress, Hostname, Distribution) with field descriptions and types
- [x] 1.4 Document UniFi schemas (UniFiConfig, UniFiEntity, UniFiEndpoint, UniFiController) with examples
- [x] 1.5 Document Cloudflare schemas (CloudflareConfig, CloudflareTunnel, TunnelService) with examples
- [x] 1.6 Add schema field examples showing valid and invalid values for each field type

## 2. Document Validation Rules

- [x] 2.1 Explain MAC address validation (accepted formats, normalization, rationale)
- [x] 2.2 Explain hostname validation (RFC 1123 constraints, character rules, length limits)
- [x] 2.3 Explain DNS loop prevention (internal domain requirements, rationale, error fixes)
- [x] 2.4 Explain one tunnel per device constraint (enforcement, rationale, multiple service handling)
- [x] 2.5 Explain port range validation (valid range, reserved ports, common examples)
- [x] 2.6 Explain cross-provider MAC consistency validation (requirement, error interpretation)

## 3. Add Configuration Patterns

- [x] 3.1 Document single service per device pattern with complete example
- [x] 3.2 Document multiple services per device pattern with varied distributions
- [x] 3.3 Document internal-only services pattern with use cases
- [x] 3.4 Document external-only services pattern with routing explanation
- [x] 3.5 Document mixed distribution device pattern (internal + external services)
- [x] 3.6 Document multi-NIC device pattern with service-to-interface mapping

## 4. Create Debugging Guide

- [x] 4.1 Add syntax error diagnosis section with line number interpretation
- [x] 4.2 Add type error diagnosis section with common type mismatches
- [x] 4.3 Add validation error diagnosis section with check block failure interpretation
- [x] 4.4 Add generator error diagnosis section with output validation
- [x] 4.5 Create common mistakes reference table with symptoms and solutions
- [x] 4.6 Add step-by-step debugging workflow (syntax → types → validation → generation)

## 5. Create Testing Section

- [x] 5.1 Add validation commands section (kcl run syntax checks)
- [x] 5.2 Add generator testing commands (UniFi and Cloudflare JSON generation)
- [x] 5.3 Add output verification techniques
- [x] 5.4 Link to debugging guide sections for specific error types

## 6. Create Single Service Example

- [x] 6.1 Create `examples/single-service/` directory
- [x] 6.2 Write `examples/single-service/main.k` with complete working configuration
- [x] 6.3 Create `examples/single-service/README.md` explaining example and customization
- [x] 6.4 Add validation commands to README with expected output
- [x] 6.5 Test example validates successfully with `kcl run main.k`

## 7. Create Multiple Services Example

- [x] 7.1 Create `examples/multiple-services/` directory
- [x] 7.2 Write `examples/multiple-services/main.k` with 3+ services using varied distributions
- [x] 7.3 Create `examples/multiple-services/README.md` with service organization guidance
- [x] 7.4 Add customization instructions for adding/removing services
- [x] 7.5 Test example validates successfully

## 8. Create Internal-Only Example

- [x] 8.1 Create `examples/internal-only/` directory
- [x] 8.2 Write `examples/internal-only/main.k` with unifi_only distribution services
- [x] 8.3 Create `examples/internal-only/README.md` explaining security boundary and use cases
- [x] 8.4 Add verification steps showing no Cloudflare tunnel generation
- [x] 8.5 Test example validates successfully

## 9. Create External-Only Example

- [x] 9.1 Create `examples/external-only/` directory
- [x] 9.2 Write `examples/external-only/main.k` with cloudflare_only distribution services
- [x] 9.3 Create `examples/external-only/README.md` explaining routing and DNS resolution
- [x] 9.4 Add troubleshooting section for external access
- [x] 9.5 Test example validates successfully

## 10. Add Cross-References and Links

- [x] 10.1 Update main `README.md` with link to KCL guide in documentation section
- [x] 10.2 Update `docs/README.md` index with KCL guide entry
- [x] 10.3 Update `kcl/README.md` with prominent link to docs/kcl-guide.md
- [x] 10.4 Add examples section to kcl-guide.md with links to all example directories
- [x] 10.5 Add "See also" sections in kcl-guide.md linking between related sections

## 11. Validation and Polish

- [x] 11.1 Verify all KCL examples validate successfully with `kcl run`
- [x] 11.2 Test all generator commands in examples produce valid JSON output
- [x] 11.3 Verify all cross-links work correctly (no broken references)
- [x] 11.4 Proofread documentation for clarity and completeness
- [x] 11.5 Ensure consistent terminology throughout documentation
- [x] 11.6 Verify all code blocks have correct syntax highlighting language tags
