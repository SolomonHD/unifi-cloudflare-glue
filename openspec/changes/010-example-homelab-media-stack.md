# OpenSpec Prompt: Homelab Media Stack Example

## Context

A complete working example demonstrates the entire workflow from KCL configuration to deployed infrastructure. The homelab media stack example includes popular self-hosted media applications with appropriate service categorization.

## Goal

Create a comprehensive example configuration that demonstrates:
- UniFi-only services (*arr stack for internal use)
- Cloudflare-only services (external applications)
- Both providers (media streaming services)
- Complete end-to-end workflow

## Scope

### In Scope
- Complete KCL configuration for media server with multiple services
- UniFi DNS for internal services (Sonarr, Radarr, Prowlarr)
- Cloudflare Tunnel for external services (Paperless-ngx, Immich)
- Both providers for dual-exposure services (Jellyfin, Jellyseerr)
- Documentation explaining the configuration
- README with deployment workflow

### Out of Scope
- Actual application deployment (just DNS/Tunnel)
- Docker Compose configurations
- SSL certificate management beyond tunnel

## Desired Behavior

1. **Example Structure**:
   ```
   examples/homelab-media-stack/
   ├── README.md
   ├── main.k                    # KCL configuration
   ├── outputs/                  # Generated JSON (gitignored)
   │   ├── unifi.json
   │   └── cloudflare.json
   └── terraform/                # Terraform root module
       ├── main.tf
       ├── variables.tf
       └── README.md
   ```

2. **Device Configuration**:
   - Single media server device
   - Two NICs: management (1GbE) and media (10GbE)
   - MAC addresses for both NICs
   - friendly_hostname: "media-server"

3. **Services by Distribution**:

   **UniFi-only (Internal)**:
   - Sonarr (TV management): sonarr.internal.lan
   - Radarr (Movie management): radarr.internal.lan  
   - Prowlarr (Indexer management): prowlarr.internal.lan

   **Cloudflare-only (External)**:
   - Paperless-ngx (Document management): docs.example.com
   - Immich (Photo management): photos.example.com

   **Both (Internal + External)**:
   - Jellyfin (Media server): jellyfin.internal.lan + media.example.com
   - Jellyseerr (Request management): requests.internal.lan + requests.example.com

4. **Documentation**:
   - How to customize for your environment
   - Step-by-step deployment workflow
   - How to add new services
   - Troubleshooting common issues

## Constraints & Assumptions

1. **Replaceable Values**: Use placeholders for domain, account_id, MACs
2. **Working Example**: Configuration should be valid and deployable after customization
3. **Best Practices**: Demonstrate proper service categorization
4. **Documentation**: Comprehensive README with all steps

## Acceptance Criteria

- [ ] `examples/homelab-media-stack/main.k` contains complete KCL configuration
- [ ] Example includes services for all three distribution types
- [ ] `examples/homelab-media-stack/README.md` explains the setup
- [ ] Terraform root module references both provider modules
- [ ] All placeholder values clearly marked (e.g., `<your-domain>`)
- [ ] Documentation includes deployment workflow:
   1. Customize KCL configuration
   2. Run KCL to generate JSON
   3. Apply UniFi module first
   4. Apply Cloudflare module
   5. Configure cloudflared with tokens
- [ ] Example demonstrates MAC normalization
- [ ] Example shows proper local_service_url construction

## Dependencies

- **Depends On**: 007-kcl-integration-validation (generators must work)
- **Depends On**: 008-terraform-unifi-dns-module (module must exist)
- **Depends On**: 009-terraform-cloudflare-tunnel-module (module must exist)

## Expected Files/Areas Touched

- `examples/homelab-media-stack/main.k` (new)
- `examples/homelab-media-stack/README.md` (new)
- `examples/homelab-media-stack/terraform/main.tf` (new)
- `examples/homelab-media-stack/terraform/variables.tf` (new)
- `examples/homelab-media-stack/terraform/README.md` (new)
