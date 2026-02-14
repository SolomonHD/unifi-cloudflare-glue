# OpenSpec Prompt: Troubleshooting Guide

## Context

Users encounter errors during installation, configuration, and deployment but lack a systematic troubleshooting resource. A comprehensive guide with decision trees and solutions for common issues will reduce support burden and improve user experience.

## Goal

Create a comprehensive troubleshooting guide with decision trees, common error messages, solutions, and debugging techniques for all components (Dagger, Terraform, KCL, UniFi, Cloudflare).

## Scope

### In Scope

1. Create [`docs/troubleshooting.md`](../../docs/troubleshooting.md) with systematic guide
2. Document common errors for each component:
   - Dagger module errors
   - Terraform errors (init, plan, apply)
   - KCL validation errors
   - UniFi API errors
   - Cloudflare API errors
   - State management errors
3. Add decision trees for systematic debugging
4. Include diagnostics commands for each component
5. Add FAQ section
6. Link from main README

### Out of Scope

- Detailed debugging of user-specific network issues
- Terraform internals documentation
- KCL language bugs (link to KCL issue tracker)
- Provider-specific bugs (link to provider repos)

## Desired Behavior

### Documentation Structure: docs/troubleshooting.md

```markdown
# Troubleshooting Guide

## Quick Diagnostics

Commands to check system health

## Common Errors By Component

### Dagger Module Errors

#### "Module not found"
**Symptoms:** Cannot find unifi-cloudflare-glue module
**Solution:** Check installation, verify version

#### "Secret parameter error"
**Symptoms:** Cannot read secret value
**Solution:** Check env:PREFIX syntax

### Terraform Errors

#### "Backend initialization failed"
**Symptoms:** terraform init fails
**Solution:** Check backend config, credentials

#### "State lock timeout"
**Symptoms:** Cannot acquire state lock
**Solution:** Check for stale locks, wait or force-unlock

#### "Provider authentication failed"
**Symptoms:** Cannot authenticate with UniFi/Cloudflare
**Solution:** Verify credentials, check network access

### KCL Validation Errors

#### "MAC address format invalid"
**Symptoms:** MAC validation fails
**Solution:** Use aa:bb:cc:dd:ee:ff format

#### "DNS loop detected"
**Symptoms:** Cloudflare points to external hostname
**Solution:** Use internal (.local/.lan) hostnames

### UniFi Controller Errors

#### "TLS certificate verify failed"
**Symptoms:** Cannot connect to controller
**Solution:** Use --unifi-insecure for self-signed certs

#### "API key invalid"
**Symptoms:** 401 authentication error
**Solution:** Verify API key, check key hasn't expired

### Cloudflare API Errors

#### "Zone not found"
**Symptoms:** Cannot find DNS zone
**Solution:** Verify zone name, check API token permissions

#### "Tunnel creation failed"
**Symptoms:** Cannot create tunnel
**Solution:** Check account permissions, verify account ID

## Decision Trees

### Deployment Failing?

```
Deployment fails
├─ At what stage?
   ├─ Configuration generation
   │  └─ KCL validation → See KCL Errors
   ├─ Terraform init
   │  └─ Backend issues → See Terraform Init
   ├─ Terraform plan/apply
   │  ├─ UniFi → See UniFi Errors
   │  └─ Cloudflare → See Cloudflare Errors
   └─ Dagger module
      └─ See Dagger Errors
```

### State Management Issues?

### Authentication Failures?

## Diagnostics Commands

### Check Dagger
### Check Terraform
### Check KCL
### Verify Network Access
### Test API Credentials

## FAQ

### Q: How do I reset state?
### Q: Can I use multiple tunnels per device?
### Q: Why does DNS loop validation fail?
### Q: How do I debug KCL schemas?

## Getting Help

- GitHub Issues
- Discord/Community
- Commercial Support
```

## Common Error Messages to Document

### Dagger

- "Module not found"
- "Secret parameter must use env: prefix"
- "Container execution failed"
- "Function not found"

### Terraform

- "Error: Backend initialization failed"
- "Error: Error acquiring the state lock"
- "Error: Failed to query available provider packages"
- "Error: configuring UniFi provider"
- "Error: configuring Cloudflare provider"

### KCL

- "CompileError: Name is not defined"
- "ValidationError: MAC address format invalid"
- "ValidationError: DNS loop detected"
- "ValidationError: Duplicate MAC address"

### UniFi

- "URLError: SSL: CERTIFICATE_VERIFY_FAILED"
- "401 Unauthorized"
- "Connection refused"
- "Timeout waiting for UniFi controller"

### Cloudflare

- "Zone not found"
- "Insufficient permissions"
- "Tunnel name already exists"
- "Rate limit exceeded"

## Diagnostics Commands to Include

```bash
# Check Dagger
dagger version
dagger call hello
dagger call -m unifi-cloudflare-glue --help

# Check Terraform version
terraform version

# Check KCL
kcl version
kcl run main.k  # Validate syntax

# Test network access
curl -k https://unifi.local:8443/status
curl https://api.cloudflare.com/client/v4/user/tokens/verify \
    -H "Authorization: Bearer $CF_TOKEN"

# Check state backend access
aws s3 ls s3://my-bucket/  # S3 backend
az storage blob list ...    # Azure backend
gsutil ls gs://my-bucket/   # GCS backend
```

## Constraints & Assumptions

### Constraints

- Solutions must be actionable and specific
- Link to official docs for detailed issues
- Keep updated as new versions introduce changes
- Focus on errors users actually encounter

### Assumptions

- Users have basic command-line proficiency
- Users can read error messages
- Users want self-service before asking for help
- Most issues are configuration errors, not bugs

## Acceptance Criteria

- [ ] [`docs/troubleshooting.md`](../../docs/troubleshooting.md) created with comprehensive guide
- [ ] Common errors documented for each component
- [ ] Solutions provided for each error type
- [ ] Decision trees for systematic debugging
- [ ] Diagnostics commands section included
- [ ] FAQ section with 10+ common questions
- [ ] All error messages include:
  - Symptoms (what user sees)
  - Cause (why it happens)
  - Solution (how to fix)
  - Prevention (how to avoid)
- [ ] Links to external resources (GitHub issues, official docs)
- [ ] Links added from main README
- [ ] Real error messages (copied from actual errors, not made up)

## Expected Files/Areas Touched

- `docs/troubleshooting.md` (new)
- `docs/README.md` (update index)
- `README.md` (add troubleshooting link)
- Other docs (add "See Troubleshooting" links from relevant sections)

## Dependencies

- Prompt 01 (docs structure must exist)
- All other prompts (reference their documentation in solutions)

## Notes

- Collect real error messages from issues/support requests
- Update as new errors are discovered
- Decision trees help users self-diagnose
- Link to GitHub issues for known bugs
- Emphasize checking basics (credentials, network, versions) first
