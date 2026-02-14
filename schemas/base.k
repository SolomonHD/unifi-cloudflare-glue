# Base Schemas for unifi-cloudflare-glue
#
# This module defines the core domain models used across both UniFi and Cloudflare configurations.
# It provides the foundational type system that bridges the two providers through a unified
# configuration layer.
#
# Core Concepts:
# - Entity: A physical device (server, NAS, router, etc.) with network interfaces and services
# - Endpoint: A network interface on an entity, identified by MAC address
# - Service: An application running on an entity, exposed via specific ports and protocols
# - Distribution: Controls where DNS records are published (UniFi, Cloudflare, or both)

# MACAddress validates and normalizes MAC addresses to lowercase colon format.
# Accepts three formats:
#   - Colon-separated: "aa:bb:cc:dd:ee:ff"
#   - Hyphen-separated: "aa-bb-cc-dd-ee-ff"
#   - No separator: "aabbccddeeff"
# All formats are normalized to lowercase colon format.
type MACAddress = str

# Hostname validates DNS labels according to RFC 1123.
# Requirements:
#   - 1-63 characters in length
#   - Starts with letter or digit
#   - Contains only letters, digits, and hyphens
#   - Ends with letter or digit
type Hostname = str

# Distribution controls where service DNS records are published.
# - unifi_only: Create DNS record only in UniFi (internal network)
# - cloudflare_only: Create DNS record only in Cloudflare (external/public)
# - both: Create DNS records in both UniFi and Cloudflare
type Distribution = "unifi_only" | "cloudflare_only" | "both"

# normalize_mac converts any valid MAC address format to lowercase colon format
# by removing separators and reinserting colons
normalize_mac = lambda mac: str -> str {
    # Remove all separators
    no_colons = mac.replace(":", "")
    no_hyphens = no_colons.replace("-", "")
    # Convert to lowercase
    cleaned = no_hyphens.lower()
    # Format as colon-separated
    "${cleaned[0:2]}:${cleaned[2:4]}:${cleaned[4:6]}:${cleaned[6:8]}:${cleaned[8:10]}:${cleaned[10:12]}"
}

# Endpoint represents a network interface on an entity.
# Each endpoint is uniquely identified by its MAC address and can have
# associated CNAME records for service discovery.
schema Endpoint:
    """
    Endpoint represents a network interface on a physical device.

    Attributes:
        mac_address: The MAC address of the network interface.
                     Accepts formats: aa:bb:cc:dd:ee:ff, aa-bb-cc-dd-ee-ff, or aabbccddeeff
        nic_name: Optional human-readable name for the interface (e.g., "eth0", "wlan0")
        service_cnames: List of CNAME aliases for services running on this endpoint
    """
    mac_address: MACAddress
    nic_name?: str
    service_cnames: [str] = []

    check:
        # Validate MAC address length (must be 17 for colon/hyphen format or 12 for no separator)
        len(mac_address) in [12, 17], "MAC address must be 12 chars (aabbccddeeff) or 17 chars (aa:bb:cc:dd:ee:ff or aa-bb-cc-dd-ee-ff)"

# Service represents an application running on an entity.
# Services can be exposed internally, externally, or both based on the distribution setting.
schema Service:
    """
    Service represents an application service running on an entity.

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

# Entity represents a physical device with network interfaces and services.
# This is the top-level configuration object that bridges UniFi and Cloudflare.
schema Entity:
    """
    Entity represents a physical device (server, NAS, router, etc.) in the network.

    An entity has one or more network endpoints (interfaces) and can host multiple services.
    The friendly_hostname combined with the domain forms the base DNS name for the entity.

    Attributes:
        friendly_hostname: DNS-compatible hostname for the device (e.g., "nas-01", "server-prod")
                           Must be 1-63 characters, start/end with letter/digit, 
                           and contain only letters, digits, and hyphens.
        domain: Base domain for DNS records (e.g., "internal.lan", "example.com")
        endpoints: List of network interfaces on this entity
        services: List of services running on this entity
    """
    friendly_hostname: Hostname
    domain: str
    endpoints: [Endpoint] = []
    services: [Service] = []

    check:
        # Validate hostname length (RFC 1123: 1-63 characters)
        len(friendly_hostname) >= 1 and len(friendly_hostname) <= 63, \
        "Hostname must be 1-63 characters"
