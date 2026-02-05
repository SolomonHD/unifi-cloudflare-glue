# External-Only Services Example Configuration
#
# This example demonstrates services that are accessible ONLY via Cloudflare
# Tunnel. No internal DNS records are created for these services, meaning
# they can only be accessed through the Cloudflare edge network.
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Replace with your Cloudflare zone
#   - your-account-id: Replace with your Cloudflare account ID
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# ============================================================================
# DEVICE DEFINITION: Public Services Server
# ============================================================================
#
# This server hosts services that should only be accessible from the internet
# via Cloudflare Tunnel, not directly from the internal network.
public_server = unifi.UniFiEntity {
    friendly_hostname = "public-server"
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
        # SERVICE 1: Public Website
        # ============================================================================
        unifi.Service {
            name = "website"
            port = 80
            protocol = "http"
            distribution = "cloudflare_only"
            internal_hostname = "website.internal.lan"
            public_hostname = "www.example.com"
        }
        # ============================================================================
        # SERVICE 2: Customer API
        # ============================================================================
        unifi.Service {
            name = "api"
            port = 8080
            protocol = "https"
            distribution = "cloudflare_only"
            internal_hostname = "api.internal.lan"
            public_hostname = "api.example.com"
        }
        # ============================================================================
        # SERVICE 3: Customer Portal
        # ============================================================================
        unifi.Service {
            name = "portal"
            port = 3000
            protocol = "https"
            distribution = "cloudflare_only"
            internal_hostname = "portal.internal.lan"
            public_hostname = "portal.example.com"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION (Minimal)
# ============================================================================
#
# UniFi config only includes the device record for MAC-based discovery.
# No DNS records are created for cloudflare_only services.
unifi_config = unifi.UniFiConfig {
    devices = [public_server]
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
# All services are exposed through Cloudflare Tunnel.
# The tunnel routes public hostnames to internal URLs.
cloudflare_config = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "your-account-id"
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "public-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/public-server.json"
            services = [
                # Public website
                cloudflare.TunnelService {
                    public_hostname = "www.example.com"
                    local_service_url = "http://website.internal.lan:80"
                    no_tls_verify = False
                }
                # Customer API
                cloudflare.TunnelService {
                    public_hostname = "api.example.com"
                    local_service_url = "https://api.internal.lan:8080"
                    no_tls_verify = False
                }
                # Customer portal
                cloudflare.TunnelService {
                    public_hostname = "portal.example.com"
                    local_service_url = "https://portal.internal.lan:3000"
                    no_tls_verify = False
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
