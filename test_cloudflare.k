# Test file for Cloudflare schemas
# Validates that the cloudflare schemas work correctly and can be instantiated

import schemas.cloudflare as cf

# Create a valid CloudflareConfig instance with one tunnel and multiple services
config = cf.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:ff": cf.CloudflareTunnel {
            tunnel_name = "home-server"
            mac_address = "aa:bb:cc:dd:ee:ff"
            credentials_path = "/etc/cloudflared/home-server.json"
            services = [
                cf.TunnelService {
                    public_hostname = "media.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                    no_tls_verify = False
                },
                cf.TunnelService {
                    public_hostname = "files.example.com"
                    local_service_url = "https://nas.internal.lan:443"
                    no_tls_verify = True  # Self-signed certificate
                },
                cf.TunnelService {
                    public_hostname = "api.example.com"
                    local_service_url = "http://api.internal.lan:8080"
                    path_prefix = "/v1"
                }
            ]
        }
    }
}

# Output the configuration to verify it renders correctly
output = {
    # Full config output
    full_config = config
    
    # Individual tunnel access
    tunnel_count = len(config.tunnels)
    first_tunnel = config.tunnels["aa:bb:cc:dd:ee:ff"]
    
    # Service details
    service_count = len(config.tunnels["aa:bb:cc:dd:ee:ff"].services)
    first_service_hostname = config.tunnels["aa:bb:cc:dd:ee:ff"].services[0].public_hostname
    
    # Validation info
    zone_info = {
        zone_name = config.zone_name
        account_id = config.account_id
        default_no_tls_verify = config.default_no_tls_verify
    }
}
