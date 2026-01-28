# Homelab Media Stack Example Configuration
#
# This example demonstrates a complete homelab media server setup with services
# distributed across three exposure patterns:
#   - UniFi-only: Internal automation services (*arr stack)
#   - Cloudflare-only: External document and photo management
#   - Both: Media streaming with internal and external access
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - example.com: Your Cloudflare zone (replace with your actual domain)
#   - a1b2c3d4e5f6789012345678901234ab: Your Cloudflare account ID
#   - aa:bb:cc:dd:ee:01: MAC address of your server's management NIC
#   - aa:bb:cc:dd:ee:02: MAC address of your server's media/10GbE NIC (optional)
#
# See README.md for detailed setup instructions.

# Import schemas from parent module
import unifi_cloudflare_glue.schemas.unifi
import unifi_cloudflare_glue.schemas.cloudflare
import unifi_cloudflare_glue.generators.unifi as unifi_gen
import unifi_cloudflare_glue.generators.cloudflare as cf_gen

# ============================================================================
# ENTITY DEFINITION: Media Server
# ============================================================================
#
# This media server has dual NICs:
#   1. Management NIC (1GbE): For admin access, SSH, internal services
#   2. Media NIC (10GbE): For high-bandwidth media streaming
#
# MAC Address Handling:
#   - Acceptable formats: "aa:bb:cc:dd:ee:ff", "aa-bb-cc-dd-ee-ff", "aabbccddeeff"
#   - All formats are automatically normalized to lowercase colon format
#   - MAC addresses are used as dictionary keys for tunnel mapping

