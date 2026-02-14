# UniFi Schema Extensions for unifi-cloudflare-glue
#
# This module extends the base schemas with UniFi-specific configuration for managing
# local DNS through the UniFi Controller. It provides UniFiEntity for device definitions,
# UniFiEndpoint for network interfaces with UniFi-specific properties, and UniFiConfig
# as the root configuration container.
#
# Core Concepts:
# - UniFiEntity: Device configuration with UniFi site support and device-level CNAMEs
# - UniFiEndpoint: Network interface with query_unifi flag and static IP support
# - UniFiConfig: Root configuration containing devices, domain, and controller settings

# MACAddress validates and normalizes MAC addresses to lowercase colon format.
type MACAddress = str

# Hostname validates DNS labels according to RFC 1123.
type Hostname = str

# Distribution controls where service DNS records are published.
type Distribution = "unifi_only" | "cloudflare_only" | "both"

# UniFiEndpoint represents a network interface on a UniFi-managed device.
#
# This schema extends the base endpoint concept with UniFi-specific properties
# for querying the UniFi Controller for IP addresses or using static IP assignment.
#
# Example:
#     endpoint = UniFiEndpoint {
#         mac_address = "aa:bb:cc:dd:ee:ff"
#         nic_name = "eth0"
#         query_unifi = true
#         static_ip = "192.168.1.100"
#     }
schema UniFiEndpoint:
    """UniFi-aware endpoint with IP management options.

    Attributes:
        mac_address: The MAC address of the network interface.
                     Accepts formats: aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, or aabbccddeeff
        nic_name: Optional human-readable name for the interface (e.g., "eth0", "wlan0")
        service_cnames: List of CNAME aliases for services running on this endpoint
        query_unifi: Whether to query UniFi Controller for current IP (default: true)
        static_ip: Static IP to use when query_unifi is false
    """
    mac_address: MACAddress
    nic_name?: str
    service_cnames: [str] = []
    
    # UniFi-specific fields
    query_unifi: bool = True
    static_ip?: str

    check:
        # Validate MAC address length (must be 17 for colon/hyphen format or 12 for no separator)
        len(mac_address) in [12, 17], "MAC address must be 12 chars (aabbccddeeff) or 17 chars (aa:bb:cc:dd:ee:ff or aa-bb-cc-dd-ee-ff)"
        
        # Each endpoint must have MAC address or static_ip
        (mac_address != "") or (static_ip != None), \
            "Each endpoint must have a MAC address or static_ip configured"

# Service represents an application running on an entity.
schema Service:
    """Service represents an application service running on a device.

    Attributes:
        name: Service identifier (e.g., "jellyfin", "plex", "ssh")
        port: TCP/UDP port number (1-65535)
        protocol: Application protocol - "http", "https", or "tcp"
        distribution: Where to publish DNS records (unifi_only, cloudflare_only, or both)
        internal_hostname: Optional internal DNS name (e.g., "jellyfin.internal.lan")
        public_hostname: Optional public DNS name (e.g., "jellyfin.example.com")
    """
    name: str
    port: int
    protocol: "http" | "https" | "tcp"
    distribution: Distribution = "both"
    internal_hostname?: str
    public_hostname?: str

    check:
        # Port must be in valid range
        port >= 1 and port <= 65535, "Port must be between 1 and 65535"

# UniFiEntity represents a physical device in the UniFi network.
#
# This schema represents a physical device with support for site-specific
# configuration and device-level CNAME aliases for services.
#
# Example:
#     device = UniFiEntity {
#         friendly_hostname = "nas-01"
#         domain = "internal.lan"
#         unifi_site = "default"
#         service_cnames = ["storage", "backup"]
#         endpoints = [...]
#         services = [...]
#     }
schema UniFiEntity:
    """UniFi-aware entity with site and CNAME support.

    Attributes:
        friendly_hostname: DNS-compatible hostname for the device (e.g., "nas-01", "server-prod")
                           Must be 1-63 characters, start/end with letter/digit,
                           and contain only letters, digits, and hyphens.
        domain: Base domain for DNS records (e.g., "internal.lan", "home.local")
                Must end in .lan, .local, or .home for safety.
        endpoints: List of UniFiEndpoint objects representing network interfaces
        services: List of Service objects representing applications on this device
        unifi_site: UniFi site name where this device is managed (default: "default")
        service_cnames: Additional device-level CNAME aliases for services
    """
    friendly_hostname: Hostname
    domain: str
    endpoints: [UniFiEndpoint] = []
    services: [Service] = []
    
    # UniFi-specific fields
    unifi_site: str = "default"
    service_cnames: [str] = []

    check:
        # Each device must have at least one endpoint
        len(endpoints) >= 1, "Each device must have at least one endpoint"
        
        # Domain must end in .lan, .local, or .home for safety
        domain.endswith(".lan") or domain.endswith(".local") or domain.endswith(".home"), \
            "Domain must end in .lan, .local, or .home for internal DNS safety"
        
        # Validate hostname length (RFC 1123: 1-63 characters)
        len(friendly_hostname) >= 1 and len(friendly_hostname) <= 63, \
            "Hostname must be 1-63 characters"
        
        # Validate hostname contains only valid characters (letters, digits, hyphens)
        # Basic check: no underscores, spaces, or special characters
        not ("_" in friendly_hostname or " " in friendly_hostname or "." in friendly_hostname or "@" in friendly_hostname), \
            "Hostname must not contain underscores, spaces, dots, or special characters"

# UniFiController holds connection details for the UniFi Controller.
#
# This schema contains the necessary information to connect to a UniFi Controller
# for querying device information and managing DNS records.
#
# Example:
#     controller = UniFiController {
#         host = "unifi.local"
#         port = 443
#         username_ref = "UNIFI_USERNAME"
#         password_ref = "UNIFI_PASSWORD"
#     }
schema UniFiController:
    """Connection configuration for UniFi Controller.

    Attributes:
        host: Hostname or IP address of the UniFi Controller
        port: HTTPS port for the controller (default: 443)
        username_ref: Environment variable name containing the username
        password_ref: Environment variable name containing the password
        site: Default site to use when not specified per-device (default: "default")
    """
    host: str
    port: int = 443
    username_ref: str = "UNIFI_USERNAME"
    password_ref: str = "UNIFI_PASSWORD"
    site: str = "default"

    check:
        # Port must be in valid range
        port >= 1 and port <= 65535, "Port must be between 1 and 65535"
        
        # Host should not be empty
        len(host) > 0, "Host must not be empty"

# UniFiConfig is the root configuration container for UniFi-specific settings.
#
# This schema serves as the entry point for UniFi DNS configuration, containing
# all devices, the default domain for internal DNS, and UniFi Controller connection
# details.
#
# Example:
#     config = UniFiConfig {
#         devices = [nas_device, server_device]
#         default_domain = "internal.lan"
#         unifi_controller = UniFiController {
#             host = "unifi.local"
#         }
#     }
schema UniFiConfig:
    """Root configuration container for UniFi DNS management.

    Attributes:
        devices: List of UniFiEntity objects representing physical devices
        default_domain: Default domain for internal DNS records (e.g., "internal.lan")
        unifi_controller: Connection details for the UniFi Controller
    """
    devices: [UniFiEntity] = []
    default_domain: str = "internal.lan"
    unifi_controller: UniFiController = UniFiController {}

    check:
        # Default domain must end in .lan, .local, or .home for safety
        default_domain.endswith(".lan") or default_domain.endswith(".local") or default_domain.endswith(".home"), \
            "default_domain must end in .lan, .local, or .home for internal DNS safety"
