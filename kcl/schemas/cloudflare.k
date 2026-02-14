# Cloudflare Schema Extensions
# Extends base schemas for Cloudflare Tunnel management
#
# This module defines the configuration schemas for Cloudflare Zero Trust Tunnels,
# enabling secure access to internal services through public DNS entries.
#
# Example Usage:
#     import .schemas.cloudflare
#     import .schemas.base
#
#     config = cloudflare.CloudflareConfig {
#         zone_name = "example.com"
#         account_id = "1234567890abcdef"
#         tunnels = {
#             "aa:bb:cc:dd:ee:ff": cloudflare.CloudflareTunnel {
#                 tunnel_name = "home-server"
#                 mac_address = "aa:bb:cc:dd:ee:ff"
#                 services = [
#                     cloudflare.TunnelService {
#                         public_hostname = "media.example.com"
#                         local_service_url = "http://jellyfin.internal.lan:8096"
#                     }
#                 ]
#             }
#         }
#     }

# MACAddress type alias for tunnel identification
MACAddress = str

# is_valid_domain checks if a URL contains a valid domain per RFC 1123
# Returns True if the hostname has valid syntax
# Validation rules:
# - Valid characters: alphanumeric, hyphens, dots only
# - No consecutive dots
# - No leading/trailing dots
# - Each label: 1-63 characters
# - Labels must start and end with alphanumeric
# - TLD: minimum 2 characters
# - At least one dot separator required
is_valid_domain = lambda url: str -> bool {
    hostname = url.replace("http://", "").replace("https://", "").split("/")[0].split(":")[0]
    labels = hostname.split(".")
    tld = labels[-1]
    validLabels = [l for l in labels if len(l) > 0 and len(l) <= 63 and l[0].isalnum() and l[-1].isalnum()]
    len(hostname) > 0 and not hostname.startswith(".") and not hostname.endswith(".") and ".." not in hostname and "." in hostname and len(validLabels) == len(labels) and len(tld) >= 2
}

# hostname_in_zone checks if a hostname belongs to the configured zone
# Returns True if the hostname is a subdomain of zone_name or equals it
hostname_in_zone = lambda hostname: str, zone: str -> bool {
    hostname.endswith(".${zone}") or hostname == zone
}

# TunnelService represents an ingress rule for Cloudflare Tunnel
# Defines how public traffic routes to internal services
schema TunnelService:
    """
    TunnelService defines a single ingress rule for routing traffic through
    a Cloudflare Tunnel from a public hostname to an internal service.

    Each service maps a public-facing hostname to a local internal URL,
    allowing secure access to internal services without exposing them directly.

    Attributes:
        public_hostname: The public-facing FQDN (e.g., "media.example.com")
                         Must be a subdomain of the zone configured in CloudflareConfig
        local_service_url: The internal URL where the service is accessible
                           Must use a valid domain name (RFC 1123 syntax)
        no_tls_verify: Skip TLS certificate verification for the local service
                       WARNING: Only use for self-signed certificates in development
        path_prefix: Optional path prefix for request routing (e.g., "/api")

    Example:
        TunnelService {
            public_hostname = "jellyfin.example.com"
            local_service_url = "http://jellyfin.internal.lan:8096"
            no_tls_verify = False
        }
    """
    public_hostname: str
    local_service_url: str
    no_tls_verify: bool = False
    path_prefix?: str

    check:
        # public_hostname must not be empty
        len(public_hostname) > 0, "public_hostname cannot be empty"
        # local_service_url must not be empty
        len(local_service_url) > 0, "local_service_url cannot be empty"
        # local_service_url must use valid domain syntax to prevent DNS loops
        is_valid_domain(local_service_url), "local_service_url has invalid domain syntax"

# CloudflareTunnel represents a single tunnel connected to a physical device
# Each tunnel is uniquely associated with one MAC address
schema CloudflareTunnel:
    """
    CloudflareTunnel represents a Cloudflare Zero Trust Tunnel configuration
    linked to a specific physical device identified by MAC address.

    A tunnel acts as a secure conduit between Cloudflare's edge network and
    your internal services, allowing you to expose services publicly without
    opening firewall ports or exposing your IP address.

    Attributes:
        tunnel_name: Unique identifier for the tunnel (e.g., "home-server", "nas-tunnel")
        mac_address: MAC address of the physical device running cloudflared
                     Used to link tunnel configuration to network discovery
        services: List of ingress rules defining how traffic routes to local services
        credentials_path: Optional filesystem path to tunnel credentials JSON file
                          Defaults to "/etc/cloudflared/${tunnel_name}.json"

    Validation:
        - tunnel_name must be non-empty
        - mac_address must be 17 characters (aa:bb:cc:dd:ee:ff format)
        - Each MAC address can only have one tunnel (enforced by using MAC as dict key)

    Example:
        CloudflareTunnel {
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            services = [
                TunnelService {
                    public_hostname = "jellyfin.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
            ]
            credentials_path = "/etc/cloudflared/media-server.json"
        }
    """
    tunnel_name: str
    mac_address: MACAddress
    services: [TunnelService] = []
    credentials_path?: str

    check:
        # tunnel_name must not be empty
        len(tunnel_name) > 0, "tunnel_name cannot be empty"
        # mac_address must be valid format (17 chars for colon-separated)
        len(mac_address) == 17, "mac_address must be 17 characters in aa:bb:cc:dd:ee:ff format"

# CloudflareConfig is the root configuration container for all Cloudflare resources
# Holds zone settings, account information, and all tunnel definitions
schema CloudflareConfig:
    """
    CloudflareConfig is the top-level configuration for Cloudflare Tunnel integration.

    This schema holds all Cloudflare-specific settings including the DNS zone,
    account identifier, and a dictionary of all tunnels keyed by MAC address.

    Attributes:
        zone_name: The Cloudflare DNS zone name (e.g., "example.com")
                   All public_hostnames in tunnel services must be subdomains of this zone
        account_id: Cloudflare account identifier (found in Cloudflare dashboard)
        tunnels: Dictionary mapping MAC addresses to CloudflareTunnel objects
                 Each MAC address can have only one tunnel (one-to-one mapping)
        default_no_tls_verify: Default value for no_tls_verify across all services
                               Can be overridden per-service. Defaults to False.

    Validation:
        - zone_name must be non-empty
        - account_id must be non-empty
        - Tunnel dictionary keys must match tunnel.mac_address values
        - All public_hostnames should be subdomains of zone_name

    Example:
        CloudflareConfig {
            zone_name = "example.com"
            account_id = "1234567890abcdef1234567890abcdef"
            default_no_tls_verify = False
            tunnels = {
                "aa:bb:cc:dd:ee:ff": CloudflareTunnel {
                    tunnel_name = "home-server"
                    mac_address = "aa:bb:cc:dd:ee:ff"
                    services = [
                        TunnelService {
                            public_hostname = "media.example.com"
                            local_service_url = "http://jellyfin.internal.lan:8096"
                        },
                        TunnelService {
                            public_hostname = "files.example.com"
                            local_service_url = "https://nas.internal.lan:443"
                            no_tls_verify = True  # Self-signed cert
                        }
                    ]
                }
            }
        }
    """
    zone_name: str
    account_id: str
    tunnels: {str:CloudflareTunnel} = {}
    default_no_tls_verify: bool = False

    check:
        # zone_name must not be empty
        len(zone_name) > 0, "zone_name cannot be empty"
        # account_id must not be empty
        len(account_id) > 0, "account_id cannot be empty"

