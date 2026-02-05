# External-Only Services Example

An example demonstrating services that are accessible ONLY via Cloudflare Tunnel, with no direct internal DNS resolution.

## Overview

This example configures a server with three public-facing services:

| Service | Port | Public URL | Purpose |
|---------|------|------------|---------|
| Website | 80 | `www.example.com` | Public website |
| API | 8080 | `api.example.com` | Customer API |
| Portal | 3000 | `portal.example.com` | Customer portal |

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                           INTERNET                                 │
│                                                                    │
│   User Request: www.example.com                                    │
│         │                                                          │
│         ▼                                                          │
│   ┌──────────────────────────────────────┐                        │
│   │      Cloudflare Edge Network         │                        │
│   │  (DDoS Protection, WAF, Caching)    │                        │
│   └──────────────┬───────────────────────┘                        │
│                  │                                                 │
│                  │ Tunnel Connection                               │
│                  ▼                                                 │
│   ┌──────────────────────────────────────┐                        │
│   │      Cloudflare Tunnel               │                        │
│   │   (cloudflared daemon)               │                        │
│   └──────────────┬───────────────────────┘                        │
│                  │                                                 │
└──────────────────┼─────────────────────────────────────────────────┘
                   │
                   │ Internal Network
                   ▼
        ┌─────────────────────┐
        │   UniFi Router      │◄──── DNS resolution
        │   (DNS server)      │       for .internal.lan
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │    public-server    │
        │   (aa:bb:cc:..)     │
        │                     │
        │  ┌───────────────┐  │
        │  │   Website     │  │  http://website.internal.lan:80
        │  │    :80        │  │
        │  └───────────────┘  │
        │  ┌───────────────┐  │
        │  │     API       │  │  https://api.internal.lan:8080
        │  │   :8080       │  │
        │  └───────────────┘  │
        │  ┌───────────────┐  │
        │  │    Portal     │  │  https://portal.internal.lan:3000
        │  │   :3000       │  │
        │  └───────────────┘  │
        └─────────────────────┘
```

## DNS Resolution Flow

When a user accesses `www.example.com`:

1. **Public DNS** resolves `www.example.com` to Cloudflare edge
2. **Cloudflare** routes request through tunnel to your server
3. **Tunnel** (cloudflared) receives the request
4. **Internal DNS** (UniFi) resolves `website.internal.lan` to server IP
5. **Application** responds through the tunnel

```
User → www.example.com → Cloudflare Edge → Tunnel → website.internal.lan → Application
```

## Why External-Only?

### Use Cases

1. **Public-Facing Websites**
   - Company websites
   - Blogs and documentation
   - Marketing sites

2. **Customer APIs**
   - REST APIs for mobile apps
   - Webhook endpoints
   - Integration APIs

3. **Customer Portals**
   - Self-service portals
   - Account management
   - Support systems

4. **Cloudflare Security Benefits**
   - DDoS protection
   - Web Application Firewall (WAF)
   - Bot management
   - Access policies
   - Analytics

### Benefits of External-Only

| Benefit | Description |
|---------|-------------|
| **Cloudflare Security** | DDoS protection, WAF, bot filtering |
| **No Open Ports** | No firewall rules needed; tunnel is outbound-only |
| **Global CDN** | Cached content at 300+ locations worldwide |
| **Analytics** | Detailed traffic insights |

## Configuration

### Key Setting: `distribution = "cloudflare_only"`

```kcl
unifi.Service {
    name = "website"
    port = 80
    protocol = "http"
    distribution = "cloudflare_only"  # Key setting!
    internal_hostname = "website.internal.lan"
    public_hostname = "www.example.com"
}
```

This ensures:
- ❌ No internal DNS record in UniFi
- ✅ Cloudflare tunnel entry created
- ✅ Public DNS record in Cloudflare

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

**Expected output** (notice no service CNAMEs in UniFi):
```yaml
_unifi:
  devices:
    - friendly_hostname: public-server
      domain: internal.lan
      service_cnames: []  # Empty - no internal DNS!
      nics:
        - mac_address: aa:bb:cc:dd:ee:ff
