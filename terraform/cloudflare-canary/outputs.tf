output "records" {
  description = "Non-secret exact identities for API verification and protected run evidence."
  value = {
    for key, record in cloudflare_dns_record.canary : key => {
      id      = record.id
      name    = record.name
      type    = record.type
      zone_id = record.zone_id
      proxied = record.proxied
    }
  }
}
