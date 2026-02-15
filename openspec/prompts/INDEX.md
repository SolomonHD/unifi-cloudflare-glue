# OpenSpec Prompt Index

## Active Prompts

| # | Change ID | Description | Status |
|---|-----------|-------------|--------|
| 10 | fix-terraform-module-loading | Fix embedded Terraform module loading to use current_module().source() | Ready |
| 11 | add-site-field-to-unifi-generator | Add site field to UniFi generator output to fix Terraform errors | Ready |
| 12 | improve-validation-error-handling | Improve error handling when KCL validation fails | Ready |
| 13 | add-generator-output-validation-tests | Add tests to validate generator output matches Terraform expectations | Ready (depends on #11) |

## Archive

See [openspec/changes/INDEX.md](../changes/INDEX.md) for completed changes.

## Next Prompt

**NEXT.md** → [`11-add-site-field-to-unifi-generator.md`](11-add-site-field-to-unifi-generator.md)

## Prompt Dependencies

- Prompt 13 should be implemented **after** prompt 11, as it tests the fixed generator output
- Prompts 11 and 12 are independent and can be implemented in either order