_cloudflare:
  zone_name: example.com
  account_id: your-account-id
  tunnels:
    aa:bb:cc:dd:ee:ff:
      tunnel_name: public-server
      services:
        - public_hostname: www.example.com
          local_service_url: http://website.internal.lan:80
        - public_hostname: api.example.com
          local_service_url: https://api.internal.lan:8080
        - public_hostname: portal.example.com
          local_service_url: https://portal.internal.lan:3000
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

### 4. Start Cloudflared

On the server, start the cloudflared daemon:

```bash
# Using systemd
sudo systemctl start cloudflared

# Or manually
cloudflared tunnel run public-server
```

## Troubleshooting

### Service Unreachable Externally

**Symptom**: `www.example.com` returns error or timeout

**Checklist**:

1. **Cloudflared running?**
   ```bash
   sudo systemctl status cloudflared
   # or
   ps aux | grep cloudflared
   ```

2. **Tunnel credentials exist?**
   ```bash
   ls -la /etc/cloudflared/public-server.json
   ```

3. **Internal hostname resolves?**
   ```bash
   # On the server
   nslookup website.internal.lan
   # Should resolve to the server's IP
   ```

4. **Service running?**
   ```bash
   curl http://localhost:80
   ```

### DNS Resolution Issues

**Symptom**: Cloudflared logs show "no such host" errors

**Cause**: `local_service_url` hostname can't be resolved

**Fix**: Ensure UniFi DNS is working:
```bash
# Check DNS resolution on the server
nslookup website.internal.lan

# If failing, check:
# 1. UniFi Controller is reachable
# 2. DNS record exists in UniFi
# 3. Server uses UniFi as DNS server
```

### Certificate Errors

**Symptom**: HTTPS services show certificate errors

**Solutions**:

1. **Use valid certificates** (recommended)
   ```kcl
   # Configure your app with proper certs
   # Set no_tls_verify = False (default)
   ```

2. **Disable TLS verification** (development only)
   ```kcl
   TunnelService {
       public_hostname = "api.example.com"
       local_service_url = "https://api.internal.lan:8080"
       no_tls_verify = True  # Skip cert validation
   }
   ```

### Access from Internal Network

**Issue**: Internal users can't access `www.example.com`

**Options**:

1. **Use internal hostname** (recommended)
   - Internal: `http://website.internal.lan`
   - External: `https://www.example.com`

2. **Change to `distribution = "both"`**
   - Creates both internal and external DNS
   - See [single-service](../single-service/) example

3. **Use split-horizon DNS**
   - Configure UniFi to resolve `www.example.com` internally
   - Advanced configuration

### Tunnel Disconnected

**Symptom**: Services intermittently unavailable

**Check**:
```bash
# Check tunnel status
cloudflared tunnel info public-server

# Check logs
journalctl -u cloudflared -f

# Restart if needed
sudo systemctl restart cloudflared
```

## Common External-Only Services

| Service | Public Hostname | Use Case |
|---------|-----------------|----------|
| Website | `www.example.com` | Company website |
| API | `api.example.com` | Public API |
| Blog | `blog.example.com` | Content site |
| Docs | `docs.example.com` | Documentation |
| Portal | `app.example.com` | Customer portal |
| Status | `status.example.com` | Status page |
| Webhooks | `hooks.example.com` | Webhook receiver |

## Cloudflare Benefits

### Security Features

| Feature | Benefit |
|---------|---------|
| DDoS Protection | Mitigates large-scale attacks |
| WAF | Blocks SQL injection, XSS, etc. |
| Bot Management | Filters malicious bots |
| Rate Limiting | Prevents abuse |
| Access | Identity-based access control |

### Performance Features

| Feature | Benefit |
|---------|---------|
| CDN | Global content caching |
| Argo Smart Routing | Faster connections |
| Compression | Reduced bandwidth |
| HTTP/2 & HTTP/3 | Modern protocols |

## Next Steps

- **Add internal access**: See [single-service](../single-service/) for `distribution = "both"`
- **Internal-only services**: See [internal-only](../internal-only/)
- **Mixed setup**: See [multiple-services](../multiple-services/)
- **Full docs**: See [KCL Guide](../../docs/kcl-guide.md)