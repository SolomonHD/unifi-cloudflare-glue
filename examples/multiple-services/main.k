# Multiple Services Example Configuration
#
# This example demonstrates a device hosting multiple services with different
# distribution strategies - some internal-only, some external-only, and some
# accessible from both locations.
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Replace with your Cloudflare zone
#   - your-account-id: Replace with your Cloudflare account ID
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# ============================================================================
# DEVICE DEFINITION: Home Server with Multiple Services
# ============================================================================
#
# This server hosts:
#   - Internal-only: Admin panel, monitoring
#   - External-only: Public API
#   - Both: Media server (Jellyfin)
home_server = unifi.UniFiEntity {
    friendly_hostname = "home-server"
    domain = "internal.lan"
    unifi_site = "default"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
            query_unifi = True
        }
    ]
    services = [
        # ============================================================================
        # SERVICE 1: Internal-Only (Admin Panel)
        # ============================================================================
        # Only accessible within the local network
        unifi.Service {
            name = "admin"
            port = 8080
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "admin.internal.lan"
        }
        # ============================================================================
        # SERVICE 2: Internal-Only (Monitoring)
        # ============================================================================
        unifi.Service {
            name = "prometheus"
            port = 9090
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "metrics.internal.lan"
        }
        # ============================================================================
        # SERVICE 3: External-Only (Public API)
        # ============================================================================
        # Only accessible via Cloudflare Tunnel
        unifi.Service {
            name = "api"
            port = 3000
            protocol = "https"
            distribution = "cloudflare_only"
            internal_hostname = "api.internal.lan"
            public_hostname = "api.example.com"
        }
        # ============================================================================
        # SERVICE 4: Both (Media Server)
        # ============================================================================
        # Accessible internally (direct) and externally (via Cloudflare)
        unifi.Service {
            name = "jellyfin"
            port = 8096
            protocol = "http"
            distribution = "both"
            internal_hostname = "jellyfin.internal.lan"
            public_hostname = "media.example.com"
        }
        # ============================================================================
        # SERVICE 5: Both (Media Requests)
        # ============================================================================
        unifi.Service {
            name = "requests"
            port = 5055
            protocol = "http"
            distribution = "both"
            internal_hostname = "requests.internal.lan"
            public_hostname = "requests.example.com"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# Creates DNS records for:
#   - unifi_only services: admin.internal.lan, metrics.internal.lan
#   - both services: jellyfin.internal.lan, requests.internal.lan
unifi_config = unifi.UniFiConfig {
    devices = [home_server]
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
        port = 443
        username_ref = "UNIFI_USERNAME"
        password_ref = "UNIFI_PASSWORD"
        site = "default"
    }
}

# ============================================================================
# CLOUDFLARE CONFIGURATION
# ============================================================================
#
# Creates tunnel ingress rules for:
#   - cloudflare_only services: api.example.com
#   - both services: media.example.com, requests.example.com
cloudflare_config = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "your-account-id"
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "home-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/home-server.json"
            services = [
                # External-only: API
                cloudflare.TunnelService {
                    public_hostname = "api.example.com"
                    local_service_url = "https://api.internal.lan:3000"
                    no_tls_verify = False
                }
                # Both: Media server
                cloudflare.TunnelService {
                    public_hostname = "media.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
                # Both: Media requests
                cloudflare.TunnelService {
                    public_hostname = "requests.example.com"
                    local_service_url = "http://requests.internal.lan:5055"
                }
            ]
        }
    }
}

# ============================================================================
# OUTPUT
# ============================================================================
{
    _unifi = unifi_config
    _cloudflare = cloudflare_config
}
