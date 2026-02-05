# Development Environment Configuration
#
# This example demonstrates a development setup with:
# - Ephemeral state (no backend, state lives only in container)
# - Simple environment variable secrets
# - Test services for rapid iteration
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Replace with your Cloudflare zone
#   - your-account-id: Replace with your Cloudflare account ID
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# ============================================================================
# DEVICE DEFINITION: Development Server
# ============================================================================
#
# This is a simple development server with a single service for testing.
# In development, you typically work with:
#   - Test domains (dev.example.com)
#   - Non-production ports
#   - Rapid iteration without state persistence concerns
dev_server = unifi.UniFiEntity {
    friendly_hostname = "dev-server"
    domain = "internal.lan"
    unifi_site = "default"
    endpoints = [
        unifi.UniFiEndpoint {
            # REPLACE: Use your development device's MAC address
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
            query_unifi = True
        }
    ]
    services = [
        # Development web server - accessible both internally and externally
        unifi.Service {
            name = "dev-app"
            port = 8080
            protocol = "http"
            distribution = "both"
            internal_hostname = "dev-app.internal.lan"
            # REPLACE: Use your test domain (e.g., dev.example.com)
            public_hostname = "dev.example.com"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# Creates DNS records for internal access:
#   - dev-server.internal.lan (device hostname)
#   - dev-app.internal.lan (service CNAME)
unifi_config = unifi.UniFiConfig {
    devices = [dev_server]
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        # REPLACE: Your UniFi Controller hostname or IP
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
# Creates:
#   - Cloudflare Tunnel for external access
#   - DNS record for dev.example.com
cloudflare_config = cloudflare.CloudflareConfig {
    # REPLACE: Your Cloudflare zone name
    zone_name = "example.com"
    # REPLACE: Your Cloudflare account ID
    account_id = "your-account-id"
    # Allow self-signed certs in dev
    default_no_tls_verify = True
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "dev-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/dev-server.json"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "dev.example.com"
                    local_service_url = "http://dev-app.internal.lan:8080"
                    # Allow self-signed certs in dev
                    no_tls_verify = True
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
