import .schemas.base
import .generators.cloudflare as cf_gen

_service = base.Service {
    name = "app"
    port = 443
    protocol = "https"
    internal_hostname = option("hostname", default="app.example.com")
    public_hostname = "app.example.com"
    distribution = option("distribution", default="both")
}
cf_output = cf_gen.generate_cloudflare_from_entities([
    base.Entity {
        friendly_hostname = "edge-server"
        domain = "internal.lan"
        endpoints = [{mac_address = "AA-BB-CC-DD-EE-FF"}]
        services = [_service]
    }
], option("zone", default="example.com"), "test-account", True)
