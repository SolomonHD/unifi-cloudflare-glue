# Internal-Only Services Example Configuration
#
# This example demonstrates services that are accessible ONLY within the local
# network. No Cloudflare tunnels are created, ensuring these services cannot
# be accessed from the internet.
#
# PLACEHOLDERS TO CUSTOMIZE:
#   - aa:bb:cc:dd:ee:ff: Replace with your device's MAC address
import unifi_cloudflare_glue.schemas.unifi as unifi

# ============================================================================
# DEVICE DEFINITION: Internal Tools Server
# ============================================================================
#
# This server hosts internal management and monitoring tools that should
# never be accessible from the internet.
internal_tools = unifi.UniFiEntity {
    friendly_hostname = "internal-tools"
    domain = "internal.lan"
    unifi_site = "default"
    endpoints = [
        unifi.UniFiEndpoint {
            mac_address = "aa:bb:cc:dd:ee:ff"
            nic_name = "eth0"
            query_unifi = True
        }
    ]
    services = [
        # ============================================================================
        # SERVICE 1: Prometheus Monitoring
        # ============================================================================
        unifi.Service {
            name = "prometheus"
            port = 9090
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "metrics.internal.lan"
        }
        # ============================================================================
        # SERVICE 2: Grafana Dashboards
        # ============================================================================
        unifi.Service {
            name = "grafana"
            port = 3000
            protocol = "http"
            distribution = "unifi_only"
            internal_hostname = "dashboards.internal.lan"
        }
        # ============================================================================
        # SERVICE 3: Portainer (Docker Management)
        # ============================================================================
        unifi.Service {
            name = "portainer"
            port = 9000
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "docker.internal.lan"
        }
        # ============================================================================
        # SERVICE 4: UniFi Controller (Internal Access)
        # ============================================================================
        unifi.Service {
            name = "unifi"
            port = 8443
            protocol = "https"
            distribution = "unifi_only"
            internal_hostname = "unifi-mgmt.internal.lan"
        }
    ]
}

# ============================================================================
# UNIFI CONFIGURATION
# ============================================================================
#
# Creates DNS records for all internal-only services:
#   - metrics.internal.lan (Prometheus)
#   - dashboards.internal.lan (Grafana)
#   - docker.internal.lan (Portainer)
#   - unifi-mgmt.internal.lan (UniFi Controller)
unifi_config = unifi.UniFiConfig {
    devices = [internal_tools]
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
        port = 443
        username_ref = "UNIFI_USERNAME"
        password_ref = "UNIFI_PASSWORD"
        site = "default"
    }
}

# ============================================================================
# OUTPUT
# ============================================================================
#
# Note: This example only outputs UniFi configuration.
# There is NO Cloudflare configuration since all services are unifi_only.
{
    _unifi = unifi_config
}
