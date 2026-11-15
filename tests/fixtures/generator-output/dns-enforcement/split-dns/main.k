import .schemas.base
import .schemas.cloudflare
import .generators.cloudflare as cf_gen

_zone = option("zone", default="sghd.io")
_mode = option("mode", default="explicit")
_hostname = option("hostname", default="traefik-mid.sghd.io")
_scheme = option("scheme", default="https")
_port = option("port", default=443)
_url = option("url", default="${_scheme}://${_hostname}:${_port}/path?next=internal.lan#fragment")
_origins = [cloudflare.SplitDNSOrigin {
    protocol = option("allowed_protocol", default="https")
    hostname = option("allowed_hostname", default="traefik-mid.sghd.io")
    port = option("allowed_port", default=443)
}] if option("allow", default=False) else []
_services = [
    base.Service {name = "safe", protocol = "http", port = 80, internal_hostname = "safe.internal.lan", public_hostname = "safe.sghd.io"}
    base.Service {name = "first", protocol = _scheme, port = _port, internal_hostname = _hostname if _mode != "fallback" else None, public_hostname = "first.sghd.io"}
    base.Service {name = "skipped", protocol = "https", port = 443, internal_hostname = "unapproved.sghd.io", distribution = "unifi_only"}
    base.Service {name = "second", protocol = _scheme, port = _port, internal_hostname = _hostname if _mode != "fallback" else None, public_hostname = "second.sghd.io"}
]
_config = cloudflare.CloudflareConfig {
    zone_name = _zone
    account_id = "test-account"
    split_dns_origins = _origins
    tunnels = {
        "AA:BB:CC:DD:EE:FF": cloudflare.CloudflareTunnel {
            tunnel_name = "edge-server"
            mac_address = "AA:BB:CC:DD:EE:FF"
            services = [
                {public_hostname = "safe.sghd.io", local_service_url = "http://safe.internal.lan:80"}
                {public_hostname = "first.sghd.io", local_service_url = _url, no_tls_verify = True, path_prefix = "/first"}
                {public_hostname = "second.sghd.io", local_service_url = option("second_url", default=_url), path_prefix = "/second"}
            ]
        }
    }
} if _mode == "explicit" else None

cf_output = cf_gen.generate_cloudflare_config(_config) if _mode == "explicit" else cf_gen.transform_service(_services[1], "edge-server", "sghd.io", _zone, False, split_dns_origins=_origins) if _mode == "transform" else cf_gen.transform_tunnel_services(_services, "edge-server", "sghd.io", _zone, True, split_dns_origins=_origins) if _mode == "list" else cf_gen.generate_cloudflare_from_entities([
    base.Entity {
        friendly_hostname = "edge-server"
        domain = "internal.lan"
        endpoints = [{mac_address = "AA-BB-CC-DD-EE-FF"}]
        services = _services
    }
], _zone, "test-account", True, "sghd.io", split_dns_origins=_origins)
