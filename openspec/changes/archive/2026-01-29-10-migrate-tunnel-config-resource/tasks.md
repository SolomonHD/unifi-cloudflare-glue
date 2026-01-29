# Tasks: Migrate cloudflare_tunnel_config Resource

## Implementation Tasks

### Task 1: Update Resource Name and Config Syntax

**Description:** Rename the resource and convert config from block to attribute syntax.

**File:** `terraform/modules/cloudflare-tunnel/main.tf`

**Changes:**
- [x] Change resource type from `cloudflare_tunnel_config` to `cloudflare_zero_trust_tunnel_cloudflared_config`
- [x] Change `config {` to `config = {`

**Verification:**
- Run `terraform fmt` to verify syntax
- Run `terraform validate` to check for errors

---

### Task 2: Convert Ingress Rules to List Syntax

**Description:** Replace dynamic ingress_rule blocks with for expression.

**File:** `terraform/modules/cloudflare-tunnel/main.tf`

**Changes:**
- [x] Remove `dynamic "ingress_rule"` block
- [x] Add `ingress = [` list with for expression
- [x] Map `svc.public_hostname` to hostname field
- [x] Map `svc.local_service_url` to service field

**Before:**
```hcl
dynamic "ingress_rule" {
  for_each = each.value.services
  content {
    hostname = ingress_rule.value.public_hostname
    service  = ingress_rule.value.local_service_url
    ...
  }
}
```

**After:**
```hcl
ingress = [
  for svc in each.value.services : {
    hostname = svc.public_hostname
    service  = svc.local_service_url
    ...
  }
]
```

**Verification:**
- Ensure for expression iterates over `each.value.services`
- Verify field mappings are correct

---

### Task 3: Convert Origin Request to Conditional Expression

**Description:** Replace dynamic origin_request block with conditional expression.

**File:** `terraform/modules/cloudflare-tunnel/main.tf`

**Changes:**
- [x] Remove `dynamic "origin_request"` block
- [x] Add `origin_request` field with ternary operator:
  ```hcl
  origin_request = svc.no_tls_verify ? {
    no_tls_verify = true
  } : null
  ```

**Before:**
```hcl
dynamic "origin_request" {
  for_each = ingress_rule.value.no_tls_verify ? [true] : []
  content {
    no_tls_verify = true
  }
}
```

**After:**
```hcl
origin_request = svc.no_tls_verify ? {
  no_tls_verify = true
} : null
```

**Verification:**
- Test with `no_tls_verify = true` - should include origin_request object
- Test with `no_tls_verify = false` - should be null

---

### Task 4: Add Catch-All Rule with Concat

**Description:** Append the catch-all 404 rule using concat function.

**File:** `terraform/modules/cloudflare-tunnel/main.tf`

**Changes:**
- [x] Wrap ingress list in `concat()`
- [x] Add catch-all rule as second argument:
  ```hcl
  [{ service = "http_status:404" }]
  ```

**Before:**
```hcl
config {
  ingress = [for svc in each.value.services : { ... }]
  ingress_rule {
    service = "http_status:404"
  }
}
```

**After:**
```hcl
config = {
  ingress = concat(
    [for svc in each.value.services : { ... }],
    [{ service = "http_status:404" }]
  )
}
```

**Verification:**
- Ensure catch-all is last in the list
- Test that empty services list still produces valid config with just catch-all

---

### Task 5: Verify Tunnel ID Reference

**Description:** Ensure tunnel_id references the correct resource.

**File:** `terraform/modules/cloudflare-tunnel/main.tf`

**Changes:**
- [x] Verify `tunnel_id = cloudflare_zero_trust_tunnel_cloudflared.this[each.key].id`
- [x] Ensure reference matches the already-migrated tunnel resource

**Note:** This should already be correct from Prompt 09, but verify it hasn't been broken.

---

### Task 6: Format and Validate

**Description:** Run Terraform formatting and validation.

**Commands:**
```bash
cd terraform/modules/cloudflare-tunnel
terraform fmt
terraform validate
```

**Expected Results:**
- [x] `terraform fmt` makes no changes (or acceptable formatting changes)
- [x] `terraform validate` passes with no errors for the tunnel config resource (errors for other resources are expected - they have separate migration prompts)

---

### Task 7: Create Test Plan

**Description:** Generate a Terraform plan to verify the changes.

**Prerequisites:**
- Valid Cloudflare API token
- Existing cloudflare_tunnel_config resources to migrate

**Commands:**
```bash
cd examples/homelab-media-stack/terraform
terraform init
terraform plan -out=tfplan
```

**Expected Results:**
- [ ] Plan shows resource replacement (destroy + create) for tunnel config
- [ ] No errors during planning
- [ ] Tunnel resources themselves should show no changes

---

## Validation Checklist

- [x] Resource type is `cloudflare_zero_trust_tunnel_cloudflared_config`
- [x] Config uses attribute syntax (`config = {`)
- [x] Ingress uses list with for expression
- [x] Origin request uses conditional expression
- [x] Catch-all 404 rule is included via concat
- [x] Tunnel ID references correct resource
- [x] `terraform fmt` passes
- [x] `terraform validate` passes for tunnel config resource
- [ ] Plan shows expected changes (requires Cloudflare credentials)

## Dependencies

- Prompt 09 (tunnel resource migration) must be completed ✓
- Cloudflare provider version ~> 5.0 must be configured ✓

## Blocked By

None - ready to implement.

## Blocks

- Prompt 11 (DNS record migration) - should be applied after this change
