import .schemas.base
import .schemas.unifi
import .schemas.cloudflare
import .generators.unifi as unifi_gen
import .generators.cloudflare as cf_gen

_mac = option("mac", default="AA:BB:CC:DD:EE:FF")
_services = [] if option("no_services", default=False) else [
    {name = "both", port = 443, protocol = "https", distribution = "both", internal_hostname = "both.internal.lan", public_hostname = "both.example.com"}
    {name = "local", port = 22, protocol = "tcp", distribution = "unifi_only", internal_hostname = "local.internal.lan", public_hostname = None}
    {name = "remote", port = 8080, protocol = "http", distribution = "cloudflare_only", internal_hostname = None, public_hostname = None}
]
_devices = [] if option("empty", default=False) else [unifi.UniFiEntity {
    friendly_hostname = "server"
    domain = "internal.lan"
    service_cnames = ["explicit.internal.lan"]
    endpoints = [
        unifi.UniFiEndpoint {mac_address = _mac, nic_name = "eth0", service_cnames = ["wired.internal.lan"]}
        unifi.UniFiEndpoint {mac_address = "11-22-33-44-55-66"}
    ]
    services = _services
}]
unifi_output = unifi_gen.generate_unifi_config(unifi.UniFiConfig {
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {host = "controller.internal.lan", site = "test-site"}
    devices = _devices
})
cf_output = cf_gen.generate_cloudflare_config(cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "test-account"
    tunnels = {} if option("empty", default=False) else {
        "${_mac}": cloudflare.CloudflareTunnel {
            tunnel_name = "server"
            # CloudflareTunnel requires 17 chars; compact dictionary keys remain raw.
            mac_address = base.normalize_mac(_mac) if len(_mac) == 12 else _mac
            services = cf_gen.transform_tunnel_services(
                [base.Service {**svc} for svc in _services], "server", "internal.lan", "example.com", True
            )
        }
    }
})
origin_checks = [cf_gen.validate_no_dns_loop(svc.local_service_url, "example.com") for _, tunnel in cf_output.tunnels for svc in tunnel.services]
