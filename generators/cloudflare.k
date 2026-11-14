# Cloudflare Configuration Generator
# Generates Cloudflare Tunnel-compatible JSON configuration from KCL service definitions

# Import schemas
import ..schemas.base
import ..schemas.cloudflare

# normalize_mac is re-exported from base module for convenience
normalize_mac = base.normalize_mac

# Filter services for Cloudflare Tunnel (exclude unifi_only)
# Returns list of services that should be included in Cloudflare configuration
filter_cloudflare_services = lambda services: [base.Service] {
    [svc for svc in services if svc.distribution in ["cloudflare_only", "both"]]
}

# Compare DNS names, not arbitrary URL substrings (DNS loop prevention).
contains_zone_name = lambda url: str, zone: str -> bool {
    hostname = cloudflare.origin_hostname(url)
    normalized_zone = zone.lower().rstrip(".")
    hostname == normalized_zone or hostname.endswith(".${normalized_zone}")
}

# Same-zone origins are rejected unless the operator declares that exact origin.
# Acceptance of intent does not establish the connector's actual DNS resolution.
validate_no_dns_loop = lambda url: str, zone: str, split_dns_origins: [cloudflare.SplitDNSOrigin] = [] -> bool {
    not contains_zone_name(url, zone) or len([origin for origin in split_dns_origins if cloudflare.matches_split_dns_origin(url, origin)]) > 0
}

# Return the original service only after validating its resolved origin.
validate_tunnel_service = lambda service: any, zone: str, tunnel_name: str, split_dns_origins: [cloudflare.SplitDNSOrigin] = [] -> any {
    assert validate_no_dns_loop(service.local_service_url, zone, split_dns_origins), "DNS loop risk in tunnel '${tunnel_name}', service '${service.public_hostname}': unapproved origin hostname '${cloudflare.origin_hostname(service.local_service_url)}' belongs to public zone '${zone}'; use an internal hostname outside the public zone or declare this exact split_dns_origins entry and verify connector DNS separately"
    service
}

# Build local_service_url from service components
# Format: {protocol}://{hostname}:{port}
build_local_service_url = lambda protocol: str, hostname: str, port: int -> str {
    "${protocol}://${hostname}:${port}"
}

# Resolve the hostname for local_service_url
# Priority: service.internal_hostname > device_hostname + domain
resolve_internal_hostname = lambda service: base.Service, device_hostname: str, domain: str -> str {
    service.internal_hostname if service.internal_hostname not in [None, Undefined] else "${device_hostname}.${domain}"
}

# Resolve public_hostname for a service
# Priority: service.public_hostname > service.name + zone_name
resolve_public_hostname = lambda service: base.Service, zone_name: str -> str {
    service.public_hostname if service.public_hostname != None else "${service.name}.${zone_name}"
}

# Transform a base.Service to a TunnelService record for JSON output
# This converts the unified service definition to Cloudflare-specific format
transform_service = lambda service: base.Service, device_hostname: str, domain: str, zone_name: str, default_no_tls_verify: bool, split_dns_origins: [cloudflare.SplitDNSOrigin] = [] -> any {
    # Resolve internal hostname
    internal_hostname = resolve_internal_hostname(service, device_hostname, domain)

    # Build local_service_url
    local_url = build_local_service_url(service.protocol, internal_hostname, service.port)
    assert validate_no_dns_loop(local_url, zone_name, split_dns_origins), "DNS loop risk in tunnel '${device_hostname}', service '${service.name}': unapproved origin hostname '${cloudflare.origin_hostname(local_url)}' belongs to public zone '${zone_name}'; set an internal_hostname outside the public zone or declare this exact split_dns_origins entry and verify connector DNS separately"

    # Build the service record
    {
        public_hostname = resolve_public_hostname(service, zone_name)
        local_service_url = local_url
        no_tls_verify = default_no_tls_verify
    }
}

