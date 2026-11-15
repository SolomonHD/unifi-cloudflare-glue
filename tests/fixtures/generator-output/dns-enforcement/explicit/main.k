import .schemas.cloudflare
import .generators.cloudflare as cf_gen

cf_output = cf_gen.generate_cloudflare_config(cloudflare.CloudflareConfig {
    zone_name = option("zone", default="example.com")
    account_id = "test-account"
    tunnels = {
        "AA:BB:CC:DD:EE:FF": cloudflare.CloudflareTunnel {
            tunnel_name = "edge-server"
            mac_address = "AA:BB:CC:DD:EE:FF"
            services = [
                {public_hostname = "safe.example.com", local_service_url = "http://safe.internal.lan:80"}
                {
                    public_hostname = "app.example.com"
                    local_service_url = option("url", default="https://app.example.com:443/path")
                    no_tls_verify = True
                    path_prefix = "/app"
                }
            ]
        }
    }
})
