# Tasks: Fix UniFi DNS Record FQDN Creation

## Implementation Tasks

- [x] Modify `terraform/modules/unifi-dns/main.tf` line 132 to use full FQDN
  - Change from: `name = each.value.hostname`
  - Change to: `name = "${each.value.hostname}.${each.value.domain}"`

## Validation Tasks

- [x] Run `terraform fmt` on modified file
- [x] Run `terraform validate` in module directory
- [x] Verify the pattern matches CNAME implementation (line 178)

## Testing Tasks

- [ ] Run integration test with `--no-cache` to verify DNS records
- [ ] Confirm UniFi controller shows full FQDN in Domain Name field
- [ ] Verify test output shows complete FQDN in success messages

## Dependencies

- No blocking dependencies (single-line fix)
- All required fields (`hostname`, `domain`) already available in `local.dns_records`
