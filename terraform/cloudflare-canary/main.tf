# The runtime supplies qualified remote state and writer fencing before invocation.
data "cloudflare_zone" "sandbox" {
  zone_id = var.zone_id
}

locals {
  namespace = "ci.solomonhd.ai"
  records = {
    txt = {
      type    = "TXT"
      content = var.txt_value
    }
    cname = {
      type    = "CNAME"
      content = var.cname_target
    }
  }
}

resource "cloudflare_dns_record" "canary" {
  for_each = local.records

  zone_id = var.zone_id
  name    = "${var.run_prefix}.${each.key}.${local.namespace}"
  type    = each.value.type
  content = each.value.content
  ttl     = 60
  proxied = false
  comment = var.run_prefix

  lifecycle {
    precondition {
      condition     = data.cloudflare_zone.sandbox.name == "solomonhd.ai"
      error_message = "Canary records are restricted to the existing solomonhd.ai zone."
    }
  }
}
