import .generators.cloudflare as cf_gen

allowed = cf_gen.validate_no_dns_loop(option("url"), "example.com")
