# Internal-Only Services Example

An example demonstrating services that are accessible ONLY within the local network, with no external exposure via Cloudflare.

## Overview

This example configures a server with four internal management tools:

| Service | Port | Purpose |
|---------|------|---------|
| Prometheus | 9090 | Metrics collection and alerting |
| Grafana | 3000 | Metrics visualization dashboards |
| Portainer | 9000 | Docker container management |
| UniFi Controller | 8443 | Network management (alternative access) |

## Security Boundary

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                            │
│                                                             │
│    No Cloudflare Tunnel    ❌ NO ACCESS ❌                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Firewall blocks external access
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    LOCAL NETWORK                            │
│                                                             │
│   ┌──────────────┐                                         │
│   │ UniFi Router │◄──── DNS resolution                     │
│   └──────┬───────┘                                         │
│          │                                                  │
│          ▼                                                  │
│   ┌─────────────────┐                                       │
│   │  internal-tools │                                       │
│   │  (aa:bb:cc:..)  │                                       │
│   │                 │                                       │
│   │  ┌───────────┐  │                                       │
│   │  │Prometheus │  │  http://metrics.internal.lan:9090    │
│   │  │  :9090    │  │                                       │
│   │  └───────────┘  │                                       │
│   │  ┌───────────┐  │                                       │
│   │  │  Grafana  │  │  http://dashboards.internal.lan:3000 │
│   │  │  :3000    │  │                                       │
│   │  └───────────┘  │                                       │
│   │  ┌───────────┐  │                                       │
│   │  │ Portainer │  │  https://docker.internal.lan:9000    │
│   │  │  :9000    │  │                                       │
│   │  └───────────┘  │                                       │
│   └─────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Why Internal-Only?

### Use Cases

1. **Management Interfaces Without Strong Auth**
   - Portainer, database admin tools
   - Internal dashboards
   - Configuration UIs

2. **Monitoring and Observability**
   - Prometheus metrics
   - Grafana dashboards
   - Log aggregation (Loki, ELK)

3. **Internal APIs and Services**
   - Microservice communication
   - Internal tooling APIs
   - Backend services

4. **Development and Staging**
   - Test environments
   - Development tools
   - CI/CD infrastructure

### Security Benefits

| Benefit | Description |
|---------|-------------|
| **No Attack Surface** | Services unreachable from internet |
| **No Public DNS** | No DNS entries pointing to your infrastructure |
| **Network Boundary** | Physical network separation |
| **Simpler Auth** | Can use simpler auth within trusted network |

## Configuration

### Key Setting: `distribution = "unifi_only"`

```kcl
unifi.Service {
    name = "prometheus"
    port = 9090
    protocol = "http"
    distribution = "unifi_only"  # Key setting!
    internal_hostname = "metrics.internal.lan"
}
```

This ensures:
- ✅ DNS record created in UniFi
- ❌ No Cloudflare tunnel entry
- ❌ No public DNS record

## Quick Start

### 1. Customize

Edit `main.k` and replace:
- MAC address (`aa:bb:cc:dd:ee:ff`)
- UniFi Controller host (`unifi.internal.lan`)

### 2. Validate

```bash
kcl run main.k
```

**Expected output** (notice no `_cloudflare` section):
```yaml
_unifi:
  devices:
    - friendly_hostname: internal-tools
      domain: internal.lan
      service_cnames:
        - metrics.internal.lan
        - dashboards.internal.lan
        - docker.internal.lan
        - unifi-mgmt.internal.lan
      nics:
        - mac_address: aa:bb:cc:dd:ee:ff
          nic_name: eth0
  default_domain: internal.lan
```

### 3. Deploy

```bash
dagger call -m github.com/SolomonHD/unifi-cloudflare-glue@v0.3.2 deploy-unifi \
    --source=. \
    --unifi-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY
```

**Note**: Use `deploy-unifi` (not `deploy`) since we only need UniFi DNS.

## Verification Steps

### 1. Check No Cloudflare Configuration

```bash
kcl run main.k | grep -c "_cloudflare"
# Expected: 0 (or no output)
```

### 2. Verify UniFi DNS Records

After deployment, check UniFi Controller:

1. Log into UniFi Controller
2. Go to Settings → Networks → DNS
3. Verify these records exist:
   - `metrics.internal.lan`
   - `dashboards.internal.lan`
   - `docker.internal.lan`
   - `unifi-mgmt.internal.lan`

### 3. Test Internal Resolution

From a device on your network:

```bash
# Test DNS resolution
nslookup metrics.internal.lan
# Should resolve to internal-tools server IP

# Test service access
curl http://metrics.internal.lan:9090
# Should return Prometheus UI
```

### 4. Verify No External Access

From outside your network (e.g., mobile on cellular):

```bash
# These should NOT resolve
nslookup metrics.internal.lan
nslookup metrics.your-public-domain.com
```

## Common Internal-Only Services

| Service | Port | Description |
|---------|------|-------------|
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |
| Portainer | 9000 | Docker management |
| pgAdmin | 5050 | PostgreSQL admin |
| phpMyAdmin | 8080 | MySQL admin |
| Redis Commander | 8081 | Redis management |
| Jenkins | 8080 | CI/CD server |
| GitLab | 80/443 | Code repository |

## Adding a Service

To add another internal-only service:

```kcl
services = [
    # ... existing services ...
    
    unifi.Service {
        name = "new-tool"
        port = 8080
        protocol = "http"
        distribution = "unifi_only"  # Always unifi_only for internal
        internal_hostname = "new-tool.internal.lan"
    }
]
```

## Troubleshooting

### Service Not Resolving

1. Check UniFi DNS is configured as your network's DNS server
2. Verify the service is running: `curl http://localhost:PORT`
3. Check UniFi Controller DNS settings

### Accidental External Exposure

If you accidentally set `distribution = "both"` or `"cloudflare_only"`:

1. Change back to `unifi_only`
2. Remove any `TunnelService` entries
3. Re-run deployment
4. Verify in Cloudflare dashboard that DNS records are removed

### Mixed Configuration

If some services should be internal and others external:

```kcl
services = [
    # Internal-only
    unifi.Service {
        name = "admin"
        distribution = "unifi_only"
        ...
    }
    
    # External access needed
    unifi.Service {
        name = "public-api"
        distribution = "cloudflare_only"  # or "both"
        ...
    }
]
```

See [multiple-services](../multiple-services/) for mixed configurations.

## Next Steps

- **Add external access**: See [external-only](../external-only/)
- **Mixed setup**: See [multiple-services](../multiple-services/)
- **Simple single service**: See [single-service](../single-service/)
- **Full docs**: See [KCL Guide](../../docs/kcl-guide.md)