# UniFi Configuration Generator
# Generates UniFi-compatible JSON configuration from KCL service definitions

# Import schemas
import ..schemas.base
import ..schemas.unifi

# normalize_mac is re-exported from base module for convenience
normalize_mac = base.normalize_mac

# Transform UniFiEndpoint to NIC record for JSON output
# Returns a dictionary with mac_address, optional nic_name, and service_cnames
transform_endpoint = lambda endpoint: unifi.UniFiEndpoint {
    {
        mac_address = normalize_mac(endpoint.mac_address)
        nic_name = endpoint.nic_name if endpoint.nic_name != None else None
        service_cnames = endpoint.service_cnames
    }
}

# Filter services for UniFi DNS (exclude cloudflare_only)
# Returns list of services that should be included in UniFi DNS
filter_unifi_services = lambda services: [unifi.Service] {
    [
        svc for svc in services
        if svc.distribution in ["unifi_only", "both"]
    ]
}

# Generate CNAMEs from services for UniFi DNS
# Extracts internal_hostnames from services filtered for UniFi
generate_service_cnames = lambda services: [unifi.Service] {
    [
        svc.internal_hostname
        for svc in filter_unifi_services(services)
        if svc.internal_hostname != None
    ]
}

# Transform UniFiEntity to device record for JSON output
# Returns a dictionary matching the UniFi Terraform module input schema
transform_entity = lambda entity: unifi.UniFiEntity {
    # Generate service CNAMEs from services with internal_hostnames
    service_cnames_from_services = generate_service_cnames(entity.services)
    
    # Combine explicit service_cnames with those from services
    all_service_cnames = entity.service_cnames + service_cnames_from_services
    
    {
        friendly_hostname = entity.friendly_hostname
        domain = entity.domain
        service_cnames = all_service_cnames
        nics = [transform_endpoint(ep) for ep in entity.endpoints]
    }
}

# Generate UniFi configuration from UniFiConfig
# Returns a dictionary with devices and default_domain for JSON serialization
generate_unifi_config = lambda config: unifi.UniFiConfig {
    {
        devices = [transform_entity(device) for device in config.devices]
        default_domain = config.default_domain
    }
}

# Sample configuration for testing
# This demonstrates the generator with realistic homelab devices
sample_config = unifi.UniFiConfig {
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
    }
    devices = [
        # Media server with multiple services
        unifi.UniFiEntity {
            friendly_hostname = "media-server"
            domain = "internal.lan"
            service_cnames = ["storage.internal.lan"]
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "AA:BB:CC:DD:EE:01"
                    nic_name = "eth0"
                    service_cnames = ["nas.internal.lan"]
                }
            ]
            services = [
                unifi.Service {
                    name = "jellyfin"
                    port = 8096
                    protocol = "http"
                    distribution = "both"
                    internal_hostname = "jellyfin.internal.lan"
                    public_hostname = "jellyfin.example.com"
                }
                unifi.Service {
                    name = "plex"
                    port = 32400
                    protocol = "https"
                    distribution = "unifi_only"
                    internal_hostname = "plex.internal.lan"
                }
                unifi.Service {
                    name = "admin-panel"
                    port = 8080
                    protocol = "https"
                    distribution = "cloudflare_only"
                    public_hostname = "admin.example.com"
                }
            ]
        }
        # Backup server with multiple NICs
        unifi.UniFiEntity {
            friendly_hostname = "backup-server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa-bb-cc-dd-ee-02"
                    nic_name = "eth0"
                    service_cnames = ["backup-eth0.internal.lan"]
                }
                unifi.UniFiEndpoint {
                    mac_address = "AABBCCDDEE03"
                    nic_name = "eth1"
                    service_cnames = ["backup-eth1.internal.lan"]
                }
            ]
            services = [
                unifi.Service {
                    name = "restic"
                    port = 8000
                    protocol = "http"
                    distribution = "unifi_only"
                    internal_hostname = "backups.internal.lan"
                }
            ]
        }
        # Simple device with no extra services
        unifi.UniFiEntity {
            friendly_hostname = "iot-hub"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "Ab:Cd:Ef:01:23:45"
                    service_cnames = []
                }
            ]
            services = []
        }
    ]
}

# Generate and output the configuration
result = generate_unifi_config(sample_config)
