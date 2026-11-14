import .schemas.base
import .generators.cloudflare as cf_gen

_service = base.Service {
    name = "app"
    port = 443
    protocol = "https"
    internal_hostname = option("hostname", default="app.example.com") if not option("fallback", default=False) else None
    public_hostname = "app.example.com"
}
_zone = option("zone", default="example.com")
_domain = option("domain", default="internal.lan")
cf_output = cf_gen.transform_tunnel_services([_service], "edge-server", _domain, _zone, False) if option("list", default=False) else cf_gen.transform_service(_service, "edge-server", _domain, _zone, False)
