# Troubleshooting Guide

This guide provides comprehensive troubleshooting assistance for the unifi-cloudflare-glue project. Find solutions for common issues with Dagger, Terraform, KCL, UniFi Controller, and Cloudflare.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Errors By Component](#common-errors-by-component)
  - [Dagger Module Errors](#dagger-module-errors)
  - [Terraform Errors](#terraform-errors)
  - [KCL Validation Errors](#kcl-validation-errors)
  - [UniFi Controller Errors](#unifi-controller-errors)
  - [Cloudflare API Errors](#cloudflare-api-errors)
- [Decision Trees](#decision-trees)
  - [Deployment Failure Decision Tree](#deployment-failure-decision-tree)
  - [Authentication Failure Decision Tree](#authentication-failure-decision-tree)
  - [State Management Issues Decision Tree](#state-management-issues-decision-tree)
- [Diagnostics Commands](#diagnostics-commands)
  - [Dagger Verification](#dagger-verification)
  - [Terraform Verification](#terraform-verification)
  - [KCL Verification](#kcl-verification)
  - [Network Connectivity Tests](#network-connectivity-tests)
  - [State Backend Verification](#state-backend-verification)
- [FAQ](#faq)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

Run these commands first to identify the issue:

```bash
# Verify Dagger is installed
dagger version

# Verify Terraform is installed
terraform version

# Verify KCL is installed
kcl version

# Check installed Dagger modules
dagger config modules
```

If these basic checks pass, proceed to the [Decision Trees](#decision-tree) to narrow down your issue, or browse the [Common Errors By Component](#common-errors-by-component) section.

---

## Common Errors By Component

### Dagger Module Errors

#### Module Not Found

**Symptoms:**
```
Error: failed to get module: module not found
```

**Cause:**
- Module not installed or installed with wrong name
- Using incorrect module reference syntax

**Solution:**
```bash
# Install the module
dagger install github.com/SolomonHD/unifi-cloudflare-glue@vlatest

# Verify installation
dagger config modules
```

**Prevention:** Always verify module installation before use. Use the correct module name from `dagger.json`.

---

#### Secret Parameter Error

**Symptoms:**
```
Error: invalid secret format
```

**Cause:**
- Secret not passed with `env:` prefix
- Environment variable not set

**Solution:**
```bash
# Pass secrets using env: prefix
dagger call -m unifi-cloudflare-glue deploy \
  --unifi-api-key=env:UNIFI_API_KEY \
  --cloudflare-api-token=env:CLOUDFLARE_API_TOKEN
```

**Prevention:** Always use `env:VARIABLE_NAME` syntax for secrets.

---

#### Container Execution Failed

**Symptoms:**
```
Error: failed to execute container: exec failed
```

**Cause:**
- Missing system dependencies
- Container runtime issues
- Insufficient permissions

**Solution:**
```bash
# Verify Docker is running
docker ps

# Check Dagger logs
dagger diag
```

**Prevention:** Ensure Docker is running and you have necessary permissions.

---

#### Function Not Found

**Symptoms:**
```
Error: function "function-name" not found
```

**Cause:**
- Incorrect function name
- Module not loaded

**Solution:**
```bash
# List available functions
dagger functions -m unifi-cloudflare-glue
```

**Prevention:** Verify function names using `--help`.

---

### Terraform Errors

#### Backend Initialization Failed

**Symptoms:**
```
Error: Error initializing backend
Could not connect to backend storage
```

**Cause:**
- Invalid backend configuration
- Network connectivity issues
- Invalid credentials

**Solution:**
1. Verify backend configuration in `backend.hcl`
2. Test network connectivity to backend
3. Verify credentials have correct permissions

```bash
# Test S3 connectivity
aws s3 ls s3://your-bucket/

# Test Azure connectivity
az storage blob list --container-name terraform-state

# Test GCS connectivity
gsutil ls gs://your-bucket/
```

**Prevention:** Test backend configuration before deployment.

---

#### State Lock Timeout

**Symptoms:**
```
Error: Error acquiring the state lock
Lock ID: example-lock-id
```

**Cause:**
- Another Terraform process is running
- Previous process crashed without releasing lock

**Solution:**
```bash
# Check if another process is running
ps aux | grep terraform

# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

**Prevention:** Always use remote state with locking in production.

---

#### Provider Authentication Failed

**Symptoms:**
```
Error: Error while retrieving credentials
provider.Unifi: authentication failed
```

**Cause:**
- Invalid API credentials
- Expired tokens
- Missing required permissions

**Solution:**
1. Verify credentials in environment variables or backend config
2. Check API key hasn't expired
3. Verify required permissions are granted

**Prevention:** Store credentials securely and rotate regularly.

---

### KCL Validation Errors

#### MAC Address Format Invalid

**Symptoms:**
```
KCL Validation Error: MAC address format invalid
Expected format: aa:bb:cc:dd:ee:ff
```

**Cause:**
- MAC address not in correct format
- Contains invalid characters

**Solution:**
Normalize your MAC address to the standard format:
- `aabbccddeeff` → `aa:bb:cc:dd:ee:ff`
- `AA:BB:CC:DD:EE:FF` → `aa:bb:cc:dd:ee:ff`
- `aabb.ccdd.eeff` → `aa:bb:cc:dd:ee:ff`

**Prevention:** Always use lowercase colon-separated format.

---

#### DNS Loop Detected

**Symptoms:**
```
KCL Validation Error: DNS loop detected
local_service_url cannot point to external hostname
```

**Cause:**
- `local_service_url` points to an external/public hostname
- Should use internal domain (.internal.lan, .local, etc.)

**Solution:**
Use an internal domain for `local_service_url`:
```kcl
local_service_url = "https://unifi.internal.lan:8443"  # Correct
# NOT:
local_service_url = "https://unifi.example.com:8443"    # Wrong
```

**Prevention:** Always use internal domains for local service URLs.

---

#### Duplicate MAC Address

**Symptoms:**
```
KCL Validation Error: Duplicate MAC address detected
MAC: aa:bb:cc:dd:ee:ff
```

**Cause:**
- Same MAC address assigned to multiple devices

**Solution:**
Ensure each device has a unique MAC address. Check your configuration for duplicates.

**Prevention:** Maintain a registry of MAC addresses to avoid conflicts.

---

#### Schema Validation Failures

**Symptoms:**
```
KCL Validation Error: missing required field 'name'
```

**Cause:**
- Missing required fields in configuration
- Incorrect field types

**Solution:**
Review the error message and add the required field or fix the type.

**Prevention:** Use IDE with KCL language support for validation feedback.

---

### UniFi Controller Errors

#### TLS Certificate Verify Failed

**Symptoms:**
```
Error: x509: certificate signed by unknown authority
TLS handshake timeout
```

**Cause:**
- Self-signed certificate on UniFi Controller
- Certificate expired

**Solution:**
```bash
# Use --unifi-insecure flag (for testing only)
dagger call -m unifi-cloudflare-glue deploy \
  --unifi-insecure=true
```

**Prevention:** Install proper TLS certificates on UniFi Controller in production.

---

#### API Key Invalid

**Symptoms:**
```
Error: 401 Unauthorized
Invalid API credentials
```

**Cause:**
- Incorrect API key
- API key expired or revoked

**Solution:**
1. Generate new API key from UniFi Controller
2. Verify the key hasn't expired
3. Check API key has required permissions

**Prevention:** Store API keys securely and monitor for expiration.

---

#### Connection Refused

**Symptoms:**
```
Error: dial tcp: connection refused
```

**Cause:**
- UniFi Controller not running
- Wrong hostname or port
- Firewall blocking connection

**Solution:**
```bash
# Test connectivity
curl -k https://unifi.local:8443/status

# Verify controller is running
curl -s https://unifi.local:8443/api/login | head
```

**Prevention:** Verify UniFi Controller is accessible before deployment.

---

#### Timeout

**Symptoms:**
```
Error: context deadline exceeded
Operation timed out
```

**Cause:**
- Network latency
- UniFi Controller overloaded
- Firewall timeout

**Solution:**
1. Check network connectivity
2. Increase timeout values in configuration
3. Verify UniFi Controller performance

**Prevention:** Ensure stable network connection to UniFi Controller.

---

### Cloudflare API Errors

#### Zone Not Found

**Symptoms:**
```
Error: Error retrieving zone: zone not found
```

**Cause:**
- Incorrect zone name
- Zone not in Cloudflare account

**Solution:**
```bash
# List your zones
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/zones"
```

Verify the zone name matches exactly.

**Prevention:** Double-check zone name in configuration.

---

#### Insufficient Permissions

**Symptoms:**
```
Error: Permission denied
Insufficient access to resource
```

**Cause:**
- API token lacks required permissions

**Solution:**
Create a new API token with these permissions:
- `Zone:Read`
- `DNS:Read`, `DNS:Write`
- `Access:Tokens:Write` (for tunnel management)

```bash
# Test token permissions
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/user/tokens/verify"
```

**Prevention:** Create tokens with minimal required permissions.

---

#### Tunnel Name Already Exists

**Symptoms:**
```
Error: Tunnel with this name already exists
```

**Cause:**
- Tunnel name already in use

**Solution:**
Use a unique tunnel name or delete the existing tunnel:
```bash
# Delete existing tunnel
curl -X DELETE \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/..."
```

**Prevention:** Use unique, descriptive tunnel names.

---

#### Rate Limit Exceeded

**Symptoms:**
```
Error: 429 Too Many Requests
Rate limit exceeded
```

**Cause:**
- Too many API requests in short timeframe

**Solution:**
1. Implement retry with exponential backoff
2. Cache DNS records to reduce API calls
3. Wait before retrying

```python
# Example retry logic
import time

def retry_with_backoff(func, max_retries=3):
    for i in range(max_retries):
        try:
            return func()
        except RateLimitError:
            time.sleep(2 ** i)
    raise Exception("Max retries exceeded")
```

**Prevention:** Optimize API usage with caching.

---

## Decision Trees

### Deployment Failure Decision Tree

```
Deployment fails
├─ At what stage?
│  ├─ Configuration generation (KCL)
│  │  └─ What error?
│  │     ├─ MAC format invalid → [KCL Validation Errors](#mac-address-format-invalid)
│  │     ├─ DNS loop detected → [DNS Loop Detected](#dns-loop-detected)
│  │     └─ Schema validation → [Schema Validation Failures](#schema-validation-failures)
│  │
│  ├─ Terraform init
│  │  └─ What error?
│  │     ├─ Backend init failed → [Backend Initialization Failed](#backend-initialization-failed)
│  │     ├─ Provider auth failed → [Provider Authentication Failed](#provider-authentication-failed)
│  │     └─ State lock timeout → [State Lock Timeout](#state-lock-timeout)
│  │
│  ├─ Terraform plan/apply
│  │  └─ What error?
│  │     ├─ UniFi API error → [UniFi Controller Errors](#unifi-controller-errors)
│  │     └─ Cloudflare API error → [Cloudflare API Errors](#cloudflare-api-errors)
│  │
│  └─ Dagger module execution
│     └─ What error?
│        ├─ Module not found → [Module Not Found](#module-not-found)
│        ├─ Secret parameter error → [Secret Parameter Error](#secret-parameter-error)
│        └─ Container execution failed → [Container Execution Failed](#container-execution-failed)
```

### Authentication Failure Decision Tree

```
Authentication fails
├─ Which component?
│  ├─ UniFi Controller
│  │  ├─ 401 Unauthorized → [API Key Invalid](#api-key-invalid)
│  │  ├─ TLS error → [TLS Certificate Verify Failed](#tls-certificate-verify-failed)
│  │  └─ Connection refused → [Connection Refused](#connection-refused)
│  │
│  ├─ Cloudflare
│  │  ├─ Zone not found → [Zone Not Found](#zone-not-found)
│  │  ├─ Permission denied → [Insufficient Permissions](#insufficient-permissions)
│  │  └─ Rate limited → [Rate Limit Exceeded](#rate-limit-exceeded)
│  │
│  └─ State backend
│     ├─ S3 → Check AWS credentials
│     ├─ Azure → Check Azure credentials
│     └─ GCS → Check GCP credentials
│        → [Backend Initialization Failed](#backend-initialization-failed)
```

### State Management Issues Decision Tree

```
State management issue
├─ What operation?
│  ├─ terraform init fails
│  │  └─ [Backend Initialization Failed](#backend-initialization-failed)
│  │
│  ├─ Cannot acquire lock
│  │  ├─ Another process running?
│  │  │  ├─ Yes → Wait for completion
│  │  │  └─ No → [State Lock Timeout](#state-lock-timeout)
│  │  │
│  │  └─ Stale lock → terraform force-unlock
│  │
│  ├─ State migration fails
│  │  ├─ Backend connectivity → Test backend access
│  │  └─ State format incompatibility → Manual migration required
│  │
│  └─ State out of sync
│     ├─ Check remote state
│     └─ Refresh state: terraform refresh
```

---

## Diagnostics Commands

### Dagger Verification

```bash
# Check Dagger version
dagger version
# Expected: Dagger version 0.x.x or similar

# Test basic module call
dagger call hello
# Expected: Hello, World!

# List installed modules
dagger config modules

# Get module help
dagger call -m unifi-cloudflare-glue --help
```

### Terraform Verification

```bash
# Check Terraform version
terraform version
# Expected: Terraform v1.x.x

# Verify provider configuration
terraform providers
# Expected: Shows provider versions

# Check current state
terraform show

# List workspaces
terraform workspace list
```

### KCL Verification

```bash
# Check KCL version
kcl version
# Expected: KCL version 0.x.x

# Validate configuration without output
kcl run main.k
# Expected: Validation passes or shows errors

# Check module dependencies
kcl mod graph
```

### Network Connectivity Tests

```bash
# Test UniFi Controller connectivity
curl -k https://unifi.local:8443/status
# Expected: JSON response with controller status

# Test UniFi API login endpoint
curl -k -X POST https://unifi.local:8443/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
# Expected: {"meta":{"rc":"ok"}} or error response

# Verify Cloudflare API token
curl -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  "https://api.cloudflare.com/client/v4/user/tokens/verify"
# Expected: {"result":{"active":true,...},"success":true}
```

### State Backend Verification

```bash
# Test S3 backend access
aws s3 ls s3://your-terraform-bucket/
# Expected: List of objects in bucket

# Test Azure backend access
az storage blob list --container-name terraform-state \
  --account-name your-account
# Expected: List of blobs

# Test GCS backend access
gsutil ls gs://your-terraform-bucket/
# Expected: List of objects in bucket
```

---

## FAQ

### How do I reset state?

To reset Terraform state:

1. **Backup current state first:**
   ```bash
   terraform state pull > state-backup.tfstate
   ```

2. **For local state:** Delete `terraform.tfstate` file

3. **For remote state:** Use `terraform state rm` to remove resources, then re-import

**Warning:** Always backup state before resetting.

### Can I use multiple tunnels per device?

Yes, each device can have multiple tunnels. Each tunnel requires:
- Unique tunnel name
- Unique MAC address (per tunnel interface)
- Different Cloudflare tunnel configurations

### Why does DNS loop validation fail?

DNS loop detection fails when `local_service_url` points to an external/public domain. The system requires internal domains (.internal.lan, .local, etc.) to prevent DNS resolution loops.

**Solution:** Use internal domain names for local service URLs.

### How do I debug KCL schemas?

1. Run with verbose output:
   ```bash
   kcl run -v main.k
   ```

2. Check IDE integration for real-time validation

3. Validate individual files:
   ```bash
   kcl validate main.k
   ```

4. Check generated output:
   ```bash
   kcl run main.k 2>&1 | head -50
   ```

### What MAC address formats are accepted?

The system accepts MAC addresses in these formats:
- `aa:bb:cc:dd:ee:ff` (canonical - recommended)
- `AA:BB:CC:DD:EE:FF` (uppercase)
- `aabbccddeeff` (no separators)
- `aabb.ccdd.eeff` (Cisco format)

All formats are normalized to lowercase colon-separated.

### How do I update provider credentials?

1. **Environment variables:**
   ```bash
   export UNIFI_API_KEY="new-key"
   export CLOUDFLARE_API_TOKEN="new-token"
   ```

2. **Backend config file:**
   Update your backend configuration file with new credentials

3. **Re-run deployment:**
   ```bash
   dagger call -m unifi-cloudflare-glue deploy
   ```

### Why is my tunnel not connecting?

Common causes:
1. **Network connectivity:** Check firewall rules allow tunnel traffic
2. **Credentials:** Verify Cloudflare API token has correct permissions
3. **Tunnel name:** Ensure tunnel name is unique
4. **DNS:** Check Cloudflare dashboard for tunnel status

Check tunnel status in Cloudflare dashboard: **Zero Trust > Networks > Tunnels**

### How do I force-unlock Terraform state?

**Use with caution - only when sure no other process is running:**

```bash
terraform force-unlock <lock-id>
```

To find lock ID:
```bash
terraform state pull | jq '.lock'
```

**Warning:** Force-unlocking can cause state corruption if another process is actively working.

### What Cloudflare permissions are required?

Create an API token with these minimum permissions:

- **Zone Settings:** Read
- **DNS:** Read, Write
- **Account:** Cloudflare Tunnel: Edit

Or use the "Edit" template for "All Accounts - Cloudflare Tunnel".

### How do I verify my configuration before deploying?

1. **KCL validation:**
   ```bash
   kcl run main.k
   ```

2. **Terraform plan:**
   ```bash
   cd terraform
   terraform init
   terraform plan
   ```

3. **Dagger dry-run:**
   ```bash
   dagger call -m unifi-cloudflare-glue validate
   ```

---

## Getting Help

If you've tried the troubleshooting steps and still need help:

1. **Check the [CHANGELOG.md](../CHANGELOG.md)** for known issues and fixes in recent releases

2. **Search existing [GitHub Issues](https://github.com/SolomonHD/unifi-cloudflare-glue/issues)** - your issue might already be reported

3. **Review [Contributing Guide](../CONTRIBUTING.md)** for development setup help

4. **Open a new issue** with:
   - Full error message
   - Steps to reproduce
   - Your environment details
   - What you've already tried

### Debug Information to Include

When reporting issues, include:

```bash
# Dagger version
dagger version

# Terraform version  
terraform version

# KCL version
kcl version

# Module configuration
dagger call -m unifi-cloudflare-glue --help

# Error logs
terraform apply 2>&1 | tee error.log
```

---

## Related Topics

- [Getting Started](getting-started.md) - Installation and first deployment
- [Backend Configuration](backend-configuration.md) - Backend setup and configuration
- [Security](security.md) - Authentication and credential handling
- [State Management](state-management.md) - State-related issues and solutions
- [Dagger Reference](dagger-reference.md) - Function usage and examples
