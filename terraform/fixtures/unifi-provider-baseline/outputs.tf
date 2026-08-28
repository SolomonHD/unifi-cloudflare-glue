output "sandbox_zone" {
  description = "Run-specific namespace used by every disposable record."
  value       = local.sandbox_zone
}

output "a_record_names" {
  description = "Names of the disposable A records."
  value       = sort([for record in unifi_dns_record.a : record.name])
}

output "cname_record_names" {
  description = "Names of the disposable CNAME records."
  value       = sort([for record in unifi_dns_record.cname : record.name])
}

output "record_count" {
  description = "Total number of disposable DNS records."
  value       = length(unifi_dns_record.a) + length(unifi_dns_record.cname)
}
