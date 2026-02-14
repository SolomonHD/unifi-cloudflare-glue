# Single Service Example Configuration
#
# This example demonstrates a simple setup with one device hosting a single
# service that is accessible both internally (via UniFi DNS) and externally
# (via Cloudflare Tunnel).
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Replace with your Cloudflare zone
#   - your-account-id: Replace with your Cloudflare account ID
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address

# Import schemas from the KCL module
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare

# ============================================================================
# DEVICE DEFINITION
# ============================================================================
#
# Define a single device with one service. The device has:
#   - A friendly hostname for DNS
#   - An internal domain for local DNS
#   - One network interface (MAC address)
#   - One service (Jellyfin media server)
media_server = unifi.UniFiEntity {
    friendly_hostname = "media-server"
    domain = "internal.lan"
    unifi_site = "default"
    # Network interfaces on this device
    endpoints = [
        unifi.UniFiEndpoint {
            # REPLACE: Use your device's MAC address
            # Acceptable formats: aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, aabbccddeeff
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
            query_unifi = True
        }
    ]
    # Services running on this device
    services = [
        # Jellyfin media server - accessible both internally and externally
        unifi.Service {
            name = "jellyfin"
            port = 8096
            protocol = "http"
            # "both" means this service gets:
            #   - Internal DNS record (via UniFi)
            #   - External DNS record (via Cloudflare Tunnel)
            distribution = "both"
            # Internal DNS name - used for local access
            internal_hostname = "jellyfin.internal.lan"
            # Public DNS name - used for external access
            # REPLACE: Use your actual domain
            public_hostname = "media.example.com"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# This configuration is consumed by the unifi-dns Terraform module.
# It creates DNS records for:
#   - Device hostname (media-server.internal.lan)
#   - Service internal_hostname (jellyfin.internal.lan)
unifi_config = unifi.UniFiConfig {
    devices = [media_server]
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
# This configuration is consumed by the cloudflare-tunnel Terraform module.
# It creates:
#   - A Cloudflare Tunnel for the device
#   - DNS records for the tunnel
#   - Ingress rules mapping public_hostnames to local_service_urls
cloudflare_config = cloudflare.CloudflareConfig {
    # REPLACE: Your Cloudflare zone name
    zone_name = "example.com"
    # REPLACE: Your Cloudflare account ID (found in Cloudflare dashboard)
    account_id = "your-account-id"
    default_no_tls_verify = False
    # Tunnels are keyed by MAC address
    # Each physical device gets exactly one tunnel
    tunnels = {
        # REPLACE: Use the same MAC address as in the UniFi device
        "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/media-server.json"
            # Services are filtered to include only:
            #   - distribution = "cloudflare_only"
            #   - distribution = "both"
            # (unifi_only services are excluded from tunnel config)
            services = [
                cloudflare.TunnelService {
                    # Public hostname users will access
                    public_hostname = "media.example.com"
                    # Internal URL where the service is accessible
                    # Can use any valid domain (internal .internal.lan, .local, .home or public like .com)
                    local_service_url = "http://jellyfin.internal.lan:8096"
                    no_tls_verify = False
                }
            ]
        }
    }
}

# ============================================================================
# OUTPUT
# ============================================================================
#
# This combines both configurations into a single output object.
# When you run: kcl run main.k
# The output contains both UniFi and Cloudflare configurations.
{
    _unifi = unifi_config
    _cloudflare = cloudflare_config
}