media_server = unifi.UniFiEntity {
    friendly_hostname = "media-server"
    domain = "internal.lan"
    unifi_site = "default"

    # Endpoints (network interfaces)
    endpoints = [
        # Management NIC - for SSH, admin panels, internal-only services
        unifi.UniFiEndpoint {
            # REPLACE: aa:bb:cc:dd:ee:01 with your management NIC MAC address
            # Example formats accepted: "aa:bb:cc:dd:ee:ff", "aa-bb-cc-dd-ee-ff", "aabbccddeeff"
            mac_address = "aa:bb:cc:dd:ee:01"
            nic_name = "eth0"
            service_cnames = [
                "admin.internal.lan",
                "ssh.internal.lan",
            ]
            query_unifi = True
        },
        # Media NIC (10GbE) - for high-bandwidth media streaming
        unifi.UniFiEndpoint {
            # REPLACE: aa:bb:cc:dd:ee:02 with your media/10GbE NIC MAC address
            mac_address = "aa:bb:cc:dd:ee:02"
            nic_name = "eth1-10gbe"
            service_cnames = [
                "media.internal.lan",
            ]
            query_unifi = True
        },
    ]

    # ============================================================================
    # SERVICES: UniFi-Only (Internal Automation Stack)
    # ============================================================================
    #
    # These services are ONLY accessible within your internal network.
    # They have no public_hostname defined and use distribution = "unifi_only".
    #
    # Why UniFi-only?
    #   - These are automation tools that don't need external access
    #   - Security: *arr apps have no built-in authentication
    #   - Bandwidth: Large media files stay on local network

    services = [
        # Sonarr - TV show management and organization
        unifi.Service {
            name = "sonarr"
            port = 8989
            protocol = "http"
            distribution = "unifi_only"
            # Internal DNS name format: servicename.internal.lan
            internal_hostname = "sonarr.internal.lan"
        },

        # Radarr - Movie management and organization
        unifi.Service {
            name = "radarr"
            port = 7878
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "radarr.internal.lan"
        },

        # Prowlarr - Indexer management for Sonarr/Radarr
        unifi.Service {
            name = "prowlarr"
            port = 9696
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "prowlarr.internal.lan"
        },

        # Lidarr - Music management (optional but included for completeness)
        unifi.Service {
            name = "lidarr"
            port = 8686
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "lidarr.internal.lan"
        },

        # Readarr - Book/ebook management (optional)
        unifi.Service {
            name = "readarr"
            port = 8787
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "readarr.internal.lan"
        },

        # ============================================================================
        # SERVICES: Cloudflare-Only (External Access Only)
        # ============================================================================
        #
        # These services are ONLY accessible through Cloudflare Tunnel.
        # They have distribution = "cloudflare_only" and require both
        # internal_hostname (for local_service_url) and public_hostname.
        #
        # Why Cloudflare-only?
        #   - These services need external access for mobile apps, sharing
        #   - Paperless-ngx: Access documents on the go
        #   - Immich: Photo backup from mobile devices

        # Paperless-ngx - Document management system
        unifi.Service {
            name = "paperless"
            port = 8000
            protocol = "http"
            distribution = "cloudflare_only"
            # internal_hostname is REQUIRED for constructing local_service_url
            internal_hostname = "paperless.internal.lan"
            # REPLACE: example.com with your actual Cloudflare zone
            public_hostname = "paperless.example.com"
        },

        # Immich - Self-hosted photo/video backup solution
        unifi.Service {
            name = "immich"
            port = 2283
            protocol = "http"
            distribution = "cloudflare_only"
            internal_hostname = "immich.internal.lan"
            # REPLACE: example.com with your actual Cloudflare zone
            public_hostname = "photos.example.com"
        },

        # ============================================================================
        # SERVICES: Both (Dual Exposure - Internal + External)
        # ============================================================================
        #
        # These services are accessible BOTH internally (UniFi DNS) AND
        # externally (Cloudflare Tunnel). They have distribution = "both"
        # and define both internal_hostname and public_hostname.
        #
        # Why both?
        #   - Jellyfin: Stream at home (direct) and away (via Cloudflare)
        #   - Jellyseerr: Request media from inside and outside the network
        #   - Local access avoids Cloudflare bandwidth limits for high-bitrate streaming

        # Jellyfin - Media server for streaming movies/TV/music
        unifi.Service {
            name = "jellyfin"
            port = 8096
            protocol = "http"
            distribution = "both"
            internal_hostname = "jellyfin.internal.lan"
            # REPLACE: example.com with your actual Cloudflare zone
            public_hostname = "media.example.com"
        },

        # Jellyseerr - Media request management for Jellyfin
        unifi.Service {
            name = "jellyseerr"
            port = 5055
            protocol = "http"
            distribution = "both"
            internal_hostname = "requests.internal.lan"
            # REPLACE: example.com with your actual Cloudflare zone
            public_hostname = "requests.example.com"
        },
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# This configuration is consumed by the unifi-dns Terraform module.
# It generates DNS records for:
#   - Device hostnames (from endpoints)
#   - Service CNAMEs (from services with distribution = "unifi_only" or "both")

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
#   - Cloudflare Tunnels (one per device MAC address)
#   - DNS records for tunnel ingress rules
#   - Ingress rules mapping public_hostnames to local_service_urls
#
# IMPORTANT: local_service_url construction
#   The generator builds local_service_url from:
#     "${protocol}://${internal_hostname}:${port}"
#   
#   Example: For Jellyfin with protocol=http, internal_hostname=jellyfin.internal.lan, port=8096
#   Result: "http://jellyfin.internal.lan:8096"
#
#   This MUST use internal domains to prevent DNS resolution loops.

cloudflare_config = cloudflare.CloudflareConfig {
    # REPLACE: example.com with your actual Cloudflare zone
    zone_name = "example.com"
    # REPLACE: a1b2c3d4e5f6789012345678901234ab with your Cloudflare account ID
    # Found in Cloudflare dashboard: Right sidebar -> Account ID
    account_id = "a1b2c3d4e5f6789012345678901234ab"
    default_no_tls_verify = False

    # Tunnels are keyed by MAC address (normalized to lowercase colon format)
    # Each physical device gets one tunnel
    tunnels = {
        # Primary tunnel on the management NIC
        # REPLACE: aa:bb:cc:dd:ee:01 with your management NIC MAC
        "aa:bb:cc:dd:ee:01": cloudflare.CloudflareTunnel {
            tunnel_name = "media-server"
            # REPLACE: aa:bb:cc:dd:ee:01 with your management NIC MAC
            mac_address = "aa:bb:cc:dd:ee:01"
            credentials_path = "/etc/cloudflared/media-server.json"

            # Services are automatically filtered to include only:
            #   - distribution = "cloudflare_only"
            #   - distribution = "both"
            # UniFi-only services are excluded from tunnel configuration.
            services = [
                # Cloudflare-only services
                cloudflare.TunnelService {
                    public_hostname = "paperless.example.com"
                    local_service_url = "http://paperless.internal.lan:8000"
                },
                cloudflare.TunnelService {
                    public_hostname = "photos.example.com"
                    local_service_url = "http://immich.internal.lan:2283"
                },
                # Dual-exposure services
                cloudflare.TunnelService {
                    public_hostname = "media.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                },
                cloudflare.TunnelService {
                    public_hostname = "requests.example.com"
                    local_service_url = "http://requests.internal.lan:5055"
                },
            ]
        }
    }
}

# ============================================================================
# OUTPUT GENERATION
# ============================================================================
#
# Generate the JSON files that Terraform will consume.
# Run: kcl run main.k
# This creates unifi.json and cloudflare.json in the outputs/ directory.

# Generate UniFi configuration
unifi_output = unifi_gen.generate_unifi_config(unifi_config)

# Generate Cloudflare configuration  
cf_output = cf_gen.generate_cloudflare_config(cloudflare_config)

# Output both configurations as a combined object
# The _uniFi and _cloudflare keys will be written to separate files
{
    _unifi = unifi_output
    _cloudflare = cf_output
}