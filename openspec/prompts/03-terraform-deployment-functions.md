# OpenSpec Change Prompt: Terraform Deployment Functions

## Context

KCL generation functions are working. Now we need to implement Terraform deployment functions that apply the generated JSON configurations to UniFi and Cloudflare. These functions must handle sensitive credentials securely using Dagger's `Secret` type.

**Critical requirement**: All API keys, tokens, and passwords must use `dagger.Secret` type, never plain strings.

## Goal

Implement Dagger functions to deploy infrastructure via Terraform, with proper secret handling for UniFi and Cloudflare credentials.

## Scope

**In scope:**
- Add `deploy_unifi` function for UniFi DNS deployment
- Add `deploy_cloudflare` function for Cloudflare Tunnel deployment
- Add `deploy` function that orchestrates both (UniFi first, then Cloudflare)
- Add `destroy` function for emergency teardown
- Containerize Terraform (no local Terraform required)
- Secure credential handling via Dagger Secrets

**Out of scope:**
- Integration testing with ephemeral resources (next prompt)
- Modifying Terraform modules themselves
- State backend configuration (use local or existing backend)

## Desired Behavior

1. **`deploy_unifi`**:
   - Takes source directory with generated UniFi JSON
   - Takes UniFi credentials as Secrets
   - Runs `terraform apply` for UniFi DNS module
   - Returns deployment status/output

2. **`deploy_cloudflare`**:
   - Takes source directory with generated Cloudflare JSON
   - Takes Cloudflare credentials as Secrets
   - Runs `terraform apply` for Cloudflare Tunnel module
   - Returns deployment status/output

3. **`deploy`** (orchestration):
   - Runs KCL generation (calls previous functions)
   - Deploys UniFi first (creates local DNS)
   - Deploys Cloudflare second (tunnels point to now-resolvable hostnames)
   - Returns combined deployment status

4. **`destroy`**:
   - Destroys Cloudflare resources first (avoid DNS loops)
   - Destroys UniFi resources second
   - Useful for emergencies or cleanup

## Constraints & Assumptions

- Terraform modules exist at `terraform/modules/unifi-dns/` and `terraform/modules/cloudflare-tunnel/`
- **All sensitive inputs must use `dagger.Secret` type**:
  - UniFi API key/username/password
  - Cloudflare API token
  - Any other credentials
- Functions must be async
- Return `str` for CLI-friendly status messages
- Use official Terraform Docker image or HashiCorp packages
- Support passing variables via `-var-file` or `-var`

## Required Secrets

### UniFi Module (Mutually Exclusive Auth)
**Option 1: API Key (Preferred)**
- `unifi_api_key`: API key for UniFi Controller (Secret)
- `unifi_url`: UniFi Controller URL (string, not secret)

**Option 2: Username/Password**
- `unifi_username`: Username for UniFi Controller (Secret)
- `unifi_password`: Password for UniFi Controller (Secret)
- `unifi_url`: UniFi Controller URL (string, not secret)

### Cloudflare Module
- `cloudflare_token`: Cloudflare API Token (Secret)
- `cloudflare_account_id`: Cloudflare Account ID (string, not secret)
- `zone_name`: DNS zone name (string, not secret)

## Terraform State Backend

Functions must support both:
- **Local state**: Default for testing/single-user
- **Remote state**: For team environments (S3, Terraform Cloud, etc.)

Backend configuration should be passed via standard Terraform means (backend config files or environment variables).

## Acceptance Criteria

- [ ] `deploy_unifi` function exists:
  - Parameters (mutually exclusive auth methods):
    - `source: dagger.Directory` (required) - contains unifi.json
    - `unifi_url: str` (required) - UniFi Controller URL
    - `api_url: str` (optional) - UniFi API URL (defaults to unifi_url)
    - `unifi_api_key: dagger.Secret` (optional) - API key auth (preferred)
    - `unifi_username: dagger.Secret` (optional) - Username for user/pass auth
    - `unifi_password: dagger.Secret` (optional) - Password for user/pass auth
  - Validation: Either `unifi_api_key` OR (`unifi_username` AND `unifi_password`) must be provided
  - Returns: `str` - deployment status
  - Runs in Terraform container
  - Applies `terraform/modules/unifi-dns/`
  - Supports both local and remote Terraform state backends

- [ ] `deploy_cloudflare` function exists:
  - Parameters:
    - `source: dagger.Directory` (required) - contains cloudflare.json
    - `cloudflare_token: dagger.Secret` (required)
    - `cloudflare_account_id: str` (required)
    - `zone_name: str` (required)
  - Returns: `str` - deployment status
  - Runs in Terraform container
  - Applies `terraform/modules/cloudflare-tunnel/`

- [ ] `deploy` function exists:
  - Parameters: All of the above (combines both modules)
  - Returns: `str` - combined deployment status
  - Orchestrates in correct order: KCL gen → UniFi → Cloudflare

- [ ] `destroy` function exists:
  - Parameters: Same credentials as deploy
  - Returns: `str` - destruction status
  - Order: Cloudflare first, then UniFi (reverse of deploy)

- [ ] All functions:
  - Use `Annotated[type, Doc("...")]` for parameters
  - Have comprehensive docstrings
  - Return clear status messages (✓ Success or ✗ Failed)
  - Handle errors gracefully

- [ ] Example usage works:
  ```bash
  # Deploy UniFi with API key (preferred)
  dagger call deploy-unifi \
    --source=. \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-url=https://unifi.local:8443

  # Deploy UniFi with username/password
  dagger call deploy-unifi \
    --source=. \
    --unifi-username=env:UNIFI_USER \
    --unifi-password=env:UNIFI_PASS \
    --unifi-url=https://unifi.local:8443

  # Deploy Cloudflare only
  dagger call deploy-cloudflare \
    --source=. \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com

  # Full deployment with API key
  dagger call deploy \
    --source=. \
    --unifi-api-key=env:UNIFI_API_KEY \
    --unifi-url=https://unifi.local:8443 \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id=xxx \
    --zone-name=example.com
  ```

## Files to Modify

**Modify:**
- `src/unifi_cloudflare_glue/main.py` - add deployment functions

## Dependencies

- Requires change 01 (Dagger module scaffolding)
- Requires change 02 (KCL generation functions) for `deploy` orchestration
- Existing Terraform modules at `terraform/modules/`

## Example Implementation Pattern

```python
@function
async def deploy_unifi(
    self,
    source: Annotated[dagger.Directory, Doc("Source directory with unifi.json")],
    unifi_api_key: Annotated[dagger.Secret, Doc("UniFi API key")],
    unifi_url: Annotated[str, Doc("UniFi Controller URL")],
) -> str:
    """
    Deploy UniFi DNS configuration.
    
    Returns:
        ✓ Success message with applied resources
        ✗ Error message if deployment fails
    """
    # Get secret value
    api_key = await unifi_api_key.plaintext()
    
    # Create Terraform container
    # Mount source directory
    # Run terraform apply with vars
    # Return status
```

## Security Notes

- **Never log secret values**
- Use `await secret.plaintext()` only when needed for Terraform
- Terraform will receive secrets via environment variables or var files
- Consider using `TF_VAR_*` environment variables for sensitive values

## Reference

- Terraform modules at `terraform/modules/unifi-dns/` and `terraform/modules/cloudflare-tunnel/`
- Dagger Secret documentation: https://docs.dagger.io/api/secrets/
- Terraform Docker images: https://hub.docker.com/r/hashicorp/terraform/

## Open Questions

None - straightforward implementation following Dagger security patterns.
