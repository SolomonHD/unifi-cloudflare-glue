# Multiple Services Example

An example demonstrating a device hosting multiple services with different exposure patterns - internal-only, external-only, and dual exposure.

## Overview

This example configures a home server with five services:

| Service | Port | Distribution | Access |
|---------|------|--------------|--------|
| Admin Panel | 8080 | `unifi_only` | Internal network only |
| Prometheus | 9090 | `unifi_only` | Internal network only |
| Public API | 3000 | `cloudflare_only` | Internet only (via Cloudflare) |
| Jellyfin | 8096 | `both` | Internal + Internet |
| Media Requests | 5055 | `both` | Internal + Internet |

## Architecture

```
                    ┌─────────────────┐
                    │   home-server   │
                    │ (aa:bb:cc:..)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   Internal-Only       External-Only          Both
        │                    │                    │
   ┌────────┐          ┌──────────┐      ┌──────────────┐
   │  UniFi │          │Cloudflare│      │  UniFi + CF  │
   │  DNS   │          │  Tunnel  │      │              │
   └────────┘          └──────────┘      └──────────────┘
        │                    │                    │
   admin.             api.example.com    jellyfin.
   internal.lan       (public)           internal.lan
   metrics.                              media.example.com
   internal.lan                          (public)
```

## Service Organization Strategy

When hosting multiple services on one device, consider these patterns:

### Security Zones

1. **Internal-Only (`unifi_only`)**
   - Admin interfaces without strong authentication
   - Monitoring tools (Prometheus, Grafana)
   - Internal APIs and databases
   - Development/staging services

2. **External-Only (`cloudflare_only`)**
   - Public APIs with Cloudflare security
   - Customer-facing services
   - Webhooks requiring public endpoints

3. **Both (`both`)**
   - Media servers (bandwidth-efficient local access)
   - Services used from home and away
   - Anything needing both direct and tunneled access

## Quick Start

### 1. Customize

Edit `main.k` and replace:
- MAC address (`aa:bb:cc:dd:ee:ff`)
- Cloudflare zone (`example.com`)
- Cloudflare account ID (`your-account-id`)
- UniFi Controller host (`unifi.internal.lan`)

### 2. Validate

```bash
kcl run main.k
```

### 3. Deploy

```bash
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.3.2 deploy \
    --kcl-source=. \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=your-account-id \
    --zone-name=example.com
```

## Adding a Service

To add a new service to the configuration:

```kcl
# In the services list, add:
unifi.Service {
    name = "new-service"
    port = 8080
    protocol = "http"  # or "https" or "tcp"
    
    # Choose distribution based on access needs:
    distribution = "unifi_only"      # Internal only
    # distribution = "cloudflare_only"  # External only
    # distribution = "both"             # Both
    
    internal_hostname = "new-service.internal.lan"
    
    # Only for cloudflare_only or both:
    public_hostname = "new-service.example.com"
}
```

Then add the corresponding `TunnelService` if using Cloudflare:

```kcl
# In the tunnel services list:
cloudflare.TunnelService {
    public_hostname = "new-service.example.com"
    local_service_url = "http://new-service.internal.lan:8080"
}
```

## Removing a Service

1. Remove the `Service` from the `services` list
2. Remove the corresponding `TunnelService` (if applicable)

## Verifying Service Distribution

After running `kcl run main.k`, verify:

**UniFi services** (should include `unifi_only` + `both`):
```yaml
_unifi:
  devices:
    - services:  # These become UniFi DNS records
        - admin.internal.lan      # unifi_only
        - metrics.internal.lan    # unifi_only
        - jellyfin.internal.lan   # both
        - requests.internal.lan   # both
```

**Cloudflare services** (should include `cloudflare_only` + `both`):
```yaml
_cloudflare:
  tunnels:
    services:  # These become tunnel ingress rules
      - api.example.com         # cloudflare_only
      - media.example.com       # both
      - requests.example.com    # both
```

## Common Patterns

### Admin Separation

Keep admin interfaces internal-only for security:

```kcl
# Admin panel - never exposed externally
unifi.Service {
    name = "admin"
    port = 8080
    protocol = "https"
    distribution = "unifi_only"
    internal_hostname = "admin.internal.lan"
}
```

### Public API with Internal Fallback

Services that need both public and internal access:

```kcl
unifi.Service {
    name = "api"
    port = 3000
    protocol = "https"
    distribution = "both"
    internal_hostname = "api.internal.lan"
    public_hostname = "api.example.com"
}
```

Internal clients use `https://api.internal.lan:3000` (direct)
External clients use `https://api.example.com` (via Cloudflare)

### Database + Application

Database internal-only, application external:

```kcl
# Database - no external access
unifi.Service {
    name = "postgres"
    port = 5432
    protocol = "tcp"
    distribution = "unifi_only"
    internal_hostname = "db.internal.lan"
}

# Application - external access
unifi.Service {
    name = "app"
    port = 8080
    protocol = "https"
    distribution = "cloudflare_only"
    internal_hostname = "app.internal.lan"
    public_hostname = "app.example.com"
}
```

## Troubleshooting

### Service Not Appearing in UniFi

- Check `distribution` is `unifi_only` or `both`
- Verify `internal_hostname` is set

### Service Not Appearing in Cloudflare

- Check `distribution` is `cloudflare_only` or `both`
- Verify `public_hostname` is set
- Check that `TunnelService` exists in the tunnel

### Port Conflicts

Each service needs a unique port:

```kcl
# Good - different ports
Service { name = "app1", port = 8080, ... }
Service { name = "app2", port = 8081, ... }

# Bad - same port
Service { name = "app1", port = 8080, ... }
Service { name = "app2", port = 8080, ... }  # Conflict!
```

## Next Steps

- **Simpler setup**: See [single-service](../single-service/)
- **Internal-only**: See [internal-only](../internal-only/)
- **External-only**: See [external-only](../external-only/)
- **Full docs**: See [KCL Guide](../../docs/kcl-guide.md)