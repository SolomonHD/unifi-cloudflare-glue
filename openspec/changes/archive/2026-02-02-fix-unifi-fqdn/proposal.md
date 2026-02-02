# Proposal: Fix UniFi DNS Record FQDN Creation

## Problem

The UniFi DNS A-record resource in `terraform/modules/unifi-dns/main.tf` (line 132) creates DNS records using only the hostname without the domain suffix. This results in incomplete DNS records being created in the UniFi controller.

**Current broken behavior:**
- A-record resource uses: `name = each.value.hostname` (line 132)
- Results in DNS records like "test-14fqf" instead of "test-14fqf.sghd.io"
- The `local.dns_records` map (lines 100-106) provides both `hostname` and `domain` fields, but only `hostname` is used

**Observable issue:**
- Integration tests create UniFi DNS records with incomplete hostnames
- UniFi controller UI displays only the hostname portion in the Domain Name field
- This differs from CNAME records which correctly use full FQDN (line 178)

## Solution

Modify the A-record resource `name` field to concatenate `hostname` and `domain` fields into a full FQDN, matching the pattern already used for CNAME records.

**Change location:** `terraform/modules/unifi-dns/main.tf`, line 132

**Current:**
```terraform
name    = each.value.hostname
```

**New:**
```terraform
name    = "${each.value.hostname}.${each.value.domain}"
```

This matches the existing CNAME pattern on line 178: `record = "${each.value.hostname}.${each.value.domain}"`

## Scope

**Affected capability:**
- UniFi DNS deployment (A-record creation)

**Files to modify:**
- `terraform/modules/unifi-dns/main.tf` (line 132 only)

**No changes needed to:**
- `local.dns_records` map structure (already provides both fields)
- CNAME record resource (already correct)
- Domain extraction logic in locals
- Test configuration generation

## Impact

- UniFi DNS A-records will be created with complete FQDNs
- Integration tests will show proper domain names in success messages
- Consistency with existing CNAME record implementation
- UniFi controller will display full domain names in DNS record listings

## Acceptance Criteria

- [ ] A-record resource `name` uses `"${each.value.hostname}.${each.value.domain}"`
- [ ] UniFi controller shows DNS records with full FQDNs (e.g., "test-14fqf.sghd.io")
- [ ] Integration tests create properly formatted FQDN records
- [ ] Terraform plan/apply succeeds without errors
- [ ] Pattern matches the CNAME implementation on line 178
