# OpenSpec Change Prompt 01: Fix Test Config Generation

## Context

The `test_integration` function currently generates test configuration using `_generate_test_kcl_config()` which outputs raw KCL code. However, the Terraform modules expect JSON configuration files in specific formats:

- **Cloudflare module** (`terraform/modules/cloudflare-tunnel/`): Expects `cloudflare.json` with `zone_name`, `account_id`, and `tunnels` map
- **UniFi module** (`terraform/modules/unifi-dns/`): Expects `unifi.json` with `devices` list containing MAC addresses

## Goal

Replace the KCL-based test config generation with direct JSON generation that matches the Terraform module variable structures.

## Scope

**In scope:**
- Modify `_generate_test_kcl_config()` method to generate JSON instead of KCL
- Rename method to `_generate_test_configs()` for clarity
- Generate both Cloudflare and UniFi JSON configs in one call
- Return a tuple or dict with both config strings

**Out of scope:**
- Changing how the configs are used in test_integration
- Adding Terraform execution logic
- Modifying the test phases

## Desired Behavior

### 1. New Method Signature

```python
def _generate_test_configs(
    self, 
    test_id: str, 
    cloudflare_zone: str,
    cloudflare_account_id: str
) -> dict:
    """Generate test configurations for both Cloudflare and UniFi.
    
    Returns:
        dict with keys:
            - "cloudflare": JSON string for cloudflare-tunnel module
            - "unifi": JSON string for unifi-dns module
    """
```

### 2. Cloudflare Config Format

```json
{
  "zone_name": "test.example.com",
  "account_id": "xxx",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "tunnel-test-abc12",
      "mac_address": "aa:bb:cc:dd:ee:ff",
      "services": [
        {
          "public_hostname": "test-abc12.test.example.com",
          "local_service_url": "http://192.168.1.100:8080",
          "no_tls_verify": false
        }
      ]
    }
  }
}
```

### 3. UniFi Config Format

```json
{
  "devices": [
    {
      "friendly_hostname": "test-device",
      "domain": "local",
      "nics": [
        {
          "mac_address": "aa:bb:cc:dd:ee:ff",
          "nic_name": "eth0"
        }
      ]
    }
  ],
  "default_domain": "local",
  "site": "default"
}
```

### 4. Test ID Usage

- `test_hostname = f"{test_id}.{cloudflare_zone}"` (e.g., `test-abc12.test.example.com`)
- `tunnel_name = f"tunnel-{test_id}"` (e.g., `tunnel-test-abc12`)
- Use a fake MAC address like `aa:bb:cc:dd:ee:ff` for testing
- Use a fake internal IP like `192.168.1.100`

## Constraints & Assumptions

- The generated JSON must match the variable types defined in:
  - `terraform/modules/cloudflare-tunnel/variables.tf`
  - `terraform/modules/unifi-dns/variables.tf`
- Use `json.dumps()` to generate valid JSON
- MAC address format must match the regex in variables.tf: `^([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})$|^[0-9a-fA-F]{12}$`
- The method should return both configs so they can be written to files later

## Acceptance Criteria

- [ ] `_generate_test_kcl_config()` is renamed to `_generate_test_configs()`
- [ ] Method returns a dict with "cloudflare" and "unifi" keys
- [ ] Cloudflare config JSON matches the module's variable structure
- [ ] UniFi config JSON matches the module's variable structure
- [ ] test_id is used consistently in tunnel names and hostnames
- [ ] Both configs use the same fake MAC address
- [ ] Method has proper docstring explaining return format

## Reference

- Target method: `_generate_test_kcl_config()` at line 710 in `src/main/main.py`
- Cloudflare variables: `terraform/modules/cloudflare-tunnel/variables.tf`
- UniFi variables: `terraform/modules/unifi-dns/variables.tf`
