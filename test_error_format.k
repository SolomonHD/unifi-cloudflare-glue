# Test error formatting
import .main
import .schemas.unifi
import .schemas.cloudflare

# Create a config with MAC mismatch
test_unifi = unifi.UniFiConfig {
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
    }
    devices = [
        unifi.UniFiEntity {
            friendly_hostname = "media-server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa:bb:cc:dd:ee:01"
                }
            ]
            services = []
        }
    ]
}

test_cloudflare = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    tunnels = {
        "aa:bb:cc:dd:ee:99": cloudflare.CloudflareTunnel {
            tunnel_name = "unknown-server"
            mac_address = "aa:bb:cc:dd:ee:99"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "unknown.example.com"
                    local_service_url = "http://unknown.internal.lan:8080"
                }
            ]
        }
    }
}

test_config = main.UnifiedConfig {
    unifi = test_unifi
    cloudflare = test_cloudflare
}

test_result = main.generate(test_config)

# Test error formatting
formatted_errors = main.format_validation_errors(test_result.errors)
