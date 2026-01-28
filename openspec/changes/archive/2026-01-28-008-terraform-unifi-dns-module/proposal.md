# Change: Terraform UniFi DNS Module

## Why

The UniFi DNS module bridges the KCL-generated configuration with the UniFi Controller's DNS management. It queries the UniFi Controller for device IP addresses by MAC address and creates corresponding A-records and CNAMEs. This enables automatic DNS management for homelab devices where IPs are dynamically assigned by the UniFi Controller but need stable DNS names.

## What Changes

- Define complete input variable schema matching KCL generator output
- Create data source queries to UniFi Controller for device IPs by MAC address
- Implement A-record creation for device friendly_hostnames with round-robin for multi-NIC devices
- Implement CNAME creation for service hostnames pointing to device FQDNs
- Define outputs for created records, missing devices, and device IP mappings
- Add MAC address normalization for consistent lookups
- Implement graceful handling of missing MAC addresses (warn but don't fail)
- Update module README with complete usage documentation

## Impact

- Affected specs: `terraform-module` capability
- Affected code:
  - `terraform/modules/unifi-dns/variables.tf` - Complete input variable definitions
  - `terraform/modules/unifi-dns/main.tf` - Data sources and DNS record resources
  - `terraform/modules/unifi-dns/outputs.tf` - Output definitions
  - `terraform/modules/unifi-dns/README.md` - Usage documentation

## Dependencies

- Depends on: Project scaffolding (`project-scaffolding` / 001) must exist
- Soft Depends on: KCL UniFi generator (`kcl-unifi-generator` / 005) for input format compatibility

## Expected JSON Input Format

The module consumes JSON output from the KCL UniFi generator with this structure:

```json
{
  "devices": [
    {
      "friendly_hostname": "media-server",
      "domain": "internal.lan",
      "service_cnames": ["storage.internal.lan"],
      "nics": [
        {
          "mac_address": "aa:bb:cc:dd:ee:01",
          "nic_name": "eth0",
          "service_cnames": ["nas.internal.lan"]
        }
      ]
    }
  ],
  "default_domain": "internal.lan"
}
```
