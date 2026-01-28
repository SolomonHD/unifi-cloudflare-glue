# UniFi Schema Extensions
# Extends base schemas for UniFi DNS management

# UniFi client device definition
# Represents a physical device connected to the UniFi network
schema UniFiClient:
    """UniFi client device with MAC and IP assignment"""
    name: str
    mac_address: str
    fixed_ip?: str

# UniFi DNS record for local name resolution
# Maps hostnames to IP addresses within the local network
schema UniFiDNSRecord:
    """DNS record for UniFi local resolution"""
    hostname: str
    ip: str
    description?: str

# UniFi configuration container
# Holds all UniFi-specific configuration
schema UniFiConfig:
    """Complete UniFi configuration"""
    clients: [UniFiClient] = []
    dns_records: [UniFiDNSRecord] = []
