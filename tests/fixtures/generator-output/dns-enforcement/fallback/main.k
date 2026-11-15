import .schemas.base
import .generators.cloudflare as cf_gen

cf_output = cf_gen.generate_cloudflare_from_entities([
    base.Entity {
        friendly_hostname = "edge-server"
        domain = "internal.lan"
        endpoints = [{mac_address = "AA:BB:CC:DD:EE:FF"}]
        services = [{name = "app", port = 8080, protocol = "http", public_hostname = "app.example.com"}]
    }
], option("zone", default="example.com"), "test-account", False, option("domain", default="example.com"))
