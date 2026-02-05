# Production Environment Configuration
#
# This example demonstrates a production setup with:
# - S3 backend with DynamoDB locking for state management
# - vals integration for secure secret injection
# - Production-grade security practices
# - Full TLS verification and valid certificates
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Replace with your Cloudflare zone
#   - your-account-id: Replace with your Cloudflare account ID
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# ============================================================================
# DEVICE DEFINITION: Production Server
# ============================================================================
#
# This is a production server with multiple services for real workloads.
# Production configuration requires:
#   - Valid TLS certificates (no self-signed)
#   - Production domains (app.example.com)
#   - Full security hardening
production_server = unifi.UniFiEntity {
    friendly_hostname = "prod-server"
    domain = "internal.lan"
    unifi_site = "default"
    endpoints = [
        unifi.UniFiEndpoint {
            # REPLACE: Use your production device's MAC address
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
            query_unifi = True
        }
    ]
    services = [
        # Production web application - accessible both internally and externally
        unifi.Service {
            name = "production-app"
            port = 443
            protocol = "https"
            distribution = "both"
            internal_hostname = "production-app.internal.lan"
            # REPLACE: Use your production domain (e.g., app.example.com)
            public_hostname = "app.example.com"
        }
        # Production API - external access for clients
        unifi.Service {
            name = "production-api"
            port = 443
            protocol = "https"
            distribution = "cloudflare_only"
            internal_hostname = "production-api.internal.lan"
            # REPLACE: Use your production API domain
            public_hostname = "api.example.com"
        }
        # Production admin panel - internal only for security
        unifi.Service {
            name = "production-admin"
            port = 443
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "production-admin.internal.lan"
        }
        # Internal monitoring - internal only
        unifi.Service {
            name = "monitoring"
            port = 3000
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "monitoring.internal.lan"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# Creates DNS records for internal access:
#   - prod-server.internal.lan (device hostname)
#   - production-app.internal.lan (service CNAME)
#   - production-api.internal.lan (service CNAME)
#   - production-admin.internal.lan (service CNAME)
#   - monitoring.internal.lan (service CNAME)
unifi_config = unifi.UniFiConfig {
    devices = [production_server]
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
#   - DNS records for app.example.com and api.example.com
#   - Full TLS verification (no self-signed certificates)
cloudflare_config = cloudflare.CloudflareConfig {
    # REPLACE: Your Cloudflare zone name
    zone_name = "example.com"
    # REPLACE: Your Cloudflare account ID
    account_id = "your-account-id"
    # Require valid certificates in production
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "production-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/production-server.json"
            services = [
                # Production web application
                cloudflare.TunnelService {
                    public_hostname = "app.example.com"
                    local_service_url = "https://production-app.internal.lan:443"
                    no_tls_verify = False
                }
                # Production API
                cloudflare.TunnelService {
                    public_hostname = "api.example.com"
                    local_service_url = "https://production-api.internal.lan:443"
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