# Transform services for a tunnel, filtering by distribution
# Returns list of TunnelService records
transform_tunnel_services = lambda services: [base.Service], device_hostname: str, domain: str, zone_name: str, default_no_tls_verify: bool, split_dns_origins: [cloudflare.SplitDNSOrigin] = [] -> [any] {
    filtered_services = filter_cloudflare_services(services)
    [transform_service(svc, device_hostname, domain, zone_name, default_no_tls_verify, split_dns_origins) for svc in filtered_services]
}

# Generate Cloudflare configuration from CloudflareConfig
# Returns a dictionary with zone_name, account_id, and tunnels for JSON serialization
generate_cloudflare_config = lambda config: cloudflare.CloudflareConfig {
    # Transform all tunnels, keyed by normalized MAC address
    # config.tunnels is {str:CloudflareTunnel}, so we iterate over items
    {
        zone_name = config.zone_name
        account_id = config.account_id
        tunnels = {normalize_mac(mac): {
            tunnel_name = tunnel.tunnel_name
            mac_address = normalize_mac(tunnel.mac_address)
            services = [validate_tunnel_service(svc, config.zone_name, tunnel.tunnel_name, config.split_dns_origins) for svc in tunnel.services]
        } for mac, tunnel in config.tunnels}
    }
}

# Alternative generator that works with base entities and services
# This creates CloudflareTunnel-compatible output from base schema entities
generate_cloudflare_from_entities = lambda entities: [base.Entity], zone_name: str, account_id: str, default_no_tls_verify: bool = False, internal_domain: str = "internal.lan", split_dns_origins: [cloudflare.SplitDNSOrigin] = [] {
    # Build tunnels from entities with cloudflare-capable services
    # Use comprehension to build the tunnels dictionary
    {
        zone_name = zone_name
        account_id = account_id
        tunnels = {normalize_mac(entity.endpoints[0].mac_address): {
            tunnel_name = entity.friendly_hostname
            mac_address = normalize_mac(entity.endpoints[0].mac_address)
            services = transform_tunnel_services(entity.services, entity.friendly_hostname, internal_domain, zone_name, default_no_tls_verify, split_dns_origins)
        } for entity in entities if len(entity.services) > 0 and len(filter_cloudflare_services(entity.services)) > 0 and len(entity.endpoints) > 0}
    }
}

# Internal sample configuration - used when running this file directly
# Not exported as output (see 'result' below for the single output)
_sample_config = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    default_no_tls_verify = False
    tunnels = {
        # Media server tunnel
        "aa:bb:cc:dd:ee:01": cloudflare.CloudflareTunnel {
            tunnel_name = "media-server"
            mac_address = "AA:BB:CC:DD:EE:01"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "jellyfin.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
                cloudflare.TunnelService {
                    public_hostname = "plex.example.com"
                    local_service_url = "http://plex.internal.lan:32400"
                    # Self-signed cert
                    no_tls_verify = True
                }
            ]
        }
        # NAS tunnel with multiple services
        "aa-bb-cc-dd-ee-02": cloudflare.CloudflareTunnel {
            tunnel_name = "nas-server"
            mac_address = "aa-bb-cc-dd-ee-02"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "files.example.com"
                    local_service_url = "https://nas.internal.lan:443"
                    no_tls_verify = True
                }
                cloudflare.TunnelService {
                    public_hostname = "sync.example.com"
                    local_service_url = "http://syncthing.internal.lan:8384"
                }
            ]
        }
        # IoT hub with mixed distribution services
        "aa:bb:cc:dd:ee:03": cloudflare.CloudflareTunnel {
            tunnel_name = "iot-hub"
            mac_address = "aa:bb:cc:dd:ee:03"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "homeassistant.example.com"
                    local_service_url = "http://hass.internal.lan:8123"
                }
            ]
        }
    }
}

# Single output: generated configuration from sample config
# This ensures only one YAML document is output, fixing yq parsing issues
result = generate_cloudflare_config(_sample_config)
