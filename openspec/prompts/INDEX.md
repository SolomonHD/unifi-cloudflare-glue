# OpenSpec Prompt Index: Real Integration Test Implementation

This directory contains OpenSpec prompts to transform the `test_integration` function from a simulated/mock test into a real integration test that actually creates, validates, and cleans up Cloudflare and UniFi resources.

## Prompt Sequence

| Order | Prompt | Description |
|-------|--------|-------------|
| 01 | [01-fix-test-config-generation.md](./01-fix-test-config-generation.md) | Fix test config generation to output proper Terraform-compatible JSON |
| 02 | [02-implement-cloudflare-creation.md](./02-implement-cloudflare-creation.md) | Implement real Cloudflare tunnel and DNS creation via Terraform |
| 03 | [03-implement-unifi-creation.md](./03-implement-unifi-creation.md) | Implement real UniFi DNS record creation via Terraform |
| 04 | [04-implement-real-validation.md](./04-implement-real-validation.md) | Implement real validation via Cloudflare and UniFi API calls |
| 05 | [05-implement-real-cleanup.md](./05-implement-real-cleanup.md) | Implement real cleanup via terraform destroy |

## Execution Order

Prompts must be executed in order (01 → 05) as each builds upon the previous:

1. **Prompt 01** creates the foundation - proper JSON config format
2. **Prompt 02** adds Cloudflare resource creation
3. **Prompt 03** adds UniFi resource creation
4. **Prompt 04** adds real validation (depends on 02 and 03)
5. **Prompt 05** adds proper cleanup (depends on 02 and 03)

## Target File

All changes are to `src/main/main.py` in the `test_integration` function (lines 752-1044).

## Expected Outcome

After all prompts are implemented, `test_integration` will:
- ✅ Generate proper JSON configs for both Terraform modules
- ✅ Actually create Cloudflare tunnels and DNS records
- ✅ Actually create UniFi DNS records
- ✅ Validate resources exist via API queries
- ✅ Actually destroy all resources during cleanup
- ✅ Provide accurate test results based on real resource state
