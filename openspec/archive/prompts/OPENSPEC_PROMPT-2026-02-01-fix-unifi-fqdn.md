# OpenSpec Prompt: Fix UniFi DNS Record FQDN Creation

## Context

The UniFi DNS Terraform module at [`terraform/modules/unifi-dns/main.tf`](../terraform/modules/unifi-dns/main.tf) creates DNS A-records using the `unifi_dns_record` resource (line 128). However, the current implementation only uses the hostname without the domain suffix, creating incomplete DNS records.

**Current broken behavior** (line 132):
```terraform
resource "unifi_dns_record" "dns_record" {
  for_each = local.dns_records

  site    = local.effective_config.site
  name    = each.value.hostname  # ❌ Only "test-14fqf", missing domain
  record  = each.value.ip
  type    = "A"
  enabled = true
}
```

The `local.dns_records` map (lines 100-106) contains both `hostname` and `domain` fields, but only `hostname` is used in the resource name.

**Observable issue:**
When running integration tests, UniFi DNS records are created as just "test-14fqf" instead of the expected FQDN "test-14fqf.sghd.io". This is visible in the UniFi controller UI where the Domain Name field shows only the hostname part.

## Goal

Fix the UniFi DNS A-record resource to create full FQDN records by concatenating the hostname and domain fields.

## Scope

**In scope:**
- Modify the `unifi_dns_record` resource for A-records (line 132) to use full FQDN
- Ensure the fix uses both `hostname` and `domain` from `local.dns_records`
- Verify that the existing `domain` extraction logic (line 103) remains unchanged

**Out of scope:**
- Changing the CNAME record resource (line 173-181) - this already correctly uses FQDN on line 178
- Modifying the `local.dns_records` map structure (lines 100-106)
- Changing the domain field extraction logic in locals (line 41, 56, 103)
- Altering the test configuration generation in [`src/main/main.py`](../src/main/main.py:812-829)

## Desired Behavior

### Fix the A-record Resource

**Replace line 132:**
```terraform
name    = each.value.hostname  # ❌ Old: incomplete
```

**With:**
```terraform
name    = "${each.value.hostname}.${each.value.domain}"  # ✓ New: full FQDN
```

### Full Context (lines 128-136):
```terraform
resource "unifi_dns_record" "dns_record" {
  for_each = local.dns_records

  site    = local.effective_config.site
  name    = "${each.value.hostname}.${each.value.domain}"  # ✓ FIXED
  record  = each.value.ip
  type    = "A"
  enabled = true
}
```

### Expected Result

After the fix, when `test_integration` creates a UniFi DNS record with:
- `hostname`: "test-14fqf"
- `domain`: "sghd.io"

The UniFi controller should show:
- **Domain Name**: "test-14fqf.sghd.io" ✓ (full FQDN)
- **Type**: Host (A)
- **IP Address**: 192.168.x.x

## Constraints & Assumptions

- The `local.dns_records` map already contains both `hostname` and `domain` fields
- The CNAME records (line 178) already use this pattern correctly: `record = "${each.value.hostname}.${each.value.domain}"`
- UniFi DNS records support full FQDN in the `name` field
- The domain field in `local.dns_records` comes from the device configuration or defaults to `local.effective_config.default_domain`
- String interpolation in Terraform uses `"${var.a}.${var.b}"` syntax

## Acceptance Criteria

- [ ] A-record resource `name` field uses full FQDN: `"${each.value.hostname}.${each.value.domain}"`
- [ ] UniFi controller shows DNS records with complete domain names (e.g., "test-14fqf.sghd.io")
- [ ] Integration tests create properly formatted FQDN records
- [ ] The fix matches the existing CNAME pattern on line 178
- [ ] No changes to the `local.dns_records` map structure
- [ ] Terraform plan/apply succeeds without errors

## Reference

**Files to modify:**
- [`terraform/modules/unifi-dns/main.tf`](../terraform/modules/unifi-dns/main.tf): Line 132

**Related code for pattern reference:**
- Line 178 (CNAME records): Already uses `"${each.value.hostname}.${each.value.domain}"` correctly
- Lines 100-106 (`local.dns_records`): Provides both `hostname` and `domain` fields
- Lines 812-829 in [`src/main/main.py`](../src/main/main.py): Test config generation

**Testing:**
After the fix, run:
```bash
dagger call test-integration \
    --source=. \
    --cloudflare-zone=test.example.com \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --unifi-url=https://unifi.local:8443 \
    --api-url=https://unifi.local:8443 \
    --unifi-api-key=env:UNIFI_API_KEY
```

Expected outcome:
- UniFi DNS records created with full FQDN: "test-XXXXX.example.com"
- UniFi controller UI shows complete domain names
- Phase 3 success: "✓ Created UniFi DNS record: test-XXXXX.example.com"
