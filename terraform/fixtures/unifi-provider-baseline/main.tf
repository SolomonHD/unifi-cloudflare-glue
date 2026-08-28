locals {
  sandbox_zone = "unifi-poc-${var.run_id}.solomonhd.ai"

  a_records = {
    for index in range(var.a_record_count) : format("a-%03d", index + 1) => {
      name = format("a-%03d.%s", index + 1, local.sandbox_zone)
      record = (
        index == 0 && var.update_first_record
        ? "10.255.255.254"
        : cidrhost("10.255.0.0/16", index + 10)
      )
    }
  }

  cname_records = {
    for index in range(var.cname_record_count) : format("cname-%03d", index + 1) => {
      name   = format("cname-%03d.%s", index + 1, local.sandbox_zone)
      record = local.a_records[format("a-%03d", index % var.a_record_count + 1)].name
    }
  }
}

resource "unifi_dns_record" "a" {
  for_each = local.a_records

  site    = var.site
  name    = each.value.name
  record  = each.value.record
  type    = "A"
  enabled = true

  lifecycle {
    precondition {
      condition     = endswith(each.value.name, ".${local.sandbox_zone}")
      error_message = "A record escaped the run-specific sandbox namespace."
    }
  }
}

resource "unifi_dns_record" "cname" {
  for_each = local.cname_records

  site    = var.site
  name    = each.value.name
  record  = each.value.record
  type    = "CNAME"
  enabled = true

  lifecycle {
    precondition {
      condition = (
        endswith(each.value.name, ".${local.sandbox_zone}") &&
        endswith(each.value.record, ".${local.sandbox_zone}")
      )
      error_message = "CNAME record or target escaped the run-specific sandbox namespace."
    }
  }
}
