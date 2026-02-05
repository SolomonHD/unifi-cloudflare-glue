# Staging Environment Configuration
#
# This example demonstrates a staging setup with:
# - S3 backend with native lockfile for state persistence
# - Team collaboration support through shared state
# - Staging-appropriate services for pre-production testing
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Replace with your Cloudflare zone
#   - your-account-id: Replace with your Cloudflare account ID
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# ============================================================================
# DEVICE DEFINITION: Staging Server
# ============================================================================
#
# This is a staging server with multiple services for pre-production testing.
# Staging typically mirrors production but with:
#   - Staging-specific domains (staging.example.com)
#   - Reduced resource configurations
#   - Test data and configurations
staging_server = unifi.UniFiEntity {
    friendly_hostname = "staging-server"
    domain = "internal.lan"
    unifi_site = "default"
    endpoints = [
        unifi.UniFiEndpoint {
            # REPLACE: Use your staging device's MAC address
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
            query_unifi = True
        }
    ]
    services = [
        # Staging web application - accessible both internally and externally
        unifi.Service {
            name = "staging-app"
            port = 8080
            protocol = "http"
            distribution = "both"
            internal_hostname = "staging-app.internal.lan"
            # REPLACE: Use your staging domain (e.g., staging.example.com)
            public_hostname = "staging.example.com"
        }
        # Staging API - external access for integration testing
        unifi.Service {
            name = "staging-api"
            port = 3000
            protocol = "http"
            distribution = "cloudflare_only"
            internal_hostname = "staging-api.internal.lan"
            # REPLACE: Use your staging API domain
            public_hostname = "api-staging.example.com"
        }
        # Staging admin panel - internal only for security
        unifi.Service {
            name = "staging-admin"
            port = 8081
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "staging-admin.internal.lan"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# Creates DNS records for internal access:
#   - staging-server.internal.lan (device hostname)
#   - staging-app.internal.lan (service CNAME)
#   - staging-api.internal.lan (service CNAME)
#   - staging-admin.internal.lan (service CNAME)
unifi_config = unifi.UniFiConfig {
    devices = [staging_server]
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
#   - DNS records for staging.example.com and api-staging.example.com
cloudflare_config = cloudflare.CloudflareConfig {
    # REPLACE: Your Cloudflare zone name
    zone_name = "example.com"
    # REPLACE: Your Cloudflare account ID
    account_id = "your-account-id"
    # Require valid certificates in staging
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "staging-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/staging-server.json"
            services = [
                # Staging web application
                cloudflare.TunnelService {
                    public_hostname = "staging.example.com"
                    local_service_url = "http://staging-app.internal.lan:8080"
                    no_tls_verify = False
                }
                # Staging API
                cloudflare.TunnelService {
                    public_hostname = "api-staging.example.com"
                    local_service_url = "http://staging-api.internal.lan:3000"
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
