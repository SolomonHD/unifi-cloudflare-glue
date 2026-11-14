import .schemas.base
import .schemas.unifi
import .generators.cloudflare as cf_gen
import .generators.unifi as unifi_gen

_entity = base.Entity {
    friendly_hostname = "no-nics"
    domain = "internal.lan"
    endpoints = []
    services = [base.Service {name = "app", port = 80, protocol = "http", distribution = "both"}]
}
cf_output = cf_gen.generate_cloudflare_from_entities([_entity], "example.com", "test-account")
if option("unifi", default=False):
    unifi_output = unifi_gen.transform_entity(unifi.UniFiEntity {
        friendly_hostname = "no-nics"
        domain = "internal.lan"
        endpoints = []
    })
